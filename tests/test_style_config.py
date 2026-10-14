import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "skills/diagram-design-zh"
sys.path.insert(0, str(ROOT / "scripts"))
import self_check
from style_config import load_style_colors


class StyleConfigTests(unittest.TestCase):
    def test_custom_palette_comes_from_selected_profile(self):
        source = (ROOT / "assets/example-architecture.html").read_text()
        guide = (ROOT / "references/style-guide.md").read_text()
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            p = folder / "example-architecture.html"
            g = folder / "profile.md"
            p.write_text(
                source.replace("#1a4dd9", "#7048e8").replace("26,77,217", "112,72,232")
            )
            g.write_text(
                guide.replace("#1a4dd9", "#7048e8").replace("26,77,217", "112,72,232")
            )
            self.assertFalse(self_check.verify(p, g)[0])
            self.assertTrue(self_check.verify(p)[0])
            p.write_text(p.read_text().replace("#7048e8", "#123456"))
            self.assertTrue(self_check.verify(p, g)[0])

    def test_malformed_or_inaccessible_profile_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.md"
            p.write_text("No palette")
            self.assertRaises(ValueError, load_style_colors, p)
            errors, _ = self_check.verify(ROOT / "assets/example-architecture.html", p)
            self.assertTrue(any("生效样式指南无效" in e for e in errors))

    def test_low_contrast_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.md"
            p.write_text(
                (ROOT / "references/style-guide.md")
                .read_text()
                .replace("#29314f", "#eeeeee")
            )
            self.assertRaises(ValueError, load_style_colors, p)

    def test_translucent_foreground_is_composited_before_contrast_check(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.md"
            p.write_text(
                (ROOT / "references/style-guide.md")
                .read_text()
                .replace("`#29314f`", "`rgba(41,49,79,0.10)`", 1)
            )
            self.assertRaises(ValueError, load_style_colors, p)

    def test_latin_head_with_chinese_fallback_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "example-architecture.html"
            s = (
                (ROOT / "assets/example-architecture.html")
                .read_text()
                .replace("'MiSans'", "'Inter'")
            )
            p.write_text(s)
            self.assertFalse(self_check.verify(p)[0])

    def test_treemap_alpha_does_not_leak_into_other_types_or_bases(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "example-architecture.html"
            source = (ROOT / "assets/example-architecture.html").read_text()
            p.write_text(
                source.replace("rgba(86,94,126,0.08)", "rgba(86,94,126,0.04)", 1)
            )
            self.assertTrue(any("透明度" in e for e in self_check.verify(p)[0]))
            source = source.replace("rgba(86,94,126,0.08)", "rgba(41,49,79,0.04)", 1)
            p.write_text(source)
            self.assertTrue(any("透明度" in e for e in self_check.verify(p)[0]))
            p.write_text(
                source.replace("<svg ", '<svg data-diagram-type="state-lifecycle" ', 1)
            )
            self.assertFalse(self_check.verify(p)[0])

    def test_dark_container_does_not_replace_dark_page(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "style.md"
            s = (ROOT / "references/style-guide.md").read_text()
            s = s.replace(
                "| `paper-2` | 容器底（少用）；深色下与纸面同色 | `#f3f2ff` | `#0a0d1b` |",
                "| `paper-2` | 容器底 | `#f3f2ff` | `#10132a` |",
            )
            p.write_text(s)
            colors = load_style_colors(p)
            self.assertEqual(colors["dark-bg"][0], "#0a0d1b")
            self.assertEqual(colors["paper-2-dark"][0], "#10132a")


if __name__ == "__main__":
    unittest.main()
