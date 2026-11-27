import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `from src...` imports resolve on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.gui.admin_web import app
from src.gui.admin_web import app
from src.verification.notifier import router as discord_router

app.include_router(discord_router)