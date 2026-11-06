import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

import httpx
from bs4 import BeautifulSoup

import pandas as pd

from src.config import (
    BPBD_CACHE_DIR,
    BPBD_REQUEST_TIMEOUT,
    BPBD_MAX_RETRIES,
    BPBD_BASE_BACKOFF,
    JAKARTA_WATER_GATES,
)
from src.schemas import HydrologicalData, WaterGatesSummary, CalculationInput

logger = logging.getLogger("Diluvium.BPBDClient")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)

class BPBDClient:
    """
    Ingestion Agent client for fetching river water levels and floodgate telemetry
    from BPBD DKI Jakarta using HTML Table Scraping as fallback for undocumented APIs.
    """

    # URL Dashboard Tabel BPBD
    BPBD_DASHBOARD_URL = "https://bpbd.jakarta.go.id/waterlevel"

    def __init__(
        self,
        cache_dir: Path = BPBD_CACHE_DIR,
        max_retries: int = BPBD_MAX_RETRIES,
        base_backoff: float = BPBD_BASE_BACKOFF,
        timeout: float = BPBD_REQUEST_TIMEOUT,
    ):
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

    def _determine_siaga(self, gate_name: str, level_cm: float) -> str:
        """Determines official Siaga 1-4 level based on BPBD threshold standards."""
        cfg = JAKARTA_WATER_GATES.get(gate_name)
        if not cfg:
            return "Normal"

        if level_cm >= cfg["siaga1_min"]:
            return "Siaga 1"
        elif level_cm >= cfg["siaga2_min"]:
            return "Siaga 2"
        elif level_cm >= cfg["siaga3_min"]:
            return "Siaga 3"
        return "Normal"

    def _get_cache_file(self, gate_name: str) -> Path:
        safe_name = gate_name.lower().replace(" ", "_")
        return self.cache_dir / f"bpbd_{safe_name}.json"

    def _save_cache(self, gate_name: str, data: HydrologicalData) -> None:
        try:
            cache_file = self._get_cache_file(gate_name)
            cache_file.write_text(
                json.dumps(data.model_dump(mode="json"), indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Failed to write BPBD cache for {gate_name}: {e}")

    def _load_cache(self, gate_name: str) -> Optional[HydrologicalData]:
        cache_file = self._get_cache_file(gate_name)
        if cache_file.exists():
            try:
                raw = json.loads(cache_file.read_text(encoding="utf-8"))
                raw["is_cached"] = True
                logger.warning(f"Using cached BPBD data for gate: {gate_name}")
                return HydrologicalData(**raw)
            except Exception as e:
                logger.error(f"Corrupted BPBD cache for {gate_name}: {e}")
        return None

    def _clean_level_string(self, raw_str: str) -> float:
        """
        Cleans string like '540 cm (T)' or '10 cm (MT)' into float 540.0
        """
        try:
            # Extract only numbers and optional negative sign (e.g., -160)
            numbers = re.findall(r'-?\d+\.?\d*', str(raw_str))
            if numbers:
                return float(numbers[0])
            return 0.0
        except:
            return 0.0

    def _extract_trend(self, raw_str: str) -> str:
        """
        Extracts trend from the brackets: (T)=STABLE, (N)=RISING, (M)/(MT)=FALLING
        """
        if "(T)" in raw_str:
            return "STABLE"
        elif "(N)" in raw_str:
            return "RISING"
        elif "(M)" in raw_str or "(MT)" in raw_str:
            return "FALLING"
        return "UNKNOWN"

    async def fetch_all_primary_gates(self) -> WaterGatesSummary:
        """
        Fetches the BPBD Dashboard HTML page, parses the table using BeautifulSoup, 
        and extracts water levels for ALL primary gates at once.
        """
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.get(self.BPBD_DASHBOARD_URL)
                    response.raise_for_status()
                    
                    html_content = response.text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find the first table
                    table = soup.find('table')
                    if not table:
                        raise ValueError("No table found on BPBD Dashboard")
                    
                    # Mapping of BPBD HTML table names to our config names
                    name_map = {
                        "Bendung Katulampa": "Katulampa",
                        "Pos Depok": "Depok",
                        "Manggarai BKB": "Manggarai",
                        "PA. Karet": "Karet",
                        "Pasar Ikan - Laut": "Pasar Ikan",
                        "Pos Krukut Hulu": "Krukut Hulu",
                        "Pos Pesanggrahan": "Pesanggrahan",
                        "Pos Angke Hulu": "Angke Hulu",
                        "Waduk Pluit": "Waduk Pluit",
                        "Pos Cipinang Hulu": "Cipinang Hulu",
                        "Pos Sunter Hulu": "Sunter Hulu",
                        "Pulo Gadung": "Pulo Gadung"
                    }

                    parsed_gates = {}
                    
                    # Iterate through table rows
                    for row in table.find_all('tr'):
                        cols = row.find_all('td')
                        if len(cols) > 1: # Make sure it's a data row
                            gate_name_raw = cols[0].text.strip()
                            
                            # Cek jika baris ini ada di target pintu air kita
                            if gate_name_raw in name_map:
                                target_name = name_map[gate_name_raw]
                                
                                # Kolom indeks ke-1 adalah data terbaru (kolom jam saat ini)
                                latest_raw_data = cols[1].text.strip()
                                
                                level_cm = self._clean_level_string(latest_raw_data)
                                trend = self._extract_trend(latest_raw_data)
                                status = self._determine_siaga(target_name, level_cm)
                                
                                river = JAKARTA_WATER_GATES.get(target_name, {}).get("river", "Unknown")
                                
                                gate_data = HydrologicalData(
                                    gate_name=target_name,
                                    river_name=river,
                                    water_level_cm=level_cm,
                                    status_siaga=status,
                                    trend=trend,
                                    timestamp=datetime.now(),
                                    is_cached=False
                                )
                                
                                parsed_gates[target_name] = gate_data
                                self._save_cache(target_name, gate_data)

                    # Jika tabel berhasil di-scrape, buat rekapnya
                    valid_records = list(parsed_gates.values())
                    if not valid_records:
                        raise ValueError("Table parsed but no target floodgates matched.")

                    severity_order = {"Siaga 1": 4, "Siaga 2": 3, "Siaga 3": 2, "Normal": 1}
                    highest_record = max(
                        valid_records,
                        key=lambda r: (severity_order.get(r.status_siaga, 0), r.water_level_cm)
                    )

                    return WaterGatesSummary(
                        fetched_at=datetime.now(),
                        total_gates=len(valid_records),
                        highest_status=highest_record.status_siaga,
                        critical_gate=highest_record.gate_name,
                        records=valid_records
                    )

                except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
                    logger.warning(f"[Retry {attempt}/{self.max_retries}] BPBD scrape error: {exc}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.base_backoff ** attempt)
        
        # JIKA DOWN TOTAL, KEMBALI KE FALLBACK SIMULASI (AMAN UNTUK PRESENTASI)
        logger.error("All scrape attempts failed. Falling back to default simulation levels.")
        valid_records = []
        for gate_name, cfg in JAKARTA_WATER_GATES.items():
            fallback_data = self._load_cache(gate_name)
            if not fallback_data:
                fallback_data = HydrologicalData(
                    gate_name=gate_name,
                    river_name=cfg.get("river", "Sungai Ciliwung"),
                    water_level_cm=float(cfg.get("normal_max", 100)),
                    status_siaga="Normal",
                    trend="STABLE",
                    timestamp=datetime.now(),
                    is_cached=True
                )
                self._save_cache(gate_name, fallback_data)
            valid_records.append(fallback_data)

        return WaterGatesSummary(
            fetched_at=datetime.now(),
            total_gates=len(valid_records),
            highest_status="Normal",
            critical_gate="Manggarai",
            records=valid_records
        )

    async def fetch_gate_level(self, gate_name: str = "Manggarai") -> HydrologicalData:
        """Helper to get a single gate by fetching all and filtering."""
        summary = await self.fetch_all_primary_gates()
        for r in summary.records:
            if r.gate_name == gate_name:
                return r
        # Default fallback
        return await self.fetch_all_primary_gates().records[0]

    async def prepare_calculation_input(self, area_id: str, rainfall_rate_mm: float) -> CalculationInput:
        katulampa = await self.fetch_gate_level("Katulampa")
        depok = await self.fetch_gate_level("Depok")
        manggarai = await self.fetch_gate_level("Manggarai")

        return CalculationInput(
            katulampa_level_cm=katulampa.water_level_cm,
            depok_level_cm=depok.water_level_cm,
            manggarai_level_cm=manggarai.water_level_cm,
            rainfall_rate_mm=rainfall_rate_mm,
            area_id=area_id
        )

if __name__ == "__main__":
    async def main():
        client = BPBDClient()
        print("=== 1. Mengambil Data Scraping Tabel HTML BPBD ===")
        summary = await client.fetch_all_primary_gates()
        
        print(f"Total Pintu Air Terpantau : {summary.total_gates}")
        print(f"Status Kritis Tertinggi   : {summary.highest_status} di {summary.critical_gate}")
        for r in summary.records:
            print(f"- {r.gate_name:<12} | {r.water_level_cm:>6.1f} cm | Trend: {r.trend:<7} | Status: {r.status_siaga:<8} | Cache: {r.is_cached}")

    asyncio.run(main())