from pathlib import Path
import runpy

ROOT = Path(r"C:\Users\Administrator\Desktop\py")
runpy.run_path(str(ROOT / "scripts_fb" / "brandportal_gender_age_to_sheets.py"), run_name="__main__")
