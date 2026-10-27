"""Download the Kaggle competition data into data/raw.

Usage:
    download-data            # or: python -m my_project.download
    download-data --force    # re-download even if data/raw is non-empty

Authentication is handled by the `kaggle` CLI. It reads credentials from, in
order: environment variables (KAGGLE_API_TOKEN, or the older KAGGLE_USERNAME +
KAGGLE_KEY), or ~/.kaggle/kaggle.json. You must also have joined the competition
and accepted its rules on kaggle.com, or the download fails with a 403.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path

COMPETITION = "nfl-big-data-bowl-2027"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

HELP = f"""
Kaggle download failed. Common causes:
  401 Unauthorized -> credentials missing/invalid. Create a token at
                      https://www.kaggle.com/settings and either set the
                      KAGGLE_API_TOKEN env var or save ~/.kaggle/kaggle.json
                      (chmod 600).
  403 Forbidden    -> you haven't joined the competition / accepted its rules:
                      https://www.kaggle.com/competitions/{COMPETITION}/rules
"""


def has_data(raw_dir: Path = RAW_DIR) -> bool:
    """True if raw_dir contains anything besides the .gitkeep placeholder."""
    if not raw_dir.exists():
        return False
    return any(p.name != ".gitkeep" for p in raw_dir.iterdir())


def download(competition: str = COMPETITION, dest: Path = RAW_DIR, force: bool = False) -> Path:
    """Download and unzip the competition files into `dest` (idempotent)."""
    dest.mkdir(parents=True, exist_ok=True)
    if has_data(dest) and not force:
        print(f"{dest} already has data; skipping (use --force to re-download).")
        return dest

    kaggle = shutil.which("kaggle")
    if kaggle is None:
        raise SystemExit("kaggle CLI not found. Run: pip install -e '.[data]'")

    cmd = [kaggle, "competitions", "download", "-c", competition, "-p", str(dest)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(HELP) from exc

    zip_path = dest / f"{competition}.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest)
        zip_path.unlink()
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="re-download")
    parser.add_argument("--competition", default=COMPETITION)
    args = parser.parse_args()
    download(args.competition, force=args.force)


if __name__ == "__main__":
    main()
