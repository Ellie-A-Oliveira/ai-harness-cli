import json
import tempfile
import unittest
from pathlib import Path

from harness.core import Workspace, build_prompt


class WorkspaceTests(unittest.TestCase):
    def test_init_add_index_and_search(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            source = Path(temp) / "repo"
            source.mkdir()
            (source / "README.md").write_text("Retrieval uses chunks and ranking for useful context.")
            workspace = Workspace(root)
            workspace.init()
            workspace.add(source)
            self.assertEqual(workspace.index(), 1)
            results = workspace.search("chunk ranking")
            self.assertEqual(results[0]["path"], "README.md")
            self.assertIn("Retrieval", build_prompt("improve retrieval", results))

    def test_ignores_generated_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            source = Path(temp) / "repo"
            (source / "node_modules").mkdir(parents=True)
            (source / "node_modules" / "bad.md").write_text("secret")
            (source / "good.md").write_text("good context")
            workspace = Workspace(root)
            workspace.init()
            workspace.add(source)
            workspace.index()
            index = json.loads(workspace.index_path.read_text())
            self.assertEqual(len(index["chunks"]), 1)


if __name__ == "__main__":
    unittest.main()
