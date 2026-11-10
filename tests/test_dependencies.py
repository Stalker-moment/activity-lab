import importlib.util, unittest
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location(
    "dependency_check",
    Path(__file__).resolve().parents[1] / "scripts/check_dependencies.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def dist(name, version, requires=()):
    return SimpleNamespace(
        metadata={"Name": name}, version=version, requires=list(requires)
    )


class DependencyTests(unittest.TestCase):
    def test_contrib_satisfies_base_api_requirement(self):
        self.assertEqual(
            module.dependency_errors(
                [
                    dist("opencv-contrib-python", "4.12.0.88"),
                    dist("ultralytics", "8.4.208", ["opencv-python>=4.7.0"]),
                ]
            ),
            [],
        )

    def test_overlapping_wheels_rejected(self):
        self.assertTrue(
            module.dependency_errors(
                [
                    dist("opencv-python", "4.12.0.88"),
                    dist("opencv-contrib-python", "4.12.0.88"),
                ]
            )
        )

    def test_other_missing_dependencies_not_hidden(self):
        errors = module.dependency_errors(
            [
                dist("opencv-contrib-python", "4.12.0.88"),
                dist("test", "1", ["missing-runtime>=1"]),
            ]
        )
        self.assertTrue(any("missing-runtime" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
