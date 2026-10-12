import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "handoff_state.py"
spec = importlib.util.spec_from_file_location("handoff_state", SCRIPT)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)

class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "工作目录"
        self.workspace.mkdir()
        (self.workspace / "note.txt").write_text("中文输出\n", encoding="utf-8")

    def test_unchanged_and_changed_selected_file(self):
        saved = state.snapshot(self.workspace, ["note.txt"])
        self.assertTrue(state.compare(saved, self.workspace)["matched"])
        (self.workspace / "note.txt").write_text("另一个编辑者的变更\n", encoding="utf-8")
        self.assertEqual(state.compare(saved, self.workspace)["differences"], ["files.note.txt"])

    def test_missing_file_is_not_silently_accepted(self):
        saved = state.snapshot(self.workspace, ["note.txt"])
        (self.workspace / "note.txt").unlink()
        with self.assertRaises(ValueError):
            state.compare(saved, self.workspace)

    def test_escape_and_absolute_selection_rejected(self):
        outside = self.root / "private.txt"
        outside.write_text("fixture", encoding="utf-8")
        for name in ("../private.txt", str(outside)):
            with self.subTest(name=name), self.assertRaises(ValueError):
                state.snapshot(self.workspace, [name])

    def test_confirmed_relocation_keeps_content_checks(self):
        saved = state.snapshot(self.workspace, ["note.txt"])
        other = self.root / "另一目录"
        shutil.copytree(self.workspace, other)
        self.assertIn("workspace", state.compare(saved, other)["differences"])
        self.assertTrue(state.compare(saved, other, True)["matched"])
        (other / "note.txt").write_text("changed", encoding="utf-8")
        self.assertFalse(state.compare(saved, other, True)["matched"])

    def test_git_unavailable_is_explicit(self):
        with patch.object(state.shutil, "which", return_value=None):
            saved = state.snapshot(self.workspace, ["note.txt"])
        self.assertEqual(saved["limitations"], ["git-unavailable"])

    def test_cli_never_overwrites_snapshot(self):
        target = self.root / "snapshot.json"
        target.write_text("keep-existing", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "snapshot",
             "--workspace", str(self.workspace), "--file", "note.txt", "--output", str(target)],
            capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep-existing")

    @unittest.skipUnless(shutil.which("git"), "Git not available")
    def test_git_tracks_staged_unstaged_and_untracked_changes(self):
        def git(*args):
            subprocess.run(["git", "-C", str(self.workspace), *args],
                           check=True, capture_output=True)
        git("init")
        git("add", "note.txt")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "core.hooksPath=" + str(self.root / "no-hooks"), "commit", "-m", "fixture")
        saved = state.snapshot(self.workspace, ["note.txt"])
        git("checkout", "--detach")
        self.assertIn("git.branch", state.compare(saved, self.workspace)["differences"])
        git("checkout", "-")
        (self.workspace / "note.txt").write_text("staged\n", encoding="utf-8")
        git("add", "note.txt")
        (self.workspace / "note.txt").write_text("unstaged\n", encoding="utf-8")
        (self.workspace / "new.txt").write_text("untracked\n", encoding="utf-8")
        changes = state.compare(saved, self.workspace)["differences"]
        for field in ("git.status", "git.staged_diff_sha256", "git.unstaged_diff_sha256", "files.note.txt"):
            self.assertIn(field, changes)

class PacketTests(unittest.TestCase):
    def packet(self):
        return "\n\n".join("## " + section + "\n实测状态及可执行动作。" for section in state.REQUIRED)

    def test_valid_packet_and_missing_action(self):
        self.assertTrue(state.validate(self.packet())["valid"])
        broken = self.packet().replace("## 下一步\n实测状态及可执行动作。", "## 下一步\n")
        self.assertFalse(state.validate(broken)["valid"])

    def test_secret_failure_does_not_echo_value(self):
        secret = "ghp_" + "Z" * 28
        result = state.validate(self.packet() + "\n" + secret)
        self.assertFalse(result["valid"])
        self.assertNotIn(secret, json.dumps(result))

    def test_unfilled_template_and_fake_fenced_sections_fail(self):
        template = SCRIPT.parents[1] / "templates" / "handoff.md"
        self.assertFalse(state.validate(template.read_text(encoding="utf-8"))["valid"])
        self.assertFalse(state.validate("~~~markdown\n" + self.packet() + "\n~~~")["valid"])

if __name__ == "__main__":
    unittest.main()
