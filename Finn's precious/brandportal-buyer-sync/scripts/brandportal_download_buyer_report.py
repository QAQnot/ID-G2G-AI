from pathlib import Path
import runpy

ROOT = Path(r"C:\Users\Administrator\Desktop\py")
runpy.run_path(str(ROOT / "temp_scripts" / "brandportal_download_buyer_report.py"), run_name="__main__")
