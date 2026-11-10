"""Download only public official checkpoints with checksum validation.
ANN is a user-trained asset: import separately with import_ann.py.
"""

from pathlib import Path
import argparse, hashlib, json, shutil, urllib.request

ROOT = Path(__file__).resolve().parents[1]
REV = "6746d6a5202bf24300cd9bf36f457f174483d41b"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def download(record, folder):
    p = folder / record["file"]
    folder.mkdir(parents=True, exist_ok=True)
    if p.exists() and digest(p) == record["sha256"]:
        return
    tmp = p.with_suffix(p.suffix + ".partial")
    try:
        with (
            urllib.request.urlopen(record["url"], timeout=120) as source,
            tmp.open("wb") as target,
        ):
            shutil.copyfileobj(source, target)
        if digest(tmp) != record["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {p.name}")
        tmp.replace(p)
    finally:
        if tmp.exists():
            tmp.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-xclip", action="store_true")
    args = parser.parse_args()
    for record in json.loads(
        (ROOT / "docs/hybrid-sources.json").read_text(encoding="utf-8-sig")
    ):
        download(record, ROOT / "backend/models/hybrid")
    if not args.skip_xclip:
        from huggingface_hub import snapshot_download

        snapshot_download(
            "microsoft/xclip-base-patch16-zero-shot",
            revision=REV,
            local_dir=ROOT / "backend/models/xclip",
            allow_patterns=["*.json", "*.txt", "*.safetensors"],
        )
    print("Public checkpoints ready. ANN requires your exported project checkpoint.")
