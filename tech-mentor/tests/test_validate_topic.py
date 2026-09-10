import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_topic.py"
SPEC = importlib.util.spec_from_file_location("validate_topic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


VALID = """# 示例主题

## 目标
能独立完成一个任务。

## 类型
知识型。

## 路径
1. 核心模型

## 检验标准
- 独立迁移

## 学习状态
- 更新时间：2026-09-08
- 当前阶段：第一单元
- 已验证：完成一次迁移题
- 未验证项：真实环境实验
- 下一步：完成实验
"""


class ValidateTopicTests(unittest.TestCase):
    def test_valid_topic_passes(self):
        self.assertEqual([], [f for f in MODULE.validate_text(VALID) if f["severity"] == "error"])

    def test_placeholder_and_missing_sections_fail(self):
        findings = MODULE.validate_text("# <主题>\n\n## 目标\nTODO\n")
        rule_ids = {item["rule_id"] for item in findings}
        self.assertIn("TOPIC_UNFINISHED_PLACEHOLDER", rule_ids)
        self.assertIn("TOPIC_MISSING_SECTION", rule_ids)

    def test_possible_secret_fails(self):
        findings = MODULE.validate_text(VALID + "\npassword=real-secret\n")
        self.assertIn("TOPIC_POSSIBLE_SECRET", {item["rule_id"] for item in findings})

    def test_cli_reads_utf8_bom(self):
        path = Path(__file__).resolve().parents[1] / "references" / "topics" / "metallb.md"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, MODULE.main([str(path), "--json"]))


if __name__ == "__main__":
    unittest.main()
