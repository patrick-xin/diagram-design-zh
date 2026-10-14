import importlib.util
import sys
from pathlib import Path
import tempfile
import os
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / "skills/diagram-design-zh"
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "diagram_export", ROOT / "scripts/export.py"
)
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class SvgExportTests(unittest.TestCase):
    def test_nested_icon_is_preserved_with_main_diagram(self):
        svg = '<svg role="img" viewBox="0 0 1000 360"><title id="keep">图</title><svg viewBox="0 0 24 24"><path d="M0 0"/></svg><text>后续节点</text></svg>'
        selected = export.first_svg("<html><body>" + svg + "</body></html>")
        self.assertEqual(selected, svg)
        document = ET.fromstring(export.standalone_svg(selected))
        self.assertTrue(any(e.text == "后续节点" for e in document.iter()))

    def test_powerpoint_conversion_does_not_match_suffix_attributes(self):
        svg = '<svg role="img" viewBox="0 0 1000 360"><path data-fill="rgba(41,49,79,0.10)" fill="rgba(41,49,79,0.10)"/></svg>'
        converted = export.standalone_svg(svg, True)
        self.assertIn('data-fill="rgba(41,49,79,0.10)"', converted)
        self.assertIn('fill="#29314f" fill-opacity="0.10"', converted)

    def test_real_svg_export_preserves_title_ids_and_main_geometry(self):
        original = export.first_svg(
            (ROOT / "assets/example-architecture.html").read_text()
        )
        converted = export.standalone_svg(original)
        tree = ET.fromstring(converted)
        self.assertEqual(tree.attrib["viewBox"], "0 0 1000 360")
        self.assertEqual(tree[0].attrib["id"], "example-architecture-title")
        self.assertEqual(
            tree.attrib["aria-labelledby"],
            "example-architecture-title example-architecture-desc",
        )


def browser_path():
    configured = os.environ.get("DDZH_BROWSER_EXECUTABLE")
    if configured:
        return configured
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome.exists():
        return str(chrome)
    if importlib.util.find_spec("playwright"):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            executable = p.chromium.executable_path
            if Path(executable).is_file():
                return executable
    return None


BROWSER = browser_path()


@unittest.skipUnless(
    importlib.util.find_spec("playwright") and BROWSER,
    "Playwright + Chrome/Chromium required",
)
class PngExportTests(unittest.TestCase):
    def test_real_pixel_dimensions_fractional_scale_and_source_unchanged(self):
        from PIL import Image

        source = ROOT / "assets/example-architecture.html"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "diagram.png"
            export.png_export(source, target, 1.25, BROWSER)
            with Image.open(target) as image:
                self.assertEqual(image.size, (1250, 450))
        self.assertEqual(source.read_bytes(), original)

    def test_motion_exports_stable_complete_frame(self):
        from PIL import Image

        source = ROOT / "assets/example-policy-trace-animated.html"
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "motion.png"
            export.png_export(source, target, 1, BROWSER)
            size = export.svg_dimensions(export.first_svg(source.read_text()))
            with Image.open(target) as image:
                self.assertEqual(image.size, tuple(map(int, size)))


if __name__ == "__main__":
    unittest.main()
