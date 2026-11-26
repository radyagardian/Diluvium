import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai

# Kontrak skema & mesin kalkulasi yang sudah terintegrasi di repositori
from src.schemas import CalculationInput, HazardPrediction
from src.calculation.engine import HydrologicalCalculationEngine

# Muat environment variables dari .env (GEMINI_API_KEY, GEMINI_MODEL, dll.)
load_dotenv()

# Direktori data lokal
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
BMKG_CACHE_DIR = PROCESSED_DIR / "bmkg_cache"
BPBD_CACHE_DIR = PROCESSED_DIR / "bpbd_cache"


class DiluviumOrchestrator:
    """
    KAN-18: Skrip orkestrasi utama yang menghubungkan:
    1. Ingestion (BMKG & BPBD telemetry cache)
    2. Calculation (HydrologicalCalculationEngine)
    3. Verification (Validasi ambang batas Siaga 1-4 & Notifier)
    4. Gemini Flash API (Sintesis narasi peringatan dini)
    """

    def __init__(self, model_name: Optional[str] = None):
        # Ganti default di bawah dengan ID model yang tadi berhasil di terminalmu
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.calc_engine = HydrologicalCalculationEngine()

    # =========================================================================
    # TAHAP 1: INGESTION (Membaca hasil polling BMKG & BPBD)
    # =========================================================================
    def _read_json_safe(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[INGESTION WARNING] Gagal membaca {file_path.name}: {e}")
            return {}

    def _extract_water_level_cm(self, gate_slug: str, default_cm: float) -> float:
        """Membaca ketinggian air (cm) dari file cache BPBD (misal: bpbd_manggarai.json)."""
        data = self._read_json_safe(BPBD_CACHE_DIR / f"bpbd_{gate_slug}.json")
        for key in ("ketinggian_cm", "water_level_cm", "tinggi_air", "tma", "level"):
            if key in data and data[key] is not None:
                try:
                    return float(data[key])
                except (TypeError, ValueError):
                    pass
        return default_cm

    def _extract_rainfall_mm(self, area_id: str, default_mm: float = 0.0) -> float:
        """Membaca curah hujan (mm/jam) dari file cache BMKG berdasarkan kode adm4."""
        clean_code = area_id.replace(".", "_")
        candidates = [
            BMKG_CACHE_DIR / f"bmkg_{clean_code}.json",
            BASE_DIR / ".cache" / f"bmkg_{clean_code}.json",
        ]
        for path in candidates:
            data = self._read_json_safe(path)
            if not data:
                continue
            for key in ("rainfall_rate_mm", "curah_hujan_mm", "tp", "rainfall"):
                if key in data and data[key] is not None:
                    try:
                        return float(data[key])
                    except (TypeError, ValueError):
                        pass
        return default_mm

    def get_monitored_area_ids(self) -> List[str]:
        """Mengambil seluruh kode adm4 dari file cache BMKG yang tersedia."""
        area_ids = set()
        for folder in (BMKG_CACHE_DIR, BASE_DIR / ".cache"):
            if folder.exists():
                for file_path in folder.glob("bmkg_*.json"):
                    raw_code = file_path.stem.replace("bmkg_", "")
                    area_ids.add(raw_code.replace("_", "."))
        return sorted(area_ids) if area_ids else ["31.74.01.1004"]

    async def ingest_telemetry(self, area_id: str) -> CalculationInput:
        """Mengumpulkan telemetri terbaru dan membungkusnya ke CalculationInput."""
        katulampa_cm = self._extract_water_level_cm("katulampa", default_cm=50.0)
        depok_cm = self._extract_water_level_cm("depok", default_cm=150.0)
        manggarai_cm = self._extract_water_level_cm("manggarai", default_cm=650.0)
        rainfall_mm = self._extract_rainfall_mm(area_id, default_mm=0.0)

        return CalculationInput(
            katulampa_level_cm=katulampa_cm,
            depok_level_cm=depok_cm,
            manggarai_level_cm=manggarai_cm,
            rainfall_rate_mm=rainfall_mm,
            area_id=area_id,
        )

    # =========================================================================
    # TAHAP 2: CALCULATION (Hidrologi & Spasial Deterministik)
    # =========================================================================
    async def run_calculation(self, telemetry: CalculationInput) -> HazardPrediction:
        """Menjalankan Calculation Agent untuk menghitung kedalaman dan onset time."""
        return self.calc_engine.calculate_hazard(telemetry)

    # =========================================================================
    # TAHAP 3: VERIFICATION (Validasi Ambang Batas Siaga 1-4)
    # =========================================================================
    async def verify_prediction(
        self, telemetry: CalculationInput, prediction: HazardPrediction
    ) -> Dict[str, Any]:
        """
        Memvalidasi prediksi agar bebas halusinasi terhadap ambang batas Siaga 1-4 DKI Jakarta.
        Otomatis menggunakan src/verification/critic.py jika sudah diimplementasikan.
        """
        try:
            from src.verification import critic  # type: ignore

            if hasattr(critic, "verify_hazard"):
                return critic.verify_hazard(telemetry, prediction)
        except Exception:
            pass

        depth = prediction.predicted_depth_cm
        manggarai = telemetry.manggarai_level_cm

        if manggarai >= 950 or depth > 150:
            siaga_level = "Siaga 1 (AWAS / Darurat)"
            should_alert = True
        elif manggarai >= 850 or depth >= 75:
            siaga_level = "Siaga 2 (SIAGA)"
            should_alert = True
        elif manggarai >= 750 or depth >= 30:
            siaga_level = "Siaga 3 (WASPADA)"
            should_alert = True
        else:
            siaga_level = "Siaga 4 (NORMAL)"
            should_alert = False

        if prediction.confidence_score < 0.5:
            should_alert = False

        return {
            "is_verified": True,
            "siaga_level": siaga_level,
            "should_alert": should_alert,
            "reason": (
                f"TMA Manggarai {manggarai} cm, prediksi genangan {depth} cm, "
                f"confidence {prediction.confidence_score}."
            ),
        }

    # =========================================================================
    # TAHAP 4: AI SYNTHESIS (Gemini) & DISPATCH NOTIFIKASI
    # =========================================================================
    async def synthesize_alert_message(
        self,
        telemetry: CalculationInput,
        prediction: HazardPrediction,
        verification: Dict[str, Any],
    ) -> str:
        """Menyusun narasi peringatan untuk 1 wilayah menggunakan Gemini."""
        fallback_msg = (
            f"[DILUVIUM EWS - {verification['siaga_level']}]\n"
            f"Wilayah (adm4): {prediction.area_id}\n"
            f"Estimasi Kedalaman: {prediction.predicted_depth_cm} cm\n"
            f"Estimasi Waktu Tiba: {prediction.estimated_arrival_hours} jam\n"
            f"Radius Genangan: {prediction.inundation_radius_km} km\n"
            f"Data Pintu Air: Katulampa {telemetry.katulampa_level_cm} cm | "
            f"Depok {telemetry.depok_level_cm} cm | Manggarai {telemetry.manggarai_level_cm} cm."
        )

        if not self.client:
            print("[ORCHESTRATOR] GEMINI_API_KEY tidak ditemukan, menggunakan template fallback.")
            return fallback_msg

        prompt = f"""
Kamu adalah AI Orchestrator untuk sistem peringatan dini banjir DKI Jakarta (Diluvium).
Buat pesan peringatan singkat, tegas, dan mudah dipahami warga dalam Bahasa Indonesia
HANYA berdasarkan data terverifikasi berikut (jangan mengarang angka baru):

- Status Terverifikasi: {verification['siaga_level']}
- Kode Wilayah (adm4): {prediction.area_id}
- Curah Hujan: {telemetry.rainfall_rate_mm} mm/jam
- Pintu Air Katulampa: {telemetry.katulampa_level_cm} cm
- Pintu Air Depok: {telemetry.depok_level_cm} cm
- Pintu Air Manggarai: {telemetry.manggarai_level_cm} cm
- Prediksi Kedalaman Genangan: {prediction.predicted_depth_cm} cm
- Estimasi Waktu Kedatangan Air: {prediction.estimated_arrival_hours} jam
- Radius Genangan: {prediction.inundation_radius_km} km

Format output: 1 paragraf singkat + 3 poin tindakan mitigasi praktis.
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip() if response.text else fallback_msg
        except Exception as e:
            print(f"[ORCHESTRATOR WARNING] Gemini gagal ({e}), beralih ke pesan fallback.")
            return fallback_msg

    async def synthesize_multi_area_alert(self, affected_results: List[Dict[str, Any]]) -> str:
        """Menyusun 1 pesan peringatan terpadu untuk seluruh wilayah yang terdampak banjir."""
        summary_lines = []
        for item in affected_results:
            pred = item["prediction"]
            ver = item["verification"]
            tel = item["telemetry"]
            summary_lines.append(
                f"- Wilayah {pred['area_id']}: {ver['siaga_level']} | "
                f"Hujan {tel['rainfall_rate_mm']} mm/jam | "
                f"TMA Manggarai {tel['manggarai_level_cm']} cm | "
                f"Estimasi Genangan {pred['predicted_depth_cm']} cm "
                f"(Tiba dalam {pred['estimated_arrival_hours']} jam)"
            )
        joined_summary = "\n".join(summary_lines)

        fallback_msg = (
            f"[DILUVIUM EWS - PERINGATAN MULTI-WILAYAH ({len(affected_results)} Daerah Terdampak)]\n"
            f"{joined_summary}"
        )

        if not self.client:
            print("[ORCHESTRATOR] GEMINI_API_KEY tidak ditemukan, menggunakan template fallback.")
            return fallback_msg

        prompt = f"""
Kamu adalah AI Orchestrator untuk sistem peringatan dini banjir DKI Jakarta (Diluvium).
Terdeteksi potensi banjir pada {len(affected_results)} wilayah secara bersamaan.
Buat 1 pesan peringatan terpadu yang tegas, ringkas, dan jelas dalam Bahasa Indonesia
HANYA berdasarkan daftar data terverifikasi berikut (jangan mengarang angka baru):

{joined_summary}

Format output:
1. Ringkasan daftar wilayah terdampak beserta status Siaga & estimasi kedalaman/waktu tibanya.
2. 3 poin tindakan mitigasi praktis bagi warga di wilayah terdampak.
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip() if response.text else fallback_msg
        except Exception as e:
            print(f"[ORCHESTRATOR WARNING] Gemini gagal ({e}), beralih ke pesan fallback.")
            return fallback_msg

    async def dispatch_notification(self, message: str, should_alert: bool) -> Dict[str, Any]:
        """Mengirim notifikasi melalui src/verification/notifier.py jika sudah tersedia."""
        if not should_alert:
            print("[4/4 NOTIFIER] Status normal (Siaga 4). Notifikasi darurat tidak dikirim.")
            return {"dispatched": False, "channel": "none"}

        try:
            from src.verification import notifier  # type: ignore

            if hasattr(notifier, "send_alert"):
                await notifier.send_alert(message)
                return {"dispatched": True, "channel": "telegram/discord"}
        except Exception:
            pass

        print("[4/4 NOTIFIER] Modul notifier.py belum aktif. Menampilkan pesan ke log:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        return {"dispatched": False, "channel": "console_log"}

    # =========================================================================
    # PIPELINE END-TO-END (Single-Area & Multi-Area)
    # =========================================================================
    async def run_pipeline(
        self,
        area_id: str,
        override_telemetry: Optional[CalculationInput] = None,
    ) -> Dict[str, Any]:
        """Menjalankan alur lengkap untuk 1 wilayah tertentu."""
        print(f"[SINGLE-AREA] Menjalankan pipeline untuk wilayah {area_id}...")
        telemetry = override_telemetry or await self.ingest_telemetry(area_id)
        prediction = await self.run_calculation(telemetry)
        verification = await self.verify_prediction(telemetry, prediction)
        alert_message = await self.synthesize_alert_message(telemetry, prediction, verification)
        delivery = await self.dispatch_notification(alert_message, verification["should_alert"])

        return {
            "telemetry": telemetry.model_dump(),
            "prediction": prediction.model_dump(),
            "verification": verification,
            "alert_message": alert_message,
            "delivery": delivery,
        }

    async def run_all_areas(self) -> Dict[str, Any]:
        """Memindai seluruh wilayah di bmkg_cache dan mengagregasi daerah yang berstatus darurat."""
        area_ids = self.get_monitored_area_ids()
        print(f"[1/4 INGESTION & 2/4 CALCULATION] Memindai {len(area_ids)} wilayah dari bmkg_cache...")

        affected_areas: List[Dict[str, Any]] = []

        for area_id in area_ids:
            telemetry = await self.ingest_telemetry(area_id)
            prediction = await self.run_calculation(telemetry)
            verification = await self.verify_prediction(telemetry, prediction)

            if verification["should_alert"]:
                affected_areas.append(
                    {
                        "telemetry": telemetry.model_dump(),
                        "prediction": prediction.model_dump(),
                        "verification": verification,
                    }
                )

        print(f"[3/4 VERIFICATION] Selesai. Ditemukan {len(affected_areas)} wilayah terdampak.")

        if affected_areas:
            alert_message = await self.synthesize_multi_area_alert(affected_areas)
            delivery = await self.dispatch_notification(alert_message, should_alert=True)
        else:
            alert_message = f"Seluruh {len(area_ids)} wilayah terpantau dalam kondisi normal (Siaga 4)."
            delivery = await self.dispatch_notification(alert_message, should_alert=False)

        return {
            "total_monitored_areas": len(area_ids),
            "affected_count": len(affected_areas),
            "affected_areas": affected_areas,
            "alert_message": alert_message,
            "delivery": delivery,
        }


async def main():
    orchestrator = DiluviumOrchestrator()
    result = await orchestrator.run_all_areas()

    print("\n=== RINGKASAN EKSEKUSI MULTI-WILAYAH (KAN-18) ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())