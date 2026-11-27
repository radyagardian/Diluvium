import os
import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from src.orchestrator.agent import DiluviumOrchestrator

router = APIRouter(prefix="/api/discord", tags=["Discord Bot"])

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")


def verify_discord_signature(signature: str, timestamp: str, body: bytes) -> bool:
    """Memverifikasi tanda tangan Ed25519 dari server Discord."""
    public_key = os.getenv("DISCORD_PUBLIC_KEY", "").strip()
    if not public_key or not signature or not timestamp:
        return False
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False


def build_discord_embed(title: str, description: str, siaga_level: str) -> Dict[str, Any]:
    """Membuat kartu pesan berwarna (Discord Embed) sesuai status Siaga 1-4."""
    color_map = {
        "Siaga 1": 0xEF4444,  # Merah
        "Siaga 2": 0xF97316,  # Oranye
        "Siaga 3": 0xEAB308,  # Kuning
        "Siaga 4": 0x22C55E,  # Hijau
    }
    color = 0x3B82F6
    for key, hex_color in color_map.items():
        if key.lower() in siaga_level.lower():
            color = hex_color
            break

    return {
        "title": title,
        "description": description[:4000],  # Batas maksimal karakter embed Discord
        "color": color,
        "footer": {"text": "Diluvium EWS • Sistem Peringatan Dini Banjir DKI Jakarta"},
    }


@router.post("/interactions")
async def discord_interactions(request: Request):
    """Endpoint utama HTTP Webhook untuk Slash Command Discord (Serverless-ready)."""
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    raw_body = await request.body()

    # 1. Wajib lolos verifikasi kriptografi Discord
    if not verify_discord_signature(signature, timestamp, raw_body):
        raise HTTPException(status_code=401, detail="Invalid request signature")

    payload = json.loads(raw_body)
    interaction_type = payload.get("type")

    # 2. Type 1: PING dari Discord saat verifikasi URL di Developer Portal
    if interaction_type == 1:
        return {"type": 1}

    # 3. Type 2: APPLICATION_COMMAND (Slash Command dari pengguna)
    if interaction_type == 2:
        data = payload.get("data", {})
        command_name = data.get("name")
        options = {opt["name"]: opt["value"] for opt in data.get("options", [])}

        orchestrator = DiluviumOrchestrator()

        # Command 1: /statusjakarta
        if command_name == "statusjakarta":
            summary = await orchestrator.run_all_areas()
            affected = summary["affected_count"]
            total = summary["total_monitored_areas"]

            if affected == 0:
                embed = build_discord_embed(
                    title="✅ Status Banjir DKI Jakarta: AMAN (Siaga 4)",
                    description=(
                        f"Seluruh **{total} wilayah kelurahan** yang dipantau saat ini berada dalam kondisi normal.\n\n"
                        f"{summary['alert_message']}"
                    ),
                    siaga_level="Siaga 4",
                )
            else:
                embed = build_discord_embed(
                    title=f"🚨 PERINGATAN BANJIR: {affected} Wilayah Terdampak!",
                    description=summary["alert_message"],
                    siaga_level="Siaga 1",
                )

            return {"type": 4, "data": {"embeds": [embed]}}

        # Command 2: /cekbanjir area_id:<kode_adm4>
        elif command_name == "cekbanjir":
            area_id = options.get("area_id", "31.74.01.1004").strip()
            result = await orchestrator.run_pipeline(area_id=area_id)

            tel = result["telemetry"]
            pred = result["prediction"]
            ver = result["verification"]

            desc = (
                f"**Status:** {ver['siaga_level']}\n"
                f"**Curah Hujan Lokal:** {tel['rainfall_rate_mm']} mm/jam\n"
                f"**TMA Pintu Air:** Katulampa `{tel['katulampa_level_cm']} cm` | "
                f"Depok `{tel['depok_level_cm']} cm` | Manggarai `{tel['manggarai_level_cm']} cm`\n"
                f"**Prediksi Genangan:** `{pred['predicted_depth_cm']} cm` (Radius `{pred['inundation_radius_km']} km`)\n"
                f"**Estimasi Air Tiba:** `{pred['estimated_arrival_hours']} jam`\n\n"
                f"{result['alert_message']}"
            )
            embed = build_discord_embed(
                title=f"🌊 Laporan Kondisi Banjir — Wilayah {area_id}",
                description=desc,
                siaga_level=ver["siaga_level"],
            )
            return {"type": 4, "data": {"embeds": [embed]}}

        # Command 3: /pintuair
        elif command_name == "pintuair":
            tel = await orchestrator.ingest_telemetry("31.74.01.1004")
            desc = (
                f"• **Bendung Katulampa:** `{tel.katulampa_level_cm} cm`\n"
                f"• **Pos Pantau Depok:** `{tel.depok_level_cm} cm`\n"
                f"• **Pintu Air Manggarai:** `{tel.manggarai_level_cm} cm`\n\n"
                f"_Ambang batas Manggarai: Normal < 750 cm | Siaga 3 ≥ 750 cm | Siaga 2 ≥ 850 cm | Siaga 1 ≥ 950 cm._"
            )
            siaga = "Siaga 1" if tel.manggarai_level_cm >= 850 else ("Siaga 3" if tel.manggarai_level_cm >= 750 else "Siaga 4")
            embed = build_discord_embed(
                title="📏 Tinggi Muka Air (TMA) Hulu–Hilir Ciliwung",
                description=desc,
                siaga_level=siaga,
            )
            return {"type": 4, "data": {"embeds": [embed]}}

    return {"type": 4, "data": {"content": "Perintah tidak dikenali oleh bot Diluvium."}}