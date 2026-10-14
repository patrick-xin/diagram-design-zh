import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / "skills/diagram-design-zh"
sys.path.insert(0, str(ROOT / "scripts"))
import content_check


class ContentTests(unittest.TestCase):
    def test_numeric_labels_and_geometry_are_checked_together(self):
        svg = '<svg role="img"><rect id="bar" height="144"/><text id="label">2.4</text></svg>'
        model = {
            "schema": 1,
            "values": {"a": 2.4},
            "encodings": [
                {"element": "bar", "key": "a", "attribute": "height", "scale": 60},
                {"element": "label", "key": "a", "attribute": "text"},
            ],
        }
        self.assertFalse(content_check.verify(svg, model))
        self.assertTrue(content_check.verify(svg.replace("144", "72"), model))
        self.assertTrue(content_check.verify(svg.replace("2.4", "1.2"), model))

    def model(self):
        return {
            "schema": 1,
            "nodes": [
                {"source_ids": ["A"], "element": "na"},
                {"source_ids": ["B"], "element": "nb"},
            ],
            "edges": [
                {"source_ids": ["e1"], "element": "edge", "label_element": "label"}
            ],
        }

    def ir(self):
        return {
            "diagrams": [
                {
                    "nodes": [{"id": "A"}, {"id": "B"}],
                    "edges": [
                        {"id": "e1", "source": "A", "target": "B", "label": "HTTPS"}
                    ],
                }
            ]
        }

    def html(self):
        return '<svg role="img"><g id="na"/><g id="nb"/><path id="edge" data-source="na" data-target="nb"/><text id="label">HTTPS</text></svg>'

    def test_ir_missing_relations_and_wrong_endpoint_are_detected(self):
        self.assertFalse(content_check.verify(self.html(), self.model(), self.ir()))
        model = self.model()
        model["edges"] = []
        self.assertTrue(content_check.verify(self.html(), model, self.ir()))
        self.assertTrue(
            content_check.verify(
                self.html().replace('data-source="na"', 'data-source="nb"'),
                self.model(),
                self.ir(),
            )
        )

    def test_omissions_are_named_and_have_reasons(self):
        model = self.model()
        model["edges"] = []
        model["omitted"] = [{"kind": "edge", "id": "e1", "reason": "用户要求仅画节点"}]
        self.assertFalse(content_check.verify(self.html(), model, self.ir()))
        model["omitted"][0].pop("reason")
        self.assertTrue(content_check.verify(self.html(), model, self.ir()))

    def test_nonempty_labels_must_be_visible(self):
        self.assertTrue(
            content_check.verify(
                self.html().replace("HTTPS", "HTTP"), self.model(), self.ir()
            )
        )

    def test_source_fields_and_fragments_are_accounted_for(self):
        ir = self.ir()
        ir["diagrams"][0]["nodes"][0]["fields"] = ["id PK"]
        self.assertTrue(content_check.verify(self.html(), self.model(), ir))
        model = self.model()
        model["source_facts"] = {
            "fields": {"A": ["id PK"]},
            "fragments": [],
            "notes": [],
        }
        self.assertFalse(content_check.verify(self.html(), model, ir))

    def test_empty_or_executable_models_do_not_pass(self):
        with self.assertRaises(ValueError):
            content_check.verify(self.html(), {"schema": 1})
        for value in [True, float("nan"), "2*3"]:
            with self.assertRaises(ValueError):
                content_check.number(value)


if __name__ == "__main__":
    unittest.main()
