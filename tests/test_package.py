"""只复制技能目录后仍可执行用户工作流，不依赖仓库工具或测试。"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from test_export import BROWSER

PUBLIC = Path(__file__).resolve().parents[1]
SOURCE = PUBLIC / "skills/diagram-design-zh"


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name).resolve()
        cls.skill = cls.base / "skill"
        shutil.copytree(SOURCE, cls.skill, ignore=shutil.ignore_patterns("__pycache__"))
        cls.work = cls.base / "output"
        cls.work.mkdir()

    def cli(self, script, *args):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        run = subprocess.run(
            [sys.executable, str(self.skill / "scripts" / script), *map(str, args)],
            cwd=self.work,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return run.stdout

    def test_document_resources_are_contained_in_skill(self):
        for path in self.skill.rglob("*.md"):
            for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                local = target.split("#")[0]
                if not local or re.match(r"[a-z][a-z0-9+.-]*:", local):
                    continue
                resource = (path.parent / local).resolve()
                with self.subTest(document=path.relative_to(self.skill), target=local):
                    self.assertTrue(resource.is_relative_to(self.skill))
                    self.assertTrue(resource.exists())

    def test_detached_user_workflow_keeps_package_unchanged(self):
        before = {
            p.relative_to(self.skill): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.skill.rglob("*")
            if p.is_file()
        }
        source = self.skill / "assets/example-architecture.html"
        self.cli("self_check.py", source)
        renamed = self.work / "diagram.html"
        self.cli("reskin.py", "--skin", "default", source, "-o", renamed)
        self.cli("self_check.py", renamed)
        exported = self.work / "diagram.svg"
        self.cli("export.py", renamed, "--format", "svg", "-o", exported)
        self.assertEqual(ET.parse(exported).getroot().attrib["viewBox"], "0 0 1000 360")
        config = self.cli(
            "profiles.py",
            "resolve",
            "--project",
            self.work,
            "--library",
            self.work / "profiles",
        ).strip()
        self.assertEqual(Path(config), self.skill / "styles/default.json")
        routes = json.loads(self.cli("catalog.py", "蜂群"))
        self.assertEqual(routes[0]["id"], "scatter")
        for script in (
            "embed_fonts.py",
            "content_check.py",
            "reading_check.py",
            "drawio_extract.py",
            "mermaid_extract.py",
        ):
            with self.subTest(script=script):
                self.cli(script, "--help")
        after = {
            p.relative_to(self.skill): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.skill.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }
        self.assertEqual(after, before)

    @unittest.skipUnless(
        BROWSER
        and importlib.util.find_spec("playwright")
        and importlib.util.find_spec("fontTools"),
        "browser + font dependencies required",
    )
    def test_detached_font_embedding_reading_and_png_export(self):
        source = self.skill / "assets/example-bar.html"
        output = self.work / "bar-copy.html"
        self.cli("reskin.py", "--skin", "default", source, "-o", output)
        self.cli("embed_fonts.py", output, "--strip")
        self.assertNotIn("/*fonts:begin", output.read_text())
        self.cli("embed_fonts.py", output)
        self.assertIn("data:font/woff2;base64,", output.read_text())
        reading = self.work / "bar-reading.html"
        result = json.loads(
            self.cli(
                "reading_check.py",
                output,
                "--browser-executable",
                BROWSER,
                "-o",
                reading,
            )
        )
        self.assertEqual(result["after"]["clippedElements"], [])
        self.assertGreaterEqual(result["after"]["minCjkScreenPx"], 9.99)
        png = self.work / "bar.png"
        self.cli(
            "export.py",
            reading,
            "--format",
            "png",
            "--scale",
            "1",
            "--browser-executable",
            BROWSER,
            "-o",
            png,
        )
        data = png.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1000, 520))


if __name__ == "__main__":
    unittest.main()
