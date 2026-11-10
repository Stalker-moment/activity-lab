from pathlib import Path
import importlib.util, tempfile, unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "backend_installer",
    Path(__file__).resolve().parents[1] / "scripts/install_backend.py",
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_preserves_existing_config(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.object(installer, "ROOT", Path(d)),
        ):
            file = Path(d) / ".env"
            file.write_text("HOST=127.0.0.1\nPORT=9000\n")
            before = file.read_bytes()
            installer.prepare_config()
            self.assertEqual(before, file.read_bytes())

    def test_safe_cpu_defaults(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.object(installer, "ROOT", Path(d)),
        ):
            installer.prepare_config()
            text = (Path(d) / ".env").read_text()
            self.assertIn("DEVICE=cpu", text)
            self.assertIn("HOST=127.0.0.1", text)
            self.assertIn("MAX_INFLIGHT=1", text)

    def test_install_plan_is_cpu_and_imports_ann(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.object(installer, "ENV", Path(d) / "env"),
        ):
            commands = installer.installation_steps("uv")
            self.assertEqual(commands[0][1], "venv")
            self.assertTrue(
                any(
                    "https://download.pytorch.org/whl/cpu" in command
                    for command in commands
                )
            )
            self.assertTrue(
                any(
                    str(installer.ROOT / "scripts/import_ann.py") in command
                    for command in commands
                )
            )
            self.assertTrue(
                any(
                    str(installer.ROOT / "scripts/download_models.py") in command
                    for command in commands
                )
            )

    def test_existing_env_not_recreated(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch.object(installer, "ENV", Path(d) / "env"),
        ):
            python = installer.python_path()
            python.parent.mkdir(parents=True)
            python.touch()
            self.assertTrue(
                all(
                    command[1] != "venv"
                    for command in installer.installation_steps("uv")
                )
            )


if __name__ == "__main__":
    unittest.main()
