"""仓库检查只读取项目文档，不扫描已忽略的依赖目录。"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PUBLIC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PUBLIC / "tools"))
import check_project


class ProjectDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q")
        self.write(".gitignore", ".venv-test/\nvendor/\n")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_ci_dependencies_and_git_metadata_do_not_become_project_docs(self):
        self.write("README.md", "[guide](docs/guide.md)")
        self.write("docs/guide.md", "[readme](../README.md)")
        self.git("add", "README.md")
        self.write(
            ".venv-test/lib/python3.12/site-packages/playwright/driver/package/lib/tools/skills/playwright-cli/SKILL.md",
            "[recording](.playwright-cli/page-2026-02-14T19-22-42-679Z.yml)",
        )
        self.write("vendor/another-package/README.md", "[missing](missing.md)")
        self.write(".git/cache/README.md", "[missing](missing.md)")
        self.assertEqual(check_project.check_document_links(self.root), [])

    def test_tracked_and_new_project_documents_still_reject_broken_links(self):
        self.write("README.md", "[missing](missing.md)")
        self.git("add", "README.md")
        self.write("docs/new.md", "[missing](also-missing.md)")
        # Ignore rules must not hide a document already owned by the repository.
        self.write(".gitignore", ".venv-test/\nvendor/\nREADME.md\n")
        errors = check_project.check_document_links(self.root)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any(error.startswith("README.md ") for error in errors))
        self.assertTrue(any(error.startswith("docs/new.md ") for error in errors))
        self.write("missing.md", "present")
        self.write("docs/also-missing.md", "present")
        self.assertEqual(check_project.check_document_links(self.root), [])


if __name__ == "__main__":
    unittest.main()
