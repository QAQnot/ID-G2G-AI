from pathlib import Path
import runpy

ROOT = Path(r"C:\Users\Administrator\Desktop\py")
runpy.run_path(str(ROOT / "scripts_fb" / "brandportal_buyer_category_batch_to_sheet.py"), run_name="__main__")
