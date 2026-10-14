"""完整工具路径的回归，所有输出留在临时目录。"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/diagram-design-zh"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import self_check, reskin
from html_tools import map_colors, select_svg


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.source = (SKILL / "assets/example-architecture.html").read_text()

    def file(self, text, name="example-architecture.html"):
        p = self.dir / name
        p.write_text(text)
        return p

    def gallery_file(self, source):
        for path in (SKILL / "assets").glob("example-*.html"):
            (self.dir / path.name).write_text("local preview fixture")
        return self.file(source, "index.html")

    def verify_gallery(self, path):
        return self_check.verify(
            path, mode="gallery", gallery_template=ROOT / "tools/gallery_template.html"
        )

    def cli(self, script, *args, ok=True, cwd=None):
        run = subprocess.run(
            [sys.executable, str(SCRIPTS / script), *map(str, args)],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if ok:
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        else:
            self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        return run

    def test_gallery_claim_cannot_authorize_a_script(self):
        for marker in ["", " data-gallery-index"]:
            source = self.source.replace("<body>", "<body" + marker + ">").replace(
                "</body>", "<script>window.audit=1</script></body>"
            )
            self.assertTrue(self_check.verify(self.file(source))[0])
        empty = '<html lang="zh-CN"><style>:root{--font-sans:PingFang SC;--font-serif:serif;--font-mono:ui-monospace;}</style><!-- data-gallery-index --></html>'
        self.assertTrue(self_check.verify(self.file(empty))[0])

    def test_gallery_mode_requires_structure_and_canonical_script(self):
        self.assertFalse(self.verify_gallery(SKILL / "assets/index.html")[0])
        self.assertTrue(self.verify_gallery(self.file(self.source))[0])
        self.assertTrue(
            self.verify_gallery(
                self.gallery_file(
                    (SKILL / "assets/index.html")
                    .read_text()
                    .replace("(function () {", "(function () {window.audit=1;", 1)
                ),
            )[0]
        )

    def test_gallery_canonical_template_is_a_caller_dependency(self):
        errors, _ = self_check.verify(SKILL / "assets/index.html", mode="gallery")
        self.assertTrue(any("显式提供规范模板" in error for error in errors))

    def test_gallery_mode_does_not_allow_executable_links_or_remote_previews(self):
        original = (SKILL / "assets/index.html").read_text()
        self.assertFalse(self.verify_gallery(self.gallery_file(original))[0])
        for source in [
            original.replace(
                'href="https://github.com/patrick-xin/diagram-design-zh"',
                'href="javascript:alert(1)"',
                1,
            ),
            original.replace(
                'data-dark="example-architecture-dark.html"',
                'data-dark="https://example.invalid/remote.html"',
                1,
            ),
        ]:
            self.assertTrue(self.verify_gallery(self.gallery_file(source))[0])

    def test_export_ignores_decorative_svg_and_accepts_nested_svg(self):
        icon = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M0 0" fill="none"/></svg>'
        for source in [
            self.source.replace("<body>", "<body>" + icon),
            self.source.replace("</svg>", icon + "</svg>", 1),
        ]:
            p = self.file(source)
            target = self.dir / "out.svg"
            self.cli("export.py", p, "--format", "svg", "-o", target)
            self.assertIn("example-architecture-title", target.read_text())
            self.assertIn("1000 360", target.read_text())

    def test_multi_main_diagram_selection_is_explicit(self):
        a = '<svg id="a" role="img" viewBox="0 0 24 24"></svg>'
        b = '<svg id="b" role="img" viewBox="0 0 40 40"></svg>'
        with self.assertRaises(ValueError):
            select_svg(a + b)
        self.assertEqual(select_svg(a + b, "b").attrs["id"], "b")

    def test_multiple_main_diagrams_export_selected_id(self):
        def svg(ident):
            return f'<svg xmlns="http://www.w3.org/2000/svg" id="{ident}" role="img" viewBox="0 0 40 40" aria-labelledby="two-{ident}-title two-{ident}-desc"><title id="two-{ident}-title">{ident}</title><desc id="two-{ident}-desc">graph</desc><rect width="40" height="40" fill="#ffffff"/></svg>'

        source = (
            '<html lang="zh-CN"><head><style>:root{--font-sans:PingFang SC;--font-serif:serif;--font-mono:ui-monospace;}</style></head><body>'
            + svg("a")
            + svg("b")
            + "</body></html>"
        )
        p = self.file(source, "two.html")
        out = self.dir / "out.svg"
        self.cli("export.py", p, "--format", "svg", "-o", out, ok=False)
        self.assertFalse(out.exists())
        self.cli("export.py", p, "--format", "svg", "--svg-id", "b", "-o", out)
        self.assertIn("two-b-title", out.read_text())
        self.assertNotIn("two-a-title", out.read_text())

    def test_skin_chain_and_reset_preserve_data_strings(self):
        p = self.file(
            self.source.replace(
                "用户网站", "色值记录 #29314f · rgba(41,49,79,0.77) · 原值", 1
            )
        )
        first = self.dir / "first.html"
        second = self.dir / "second.html"
        direct = self.dir / "direct.html"
        reset = self.dir / "reset.html"
        self.cli("reskin.py", "--skin", "xinzhongshi", p, "-o", first)
        first.write_text(map_colors(first.read_text(), lambda v: v.replace(",", ", ")))
        self.cli("reskin.py", "--skin", "zhongguohong", first, "-o", second)
        self.cli("reskin.py", "--skin", "zhongguohong", p, "-o", direct)
        for out in [first, second, direct]:
            self.assertIn(
                "色值记录 #29314f · rgba(41,49,79,0.77) · 原值", out.read_text()
            )

        def paints(path):
            from html_tools import color_occurrences

            return [
                reskin.parse_color(v)[0]
                for a, b, v in color_occurrences(path.read_text())
            ]

        self.assertEqual(paints(second), paints(direct))
        self.cli("reskin.py", "--skin", "default", second, "-o", reset)
        self.assertEqual(paints(reset), paints(p))

    def test_brand_source_is_explicit_and_unknown_color_does_not_write(self):
        p = self.file(
            map_colors(
                self.source,
                lambda v: v.replace("#1a4dd9", "#9b1c1c").replace(
                    "26,77,217", "155,28,28"
                ),
            )
        )
        guide = self.dir / "brand.md"
        guide.write_text(
            (SKILL / "references/style-guide.md")
            .read_text()
            .replace("#1a4dd9", "#9b1c1c")
        )
        target = self.dir / "brand-red.html"
        self.cli("reskin.py", "--skin", "zhongguohong", p, "-o", target, ok=False)
        self.assertFalse(target.exists())
        self.cli(
            "reskin.py",
            "--skin",
            "zhongguohong",
            "--from-style-guide",
            guide,
            p,
            "-o",
            target,
        )
        from html_tools import color_occurrences

        self.assertNotIn(
            "#9b1c1c", [v for a, b, v in color_occurrences(target.read_text())]
        )
        self.assertFalse(self_check.verify(target)[0])

    def test_requested_relative_output_directory_is_preserved(self):
        (self.dir / "nested").mkdir()
        self.cli(
            "reskin.py",
            "--skin",
            "default",
            SKILL / "assets/example-architecture.html",
            "-o",
            "nested/requested.html",
            cwd=self.dir,
        )
        self.assertTrue((self.dir / "nested/requested.html").is_file())
        self.assertFalse((self.dir / "requested.html").exists())

    def test_renamed_treemap_and_no_tag_output_remain_valid(self):
        source = SKILL / "assets/example-treemap.html"
        target = self.dir / "new-map.html"
        self.cli("reskin.py", "--skin", "default", "--no-tag", source, "-o", target)
        self.assertFalse(self_check.verify(target)[0])
        self.assertIn('data-diagram-type="treemap"', target.read_text())

    def test_snapshot_detects_changed_paint_before_writing(self):
        p = self.file(self.source)
        skin = self.dir / "skin.html"
        out = self.dir / "out.html"
        self.cli("reskin.py", "--skin", "xinzhongshi", p, "-o", skin)
        skin.write_text(
            map_colors(skin.read_text(), lambda v: "#ff00ff" if v == "#c3272b" else v)
        )
        self.cli("reskin.py", "--skin", "default", skin, "-o", out, ok=False)
        self.assertFalse(out.exists())

    def test_css_and_svg_ids_and_content_are_never_color_values(self):
        source = '<style>#29314f { color: #29314f; content: "#29314f"; fill:url(#29314f) }</style><svg role="img"><text id="29314f" data-fill="#29314f" fill="#29314f">#29314f</text></svg>'
        changed = map_colors(source, lambda raw: "#522522")
        self.assertIn("#29314f { color: #522522;", changed)
        self.assertIn('content: "#29314f"', changed)
        self.assertIn("fill:url(#29314f)", changed)
        self.assertIn('data-fill="#29314f" fill="#522522">#29314f', changed)


if __name__ == "__main__":
    unittest.main()
