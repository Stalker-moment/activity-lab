from pathlib import Path
import argparse, hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    records = json.loads(
        (ROOT / "docs/ann-provenance.json").read_text(encoding="utf-8-sig")
    )["files"]
    for r in records:
        p = args.source / r["file"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
            raise SystemExit("ANN checksum mismatch: " + r["file"])
    out = ROOT / "backend/models/ann"
    out.mkdir(parents=True, exist_ok=True)
    for r in records:
        shutil.copy2(args.source / r["file"], out / r["file"])
    print("Original ANN verified and imported without changes.")
