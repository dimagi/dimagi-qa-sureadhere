import os
from pathlib import Path

""""Contains Path Settings"""


class PathSettings:

    """Path Settings"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    if os.environ.get("CI") == "true":
        DOWNLOAD_PATH = Path("/home/runner/work/dimagi-qa-sureadhere/dimagi-qa-sureadhere")
    else:
        DOWNLOAD_PATH = Path('~/Downloads').expanduser()

    if os.environ.get("CI") == "true":
        ROOT = os.path.abspath(os.pardir) + "/dimagi-qa-sureadhere"
    else:
        ROOT = os.path.abspath(os.pardir)

    @staticmethod
    def _get_tesseract_path():
        # 1. ENV override (highest priority)
        if os.getenv("TESSERACT_CMD"):
            return os.getenv("TESSERACT_CMD")

        # 2. CI (Linux)
        if os.environ.get("CI") == "true":
            return "/usr/bin/tesseract"

        # 3. Windows - User install (AppData)
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            path = Path(local_appdata) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
            if path.exists():
                return str(path)

        # 4. Windows - System install (Program Files)
        program_files = os.getenv("ProgramFiles")
        if program_files:
            path = Path(program_files) / "Tesseract-OCR" / "tesseract.exe"
            if path.exists():
                return str(path)

        program_files_x86 = os.getenv("ProgramFiles(x86)")
        if program_files_x86:
            path = Path(program_files_x86) / "Tesseract-OCR" / "tesseract.exe"
            if path.exists():
                return str(path)

        return None

    TESSERACT_PATH = _get_tesseract_path()