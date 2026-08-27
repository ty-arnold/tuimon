from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR    = PROJECT_ROOT / "cache"
SAVES_DIR    = PROJECT_ROOT / "saves"
LOG_DIR      = PROJECT_ROOT / "logs"
STYLES_DIR   = PROJECT_ROOT / "src/" / "ui" / "styles"
