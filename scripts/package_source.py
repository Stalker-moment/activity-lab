from pathlib import Path
import zipfile
from check_release import check, ROOT

if __name__ == "__main__":
    target = ROOT.parent / "activity-lab-source.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in check():
            archive.write(file, Path(ROOT.name) / file.relative_to(ROOT))
    print(f"Created {target.name}: {target.stat().st_size:,} bytes (source only)")
