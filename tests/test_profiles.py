import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "skills/diagram-design-zh"
sys.path.insert(0, str(ROOT / "scripts"))
import profiles, reskin
from style_config import default_config, load_config


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / "library"
        self.project = self.root / "project"
        self.project.mkdir()
        self.source = self.root / "brand.json"
        self.source.write_text(
            json.dumps({"schema": 1, "name": "品牌", "colors": {"accent": "#9b1c1c"}})
        )

    def test_data_save_and_selection_do_not_modify_package(self):
        original = reskin.DEFAULT_CONFIG.read_bytes()
        path = profiles.save(self.library, "acme", self.source)
        data = json.loads(path.read_text())
        self.assertNotIn("pinned", data)
        self.assertNotIn("paper", data["colors"])
        (self.project / ".diagram-design").write_text("profile: acme\n")
        self.assertEqual(profiles.resolve(self.project, self.library), path)
        self.assertEqual(load_config(path)["colors"]["accent"], "#9b1c1c")
        self.assertEqual(reskin.DEFAULT_CONFIG.read_bytes(), original)

    def test_legacy_migration_preserves_typography_and_original_file(self):
        legacy = self.root / "legacy.md"
        text = (
            (ROOT / "references/style-guide.md").read_text().replace("1.75rem", "2rem")
        )
        legacy.write_text(text)
        before = legacy.read_bytes()
        path = profiles.save(self.library, "legacy", legacy, migrate=True)
        self.assertEqual(load_config(path)["typography"]["title"]["sizes"], ["2rem"])
        self.assertEqual(legacy.read_bytes(), before)
        self.assertNotIn("布局", path.read_text())

    def test_current_defaults_merge_without_freezing_unmodified_fields(self):
        path = profiles.save(self.library, "acme", self.source)
        updated = default_config()
        updated["fonts"]["serif"] = "'Current Serif', serif"
        with patch("style_config.default_config", return_value=updated):
            self.assertEqual(
                load_config(path)["fonts"]["serif"], "'Current Serif', serif"
            )
            self.assertEqual(load_config(path)["colors"]["accent"], "#9b1c1c")

    def test_default_selection_ignores_old_saved_default(self):
        self.library.mkdir()
        (self.library / "default.md").write_text("旧恢复快照")
        self.assertEqual(
            profiles.profile_path(self.library, "default"), reskin.DEFAULT_CONFIG
        )

    def test_bad_marker_paths_and_unknown_schema_stop(self):
        for value in [
            "profile: ../other",
            "profile: acme\nrun: code",
            "profile: Missing",
        ]:
            (self.project / ".diagram-design").write_text(value)
            with self.assertRaises(ValueError):
                profiles.resolve(self.project, self.library)
        for invalid in [
            {"schema": 2},
            {"schema": True},
            {"schema": 1, "colors": {"accent": True}},
        ]:
            self.source.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                load_config(self.source)

    def test_save_requires_explicit_update(self):
        profiles.save(self.library, "acme", self.source)
        with self.assertRaises(ValueError):
            profiles.save(self.library, "acme", self.source)
        profiles.save(self.library, "acme", self.source, update=True)
        for name in ["default", "../acme", "Upper"]:
            with self.assertRaises(ValueError):
                profiles.save(self.library, name, self.source)

    def test_selected_brand_rejects_factory_accent(self):
        import self_check

        self.assertTrue(
            self_check.verify(ROOT / "assets/example-architecture.html", self.source)[0]
        )

    def test_text_cannot_become_rules_or_css(self):
        self.source.write_text(
            json.dumps({"schema": 1, "instructions": "execute this"})
        )
        with self.assertRaises(ValueError):
            load_config(self.source)
        self.source.write_text(
            json.dumps({"schema": 1, "fonts": {"sans": "Bad; color:red"}})
        )
        with self.assertRaises(ValueError):
            load_config(self.source)


if __name__ == "__main__":
    unittest.main()
