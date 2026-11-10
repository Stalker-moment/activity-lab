"""Start the portable checkout; does not reference the original workspace."""

from pathlib import Path
import os, sys

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    # dotenv intentionally tiny: only environment configuration, never shell eval.
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    import uvicorn

    sys.path.insert(0, str(ROOT / "backend"))
    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8765")),
        workers=1,
        access_log=False,
    )
