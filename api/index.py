import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.gui.admin_web import app
from src.verification.notifier import router as discord_router

app.include_router(discord_router)