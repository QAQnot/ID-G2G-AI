import subprocess
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\Administrator\Desktop\py")
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
DOWNLOAD_BATCH = ROOT / "skill" / "brandportal-buyer-sync" / "scripts" / "brandportal_buyer_download_batch.py"
SYNC = ROOT / "skill" / "brandportal-buyer-sync" / "scripts" / "brandportal_gender_age_to_sheets.py"


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit("Usage: brandportal_sync_pipeline.py YYYY-MM [YYYY-MM-DD]")
    print("Confirm the target shop name or shop ID before running this pipeline.")
    subprocess.run([str(PYTHON), str(DOWNLOAD_BATCH), *args], check=True)
    subprocess.run([str(PYTHON), str(SYNC)], check=True)


if __name__ == "__main__":
    main()
