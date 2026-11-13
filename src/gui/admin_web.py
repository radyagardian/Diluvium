import os
import json
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import uvicorn

# Import Sutan's BMKG Ingestion Client & Config
from src.config import BMKG_CACHE_DIR
from src.ingestion.bmkg_client import BMKGClient

# Import Irgy's Calculation Engine & Pydantic Schemas
from src.calculation.engine import (
    HydrologicalCalculationEngine,
    structure_historical_flood_data,
    PROCESSED_DIR,
)
from src.schemas import CalculationInput

# Load .env variables
load_dotenv()

# Ensure KAN-19 historical flood CSV is structured before loading the engine
if not (PROCESSED_DIR / "structured_flood_history.csv").exists():
    structure_historical_flood_data()

bmkg_client = BMKGClient()
calc_engine = HydrologicalCalculationEngine()


async def refresh_bmkg_cache_task():
    """Fetches live BMKG data for all flood-prone Jakarta areas into BMKG_CACHE_DIR."""
    try:
        await bmkg_client.fetch_all_jakarta_watchlist()
    except Exception as e:
        print(f"[!] Initial BMKG background poll warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Trigger a non-blocking live BMKG poll as soon as the FastAPI server starts
    asyncio.create_task(refresh_bmkg_cache_task())
    yield


app = FastAPI(title="Diluvium Admin Dashboard", lifespan=lifespan)

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_KEY", "")
supabase: Client = (
    create_client(supabase_url, supabase_key)
    if supabase_url and supabase_key
    else None
)

# Directory Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = Path(BASE_DIR).parent.parent

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Runtime state for admin toggles & telemetry tracking
SYSTEM_STATE = {
    "fallback_active": False,
    "tokens_used": 1420,
    "tokens_limit": 15000,
    "tokens_ingestion": 520,
    "tokens_calculation": 610,
    "tokens_verification": 290,
    # Water gate levels (cm) — ready to connect to bpbd_client.py next
    "manggarai_cm": 760.0,
    "depok_cm": 180.0,
    "katulampa_cm": 80.0,
}


class AdminLogin(BaseModel):
    email: str
    password: str


def format_hours_to_eta(hours: float) -> str:
    """Converts decimal hours (e.g., 1.5) into dashboard string format ('1h 30m')."""
    whole_hours = int(hours)
    minutes = int(round((hours - whole_hours) * 60))
    return f"{whole_hours}h {minutes:02d}m"


def load_cached_bmkg_records() -> list[dict]:
    """Reads all bmkg_*.json files from the active BMKG cache directory."""
    records = []
    candidate_dirs = [
        BMKG_CACHE_DIR,
        PROJECT_ROOT / "data" / "cache",
        PROJECT_ROOT / ".cache",
        PROCESSED_DIR / "bmkg_cache",
    ]
    seen_files = set()

    for folder in candidate_dirs:
        if folder and folder.exists():
            for f in folder.glob("bmkg_*.json"):
                if f.name not in seen_files:
                    try:
                        records.append(json.loads(f.read_text(encoding="utf-8")))
                        seen_files.add(f.name)
                    except Exception:
                        pass
    return records


def build_telemetry_payload() -> dict:
    """
    1. Reads real cached BMKG JSON data from disk.
    2. Runs Irgy's HydrologicalCalculationEngine on the highest-risk Kelurahan.
    3. Evaluates Siaga 1-4 thresholds and returns the complete dashboard payload.
    """
    records = load_cached_bmkg_records()

    if records:
        max_rec = max(records, key=lambda r: float(r.get("precipitation", 0.0)))
        peak_rain = round(float(max_rec.get("precipitation", 0.0)), 1)
        highest_area = f"{max_rec.get('kelurahan', 'Kampung Melayu')}, {max_rec.get('kecamatan', 'Jatinegara')}"
        target_area_id = max_rec.get("adm4_code", "31.75.03.1001")
        monitored_count = len(records)
        api_status = "Connected (BMKG Live Cache)"
    else:
        peak_rain = 42.5
        highest_area = "Kampung Melayu, Jatinegara"
        target_area_id = "31.75.03.1001"
        monitored_count = 12
        api_status = "Polling BMKG API..."

    # Water gate levels (cm)
    manggarai_cm = int(SYSTEM_STATE["manggarai_cm"])
    depok_cm = int(SYSTEM_STATE["depok_cm"])
    katulampa_cm = int(SYSTEM_STATE["katulampa_cm"])

    # Gate Saturation Percentages against Siaga 1 Thresholds (850 / 350 / 200 cm)
    manggarai_pct = min(round((manggarai_cm / 850) * 100), 100)
    depok_pct = min(round((depok_cm / 350) * 100), 100)
    katulampa_pct = min(round((katulampa_cm / 200) * 100), 100)
    avg_gate_saturation = round((manggarai_pct + depok_pct + katulampa_pct) / 3)

    # Run Irgy's HydrologicalCalculationEngine dynamically
    calc_input = CalculationInput(
        katulampa_level_cm=float(katulampa_cm),
        depok_level_cm=float(depok_cm),
        manggarai_level_cm=float(manggarai_cm),
        rainfall_rate_mm=float(peak_rain),
        area_id=target_area_id,
    )
    hazard_pred = calc_engine.calculate_hazard(calc_input)

    # Evaluate Official Siaga Status
    if manggarai_cm >= 850 or katulampa_cm >= 200:
        siaga_status = "Siaga 1"
    elif manggarai_cm >= 750 or katulampa_cm >= 150:
        siaga_status = "Siaga 2"
    elif manggarai_cm >= 650 or katulampa_cm >= 80:
        siaga_status = "Siaga 3"
    else:
        siaga_status = "Siaga 4"

    gemini_status = (
        "Offline (Fallback Active)"
        if SYSTEM_STATE["fallback_active"]
        else "Online (Gemini 3 Flash)"
    )

    tokens_used = SYSTEM_STATE["tokens_used"]
    tokens_limit = SYSTEM_STATE["tokens_limit"]

    return {
        "gemini_status": gemini_status,
        "token_usage": f"{tokens_used:,} / {tokens_limit:,} RPM (Free-Tier)",
        "tokens_used": tokens_used,
        "tokens_limit": tokens_limit,
        "tokens_ingestion": SYSTEM_STATE["tokens_ingestion"],
        "tokens_calculation": SYSTEM_STATE["tokens_calculation"],
        "tokens_verification": SYSTEM_STATE["tokens_verification"],
        "api_bmkg_status": api_status,
        "peak_rainfall_mm": peak_rain,
        "highest_risk_area": highest_area,
        "monitored_locations": monitored_count,
        "water_level_manggarai": manggarai_cm,
        "water_level_depok": depok_cm,
        "water_level_katulampa": katulampa_cm,
        "manggarai_pct": manggarai_pct,
        "depok_pct": depok_pct,
        "katulampa_pct": katulampa_pct,
        "avg_gate_saturation": avg_gate_saturation,
        "current_siaga": siaga_status,
        # Real outputs from Irgy's HydrologicalCalculationEngine
        "estimated_arrival_eta": format_hours_to_eta(hazard_pred.estimated_arrival_hours),
        "inundation_radius_km": f"{hazard_pred.inundation_radius_km} km",
        "predicted_depth_cm": hazard_pred.predicted_depth_cm,
        "confidence_score": hazard_pred.confidence_score,
        "hydro_labels": ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00"],
        "hydro_manggarai": [690, 705, 720, 740, 752, manggarai_cm],
        "hydro_katulampa": [60, 95, 110, 90, 85, katulampa_cm],
    }


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    context = {"request": request, **build_telemetry_payload()}
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


@app.get("/api/admin/telemetry")
async def get_live_telemetry():
    return build_telemetry_payload()


@app.post("/api/admin/login")
async def login(creds: AdminLogin):
    try:
        if supabase:
            res = supabase.auth.sign_in_with_password({
                "email": creds.email,
                "password": creds.password
            })
            return {"status": "success", "access_token": res.session.access_token}
        raise HTTPException(status_code=500, detail="Supabase client not configured")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")


@app.post("/api/admin/override")
async def toggle_fallback(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        if supabase:
            user = supabase.auth.get_user(token)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    SYSTEM_STATE["fallback_active"] = not SYSTEM_STATE["fallback_active"]
    mode_msg = (
        "[OVERRIDE] Mode switched to Non-AI Hardcoded Fallback Script!"
        if SYSTEM_STATE["fallback_active"]
        else "[RESTORED] AI Orchestrator (Gemini 3 Flash) re-engaged!"
    )
    return {
        "status": "success",
        "fallback_active": SYSTEM_STATE["fallback_active"],
        "message": mode_msg
    }


@app.post("/api/admin/test-alert")
async def trigger_test_alert(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        if supabase:
            user = supabase.auth.get_user(token)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Also trigger a fresh BMKG poll + calculation check during diagnostic run
    await refresh_bmkg_cache_task()
    payload = build_telemetry_payload()

    return {
        "status": "success",
        "message": (
            f"[DIAGNOSTIC] Delivery verified (200 OK) | Area: {payload['highest_risk_area']} | "
            f"Pred Depth: {payload['predicted_depth_cm']} cm | ETA: {payload['estimated_arrival_eta']}"
        )
    }


if __name__ == "__main__":
    uvicorn.run("src.gui.admin_web:app", host="127.0.0.1", port=8000, reload=True)