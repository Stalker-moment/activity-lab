"""Check publication source candidates; runtime artifacts are excluded via Git."""

from pathlib import Path
import subprocess, re, json, hashlib

ROOT = Path(__file__).resolve().parents[1]


def source_files():
    # Requires gitignore interpretation, not a hand-maintained packaging exclusion list.
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        capture_output=True,
        check=True,
    )
    return [ROOT / p for p in result.stdout.decode().split("\0") if p]


def check():
    problems = []
    files = source_files()
    published = json.loads(
        (ROOT / "trained-models/manifest.json").read_text(encoding="utf-8")
    )["artifacts"]
    allowed = {item["file"]: item for item in published}
    for name, record in allowed.items():
        asset = ROOT / name
        if (
            not asset.is_file()
            or hashlib.sha256(asset.read_bytes()).hexdigest() != record["sha256"]
        ):
            problems.append(f"Published model checksum mismatch: {name}")
    for p in files:
        rel = p.relative_to(ROOT)
        if p.stat().st_size > 10_000_000:
            problems.append(f"Oversized source: {rel}")
        if rel.as_posix() not in allowed and p.suffix.lower() in {
            ".pt",
            ".h5",
            ".keras",
            ".safetensors",
            ".task",
            ".mp4",
            ".avi",
            ".log",
        }:
            problems.append(f"Runtime artifact in source: {rel}")
        if (
            p.name.startswith(".env")
            and p.name != ".env.example"
            and rel.as_posix() != "web/.env.production"
        ):
            problems.append(f"Environment secret file: {rel}")
        if (
            p.suffix
            in {".py", ".tsx", ".ts", ".md", ".json", ".yml", ".yaml", ".txt", ".ipynb"}
            and p.stat().st_size < 2_000_000
        ):
            text = p.read_text(encoding="utf-8-sig")
            if re.search(r"(?:ghp_|github_pat_|hf_)[A-Za-z0-9_]{24,}", text):
                problems.append(f"Credential pattern: {rel}")
    if problems:
        raise SystemExit("\n".join(problems))
    print(
        f"PASS: {len(files)} publication files; only manifest-approved models; no videos, env secrets or oversized source."
    )
    return files


if __name__ == "__main__":
    check()
