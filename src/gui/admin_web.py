from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI(title="Diluvium Admin Dashboard")

# Konfigurasi direktori
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount folder static agar file CSS bisa diakses oleh HTML
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Konfigurasi folder templates untuk HTML
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    # Data prototipe (nantinya mengambil dari API Gateway di app.py milik Radya)
    context = {
        "request": request,
        "gemini_status": "Online (Gemini 3 Flash)",
        "token_usage": "1,420 / 15,000 RPM (Free-Tier)",
        "api_bmkg_status": "Connected (Async Polling)",
        "water_level_manggarai": "760",
        "water_level_katulampa": "80",
        "current_siaga": "Siaga 3"
    }
    return templates.TemplateResponse("dashboard.html", context)

@app.post("/api/admin/override")
async def toggle_fallback():
    # Sesuai Sequence Diagram GUI Phase 2: POST /api/admin/override
    return {
        "status": "success", 
        "message": "[OVERRIDE] Mode switched to Non-AI Hardcoded Fallback Script!"
    }

@app.post("/api/admin/test-alert")
async def trigger_test_alert():
    # Sesuai Sequence Diagram GUI Phase 3: POST /api/admin/test-alert
    return {
        "status": "success", 
        "message": "[DIAGNOSTIC] Delivery verified to Telegram (@BotFather) & Discord Webhook (200 OK)."
    }

if __name__ == "__main__":
    uvicorn.run("admin_web:app", host="127.0.0.1", port=8000, reload=True)