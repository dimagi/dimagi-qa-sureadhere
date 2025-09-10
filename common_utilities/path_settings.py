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


