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

    def test_atlassian_config_is_environment_backed(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Workspace(Path(temp) / "workspace")
            workspace.init()
            config = json.loads(workspace.atlassian_config_path.read_text())
            self.assertEqual(config["site_url_env"], "ATLASSIAN_URL")
            self.assertNotIn("site_url", config)
            self.assertIn("api_token_env", config)

    def test_prompt_requires_harness_cli(self):
        self.assertIn("use the harness CLI for all work", build_prompt("inspect the project", []))

    def test_security_policy_classifies_commands(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Workspace(Path(temp) / "workspace")
            workspace.init()
            self.assertEqual(workspace.check_command("git pull --rebase")["status"], "approved")
            self.assertEqual(workspace.check_command("rg --files")["status"], "safe_read_only")
            self.assertEqual(workspace.check_command("rm -rf ./tmp")["status"], "blocked")
            self.assertEqual(workspace.check_command("curl https://example.com")["status"], "requires_approval")
            self.assertEqual(workspace.check_command("rg foo && npm test")["status"], "blocked")

    def test_conventional_commit_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Workspace(Path(temp) / "workspace")
            workspace.init()
            self.assertEqual(workspace.check_commit_message("feat(cli): add policy check")["status"], "valid")
            self.assertEqual(workspace.check_commit_message("Add policy check")["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
