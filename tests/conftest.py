import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(BASE_DIR))