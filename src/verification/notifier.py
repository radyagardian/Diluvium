import asyncio
import json
import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from src.orchestrator.agent import DiluviumOrchestrator

router = APIRouter(prefix="/api/discord", tags=["Discord Bot"])

DISCORD_APP_ID = os.getenv("DISCORD_APPLICATION_ID", "").strip()


def verify_discord_signature(signature: str, timestamp: str, body: bytes) -> bool:
    """Memverifikasi tanda tangan Ed25519 dari server Discord."""
    public_key = os.getenv("DISCORD_PUBLIC_KEY", "").strip()
    if not public_key or not signature or not timestamp:
        return False
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode("utf-8") + body, bytes.fromhex(signature))
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
        "description": description[:4000],
        "color": color,
        "footer": {"text": "Diluvium EWS • Sistem Peringatan Dini Banjir DKI Jakarta"},
    }


async def patch_discord_original_message(
    application_id: str,
    interaction_token: str,
    embed: Dict[str, Any],
) -> None:
    """Mengirim balasan akhir ke pesan deferred Discord."""
    if not application_id or not interaction_token:
        return

    url = (
        f"https://discord.com/api/v10/webhooks/"
        f"{application_id}/{interaction_token}/messages/@original"
    )
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.patch(url, json={"embeds": [embed]})
            resp.raise_for_status()
    except Exception as e:
        print(f"[DISCORD FOLLOWUP ERROR] Gagal mengirim balasan lanjutan: {e}")


async def _handle_cekbanjir_followup(
    area_id: str,
    application_id: str,
    interaction_token: str,
) -> None:
    """Menjalankan pipeline /cekbanjir di latar belakang lalu memperbarui pesan Discord."""
    try:
        orchestrator = DiluviumOrchestrator()
        result = await asyncio.wait_for(
            orchestrator.run_pipeline(area_id=area_id),
            timeout=25.0,
        )

        tel = result["telemetry"]
        pred = result["prediction"]
        ver = result["verification"]

        desc = (
            f"**Status:** {ver['siaga_level']}\n"
            f"**Curah Hujan Lokal:** {tel['rainfall_rate_mm']} mm/jam\n"
            f"**TMA Pintu Air:** Katulampa `{tel['katulampa_level_cm']} cm` | "
            f"Depok `{tel['depok_level_cm']} cm` | Manggarai `{tel['manggarai_level_cm']} cm`\n"
            f"**Prediksi Genangan:** `{pred['predicted_depth_cm']} cm` "
            f"(Radius `{pred['inundation_radius_km']} km`)\n"
            f"**Estimasi Air Tiba:** `{pred['estimated_arrival_hours']} jam`\n\n"
            f"{result['alert_message']}"
        )
        embed = build_discord_embed(
            title=f"🌊 Laporan Kondisi Banjir — Wilayah {area_id}",
            description=desc,
            siaga_level=ver["siaga_level"],
        )
    except asyncio.TimeoutError:
        embed = build_discord_embed(
            title=f"⏱️ Waktu Proses Habis — Wilayah {area_id}",
            description="Pemrosesan data banjir melewati batas waktu server. Silakan coba beberapa saat lagi.",
            siaga_level="Siaga 4",
        )
    except Exception as e:
        embed = build_discord_embed(
            title=f"⚠️ Gagal Memproses /cekbanjir — Wilayah {area_id}",
            description=f"Terjadi kesalahan saat mengambil atau menghitung data: `{e}`",
            siaga_level="Siaga 4",
        )

    await patch_discord_original_message(application_id, interaction_token, embed)


@router.post("/interactions")
async def discord_interactions(request: Request, background_tasks: BackgroundTasks):
    """Endpoint utama HTTP Webhook untuk Slash Command Discord."""
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    raw_body = await request.body()

    if not verify_discord_signature(signature, timestamp, raw_body):
        raise HTTPException(status_code=401, detail="Invalid request signature")

    payload = json.loads(raw_body)
    interaction_type = payload.get("type")

    # 1. PING dari Discord saat verifikasi URL
    if interaction_type == 1:
        return {"type": 1}

    # 2. APPLICATION_COMMAND (Slash Command)
    if interaction_type == 2:
        data = payload.get("data", {})
        command_name = data.get("name")
        options = {opt["name"]: opt["value"] for opt in data.get("options", [])}

        # /cekbanjir -> pakai deferred response (type 5) agar tidak timeout di Vercel
        if command_name == "cekbanjir":
            raw_area = options.get("area_id")
            area_id = str(raw_area).strip() if raw_area else "31.74.01.1004"
            app_id = str(payload.get("application_id") or DISCORD_APP_ID).strip()
            interaction_token = str(payload.get("token") or "").strip()

            background_tasks.add_task(
                _handle_cekbanjir_followup,
                area_id,
                app_id,
                interaction_token,
            )
            return {"type": 5}

        orchestrator = DiluviumOrchestrator()

        # /statusjakarta
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

        # /pintuair
        if command_name == "pintuair":
            tel = await orchestrator.ingest_telemetry("31.74.01.1004")
            desc = (
                f"• **Bendung Katulampa:** `{tel.katulampa_level_cm} cm`\n"
                f"• **Pos Pantau Depok:** `{tel.depok_level_cm} cm`\n"
                f"• **Pintu Air Manggarai:** `{tel.manggarai_level_cm} cm`\n\n"
                f"_Ambang batas Manggarai: Normal < 750 cm | Siaga 3 ≥ 750 cm | Siaga 2 ≥ 850 cm | Siaga 1 ≥ 950 cm._"
            )
            siaga = (
                "Siaga 1"
                if tel.manggarai_level_cm >= 850
                else ("Siaga 3" if tel.manggarai_level_cm >= 750 else "Siaga 4")
            )
            embed = build_discord_embed(
                title="📏 Tinggi Muka Air (TMA) Hulu–Hilir Ciliwung",
                description=desc,
                siaga_level=siaga,
            )
            return {"type": 4, "data": {"embeds": [embed]}}

    return {"type": 4, "data": {"content": "Perintah tidak dikenali oleh bot Diluvium."}}