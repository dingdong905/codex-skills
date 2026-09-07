#!/usr/bin/env python3
"""对 PPTX 做零依赖静态审计；结果是 QA 线索，不替代渲染和人工判断。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}
EMU_PER_INCH = 914400
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:%|倍|GB|TB|MB|TOPS|FLOPS|W|元|美元)?", re.I)
EVIDENCE_RE = re.compile(r"来源|资料来源|截至|更新于|source|as[ -]of|https?://|doi:|arxiv|pmid", re.I)
SLIDE_RE = re.compile(r"slide(\d+)\.xml$")


def finding(severity: str, slide: int | None, category: str, message: str) -> dict:
    return {"severity": severity, "slide": slide, "category": category, "finding": message}


def slide_number(name: str) -> int:
    match = SLIDE_RE.search(name)
    return int(match.group(1)) if match else 0


def parse_xml(payload: bytes) -> ET.Element:
    return ET.fromstring(payload)


def shape_boxes(root: ET.Element) -> list[tuple[int, int, int, int]]:
    boxes = []
    for xfrm in root.findall(".//a:xfrm", NS):
        off = xfrm.find("a:off", NS)
        ext = xfrm.find("a:ext", NS)
        if off is None or ext is None:
            continue
        try:
            boxes.append(tuple(int(v) for v in (off.get("x"), off.get("y"), ext.get("cx"), ext.get("cy"))))
        except (TypeError, ValueError):
            continue
    return boxes


def inspect_deck(path: Path, mode: str, min_font: float | None) -> dict:
    findings: list[dict] = []
    slides: list[dict] = []
    if not path.is_file():
        return {"ok": False, "findings": [finding("P0", None, "file", f"文件不存在: {path}")]}

    try:
        package = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        return {"ok": False, "findings": [finding("P0", None, "file", f"无法读取 PPTX: {exc}")]}

    with package:
        names = set(package.namelist())
        pres_name = "ppt/presentation.xml"
        if pres_name not in names:
            return {"ok": False, "findings": [finding("P0", None, "file", "缺少 ppt/presentation.xml")]}
        pres = parse_xml(package.read(pres_name))
        sld_sz = pres.find("p:sldSz", NS)
        width = int(sld_sz.get("cx", "0")) if sld_sz is not None else 0
        height = int(sld_sz.get("cy", "0")) if sld_sz is not None else 0
        slide_names = sorted((n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")), key=slide_number)
        if not slide_names:
            findings.append(finding("P0", None, "file", "演示中没有幻灯片"))

        notes_count = len([n for n in names if n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml")])
        editable_text_total = 0
        for name in slide_names:
            number = slide_number(name)
            root = parse_xml(package.read(name))
            texts = [node.text or "" for node in root.findall(".//a:t", NS)]
            joined = "".join(texts).strip()
            text_chars = len(joined)
            text_boxes = len([shape for shape in root.findall(".//p:sp", NS) if shape.findall(".//a:t", NS)])
            picture_count = len(root.findall(".//p:pic", NS))
            chart_count = len(root.findall(".//c:chart", NS))
            table_count = len(root.findall(".//a:tbl", NS))
            numbers = len(NUMBER_RE.findall(joined))
            has_evidence_marker = bool(EVIDENCE_RE.search(joined))
            font_sizes = []
            for node in root.findall(".//*[@sz]"):
                try:
                    value = float(node.get("sz", "0")) / 100
                except ValueError:
                    continue
                if value > 0:
                    font_sizes.append(value)
            smallest_font = min(font_sizes) if font_sizes else None
            editable_text_total += text_chars

            outside = 0
            near_full_slide = False
            for x, y, cx, cy in shape_boxes(root):
                if width and height and (x < 0 or y < 0 or x + cx > width or y + cy > height):
                    outside += 1
                if width and height and cx >= width * 0.9 and cy >= height * 0.9:
                    near_full_slide = True

            max_chars = 320 if mode == "live" else 520
            max_boxes = 24 if mode == "live" else 36
            if text_chars > max_chars * 1.5:
                findings.append(finding("P1", number, "density", f"{text_chars} 个文本字符，显著超过 {mode} 模式预算 {max_chars}"))
            elif text_chars > max_chars:
                findings.append(finding("P2", number, "density", f"{text_chars} 个文本字符，超过 {mode} 模式预算 {max_chars}"))
            if text_boxes > max_boxes:
                findings.append(finding("P2", number, "density", f"{text_boxes} 个文本框，阅读路径可能碎片化"))
            threshold = min_font if min_font is not None else (15.0 if mode == "live" else 12.0)
            if smallest_font is not None and smallest_font < 10:
                findings.append(finding("P1", number, "readability", f"检测到 {smallest_font:g}pt 字号；确认不是正文或被迫缩字"))
            elif smallest_font is not None and smallest_font < threshold:
                findings.append(finding("P2", number, "readability", f"最小字号 {smallest_font:g}pt，低于启发式阈值 {threshold:g}pt"))
            if outside:
                findings.append(finding("P1", number, "layout", f"{outside} 个对象的几何边界超出画布；需渲染确认"))
            if picture_count and near_full_slide and text_chars < 10:
                findings.append(finding("P0", number, "editability", "页面接近整页图片且几乎没有可编辑文本"))
            if numbers >= 3 and not has_evidence_marker:
                findings.append(finding("P2", number, "evidence", f"检测到 {numbers} 个数值，但页内未发现来源或截至日期标记；也可在备注核验"))

            slides.append({
                "slide": number,
                "text_chars": text_chars,
                "text_boxes": text_boxes,
                "pictures": picture_count,
                "charts": chart_count,
                "tables": table_count,
                "numbers": numbers,
                "smallest_font_pt": smallest_font,
                "evidence_marker": has_evidence_marker,
            })

        if slide_names and editable_text_total == 0:
            findings.append(finding("P0", None, "editability", "整套演示未检测到可编辑文本"))

    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    findings.sort(key=lambda item: (severity_rank[item["severity"]], item["slide"] or 0, item["category"]))
    counts = {key: sum(item["severity"] == key for item in findings) for key in severity_rank}
    return {
        "ok": counts["P0"] == 0 and counts["P1"] == 0,
        "file": str(path.resolve()),
        "mode": mode,
        "slide_count": len(slides),
        "slide_size_inches": [round(width / EMU_PER_INCH, 3), round(height / EMU_PER_INCH, 3)] if width and height else None,
        "notes_slide_count": notes_count,
        "severity_counts": counts,
        "findings": findings,
        "slides": slides,
        "limitations": [
            "静态审计无法判断事实真伪、叙事质量、视觉层级或实际字体替换",
            "对象越界、字号、来源标记和整页图片均为启发式结果，必须结合渲染检查",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("--mode", choices=("live", "read"), default="live")
    parser.add_argument("--min-font", type=float)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = inspect_deck(args.deck, args.mode, args.min_font)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result.get('file', args.deck)}: {result.get('slide_count', 0)} slides")
        for item in result.get("findings", []):
            where = f" slide {item['slide']}" if item.get("slide") else ""
            print(f"[{item['severity']}]{where} {item['category']}: {item['finding']}")
        if not result.get("findings"):
            print("No static findings. Render and review the deck before delivery.")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

