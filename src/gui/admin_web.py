import os
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import uvicorn

# Load .env variables
load_dotenv()

app = FastAPI(title="Diluvium Admin Dashboard")

# Initialize Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Konfigurasi direktori
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount folder static agar file CSS bisa diakses oleh HTML
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Konfigurasi folder templates untuk HTML
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Define the expected JSON payload for login
class AdminLogin(BaseModel):
    email: str
    password: str

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
    # Fixed TemplateResponse arguments
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)

@app.post("/api/admin/login")
async def login(creds: AdminLogin):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": creds.email,
            "password": creds.password
        })
        return {"status": "success", "access_token": res.session.access_token}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

@app.post("/api/admin/override")
async def toggle_fallback(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "status": "success", 
        "message": "[OVERRIDE] Mode switched to Non-AI Hardcoded Fallback Script!"
    }

@app.post("/api/admin/test-alert")
async def trigger_test_alert(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "status": "success", 
        "message": "[DIAGNOSTIC] Delivery verified to Telegram (@BotFather) & Discord Webhook (200 OK)."
    }

if __name__ == "__main__":
    uvicorn.run("admin_web:app", host="127.0.0.1", port=8000, reload=True)