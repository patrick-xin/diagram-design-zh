import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PUBLIC = Path(__file__).resolve().parents[1]
ROOT = PUBLIC / "skills/diagram-design-zh"
sys.path.insert(0, str(PUBLIC / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))
import catalog, screenshots, reading_check
from html_tools import select_svg
from export import svg_dimensions
from test_export import BROWSER


class ResourceTests(unittest.TestCase):
    def test_supported_variant_routes_are_discoverable(self):
        self.assertEqual(catalog.search("蜂群")[0]["id"], "scatter")
        self.assertTrue(catalog.search("beeswarm"))
        self.assertEqual(len(catalog.search("")), 45)

    def test_source_changes_invalidate_thumbnail_cache(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "source.html"
            path.write_text("before")
            before = screenshots.fingerprint(path)
            path.write_text("after")
            self.assertNotEqual(before, screenshots.fingerprint(path))

    def test_reading_preparation_preserves_svg_and_is_idempotent(self):
        original = (ROOT / "assets/example-architecture.html").read_text()
        updated = reading_check.prepare(original, 1000)
        self.assertEqual(select_svg(original).source, select_svg(updated).source)
        self.assertEqual(updated, reading_check.prepare(updated, 1000))


@unittest.skipUnless(
    importlib.util.find_spec("playwright") and BROWSER, "browser required"
)
class ReadingTests(unittest.TestCase):
    def test_scroll_container_clipping_is_detected_before_repair(self):
        source = ROOT / "assets/example-bar.html"
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / source.name
            output.write_text(
                reading_check.prepare(source.read_text(), 1000).replace(
                    "padding: 16px;", "padding: 0;"
                )
            )
            for width in (360, 1280):
                with self.subTest(width=width):
                    evidence = reading_check.measure(output, width, 900, BROWSER)
                    victims = {
                        item["text"]: item["sides"]
                        for item in evidence["clippedElements"]
                    }
                    self.assertIn("top", victims["万人"])
                    self.assertIn("left", victims["新增用户（万人）"])

    def test_all_reading_examples_preserve_geometry_and_visible_bounds(self):
        from playwright.sync_api import sync_playwright

        sources = sorted((ROOT / "assets").glob("example-*.html"))
        self.assertTrue(sources)
        with sync_playwright() as p:
            engine = p.chromium.launch(executable_path=BROWSER)
            try:
                # Only test complete static layout. Never execute source scripts
                # or follow imported URLs while loading in-memory fixtures.
                context = engine.new_context(java_script_enabled=False)
                context.route("**/*", lambda route: route.abort())
                page = context.new_page()

                def measure_fixture(html, width):
                    page.set_viewport_size({"width": width, "height": 900})
                    page.set_content(html, wait_until="load")
                    return reading_check.measure_page(page)

                for source in sources:
                    with self.subTest(source=source.name):
                        original = source.read_bytes()
                        html = original.decode()
                        measured = measure_fixture(html, 360)
                        logical_width, _ = svg_dimensions(select_svg(html).source)
                        factor = (
                            10 / measured["minCjkScreenPx"]
                            if measured["minCjkScreenPx"]
                            else 1
                        )
                        needed = (
                            math.ceil(
                                max(logical_width, measured["svgWidth"] * factor) / 4
                            )
                            * 4
                        )
                        output = reading_check.prepare(
                            html, needed, bleed=measured["svgBleedRatio"]
                        )
                        self.assertEqual(
                            select_svg(html).source, select_svg(output).source
                        )
                        self.assertEqual(
                            output,
                            reading_check.prepare(
                                output, needed, bleed=measured["svgBleedRatio"]
                            ),
                        )
                        for width in (360, 1280, 1920):
                            with self.subTest(width=width):
                                evidence = measure_fixture(output, width)
                                self.assertEqual(evidence["clippedElements"], [])
                                if evidence["minCjkScreenPx"] is not None:
                                    self.assertGreaterEqual(
                                        evidence["minCjkScreenPx"], 9.99
                                    )
                                self.assertLessEqual(
                                    evidence["documentWidth"], width + 1
                                )
                        self.assertEqual(source.read_bytes(), original)
            finally:
                engine.close()

    def test_narrow_scroll_version_has_readable_text_without_page_overflow(self):
        source = ROOT / "assets/example-architecture.html"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / source.name
            output.write_text(reading_check.prepare(source.read_text(), 1000))
            evidence = reading_check.measure(output, 360, 800, BROWSER)
            self.assertGreaterEqual(evidence["minCjkScreenPx"], 9.99)
            self.assertLessEqual(evidence["documentWidth"], 361)
            desktop = reading_check.measure(output, 1280, 900, BROWSER)
            self.assertGreaterEqual(desktop["minCjkScreenPx"], 9.99)
        self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
