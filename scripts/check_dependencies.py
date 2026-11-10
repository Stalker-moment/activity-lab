"""Validate runtime dependencies, allowing contrib to satisfy the base OpenCV API."""

from importlib import metadata
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def dependency_errors(distributions=None):
    distributions = list(
        distributions if distributions is not None else metadata.distributions()
    )
    installed = {
        canonicalize_name(d.metadata["Name"]): d.version for d in distributions
    }
    problems = []
    wheels = [
        n
        for n in installed
        if n
        in [
            "opencv-python",
            "opencv-contrib-python",
            "opencv-python-headless",
            "opencv-contrib-python-headless",
        ]
    ]
    if wheels != ["opencv-contrib-python"]:
        problems.append(
            "Expected only opencv-contrib-python; installed: " + ", ".join(wheels)
        )
    for distribution in distributions:
        for text in distribution.requires or []:
            requirement = Requirement(text)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            name = canonicalize_name(requirement.name)
            if name == "opencv-python" and "opencv-contrib-python" in installed:
                name = "opencv-contrib-python"
            version = installed.get(name)
            if version is None or (
                requirement.specifier
                and not requirement.specifier.contains(version, prereleases=True)
            ):
                problems.append(
                    f"{distribution.metadata['Name']}: requires {requirement}; provider={name} {version}"
                )
    return problems


def main():
    errors = dependency_errors()
    if errors:
        raise SystemExit("\n".join(errors))
    import cv2
    import numpy as np

    assert cv2.__version__ == "4.12.0", cv2.__version__
    assert cv2.cvtColor(
        np.zeros((8, 8, 3), dtype=np.uint8), cv2.COLOR_BGR2GRAY
    ).shape == (8, 8)
    print(
        "PASS: dependencies valid; only OpenCV contrib 4.12.0, import and image conversion work."
    )
    print(
        "Ultralytics base OpenCV requirement is intentionally supplied by contrib (same cv2 API)."
    )


if __name__ == "__main__":
    main()
