"""Add a frontend origin to backend CORS while preserving other dotenv settings."""

from pathlib import Path
from urllib.parse import urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]


def configure(path, origin):
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or "*" in origin
    ):
        raise ValueError(
            "Supply a single HTTP(S) origin without path, credentials, query or wildcard."
        )
    origin = f"{parsed.scheme}://{parsed.netloc}"
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    indices = [
        i for i, line in enumerate(lines) if line.strip().startswith("ALLOWED_ORIGINS=")
    ]
    if len(indices) > 1:
        raise ValueError("Multiple ALLOWED_ORIGINS entries; resolve duplicates first.")
    current = (
        lines[indices[0]].split("=", 1)[1].strip()
        if indices
        else "http://localhost:3000,http://127.0.0.1:3000"
    )
    values = list(
        dict.fromkeys([s.strip() for s in current.split(",") if s.strip()] + [origin])
    )
    if "*" in values:
        raise ValueError("Remove wildcard CORS before configuring an explicit origin.")
    replacement = "ALLOWED_ORIGINS=" + ",".join(values)
    if indices:
        lines[indices[0]] = replacement
    else:
        lines.append(replacement)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return origin


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", default="https://activity-lab.tierkun.com")
    args = parser.parse_args()
    print("Frontend origin allowed:", configure(ROOT / ".env", args.origin))
    print("Restart the backend for the configuration to take effect.")
