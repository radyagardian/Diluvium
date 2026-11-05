import logging
from fastmcp import FastMCP
from pydantic import BaseModel

# Import BMKG Ingestion Client
from src.ingestion.bmkg_client import BMKGClient

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("Diluvium.MCPServer")

# Initialize central FastMCP server for Diluvium
mcp = FastMCP("diluvium-mcp-server")

# Instantiate the BMKG client
bmkg_client = BMKGClient()

# 1. INGESTION TOOLS (Data Terbuka BMKG)
# ---------------------------------------------------------
@mcp.tool()
async def get_specific_area_weather(adm4_code: str = "31.75.03.1001") -> dict:
    """
    Fetches live rainfall telemetry and weather forecasts from BMKG for a specific 
    Jakarta Kelurahan (adm4_code).
    Default '31.75.03.1001' corresponds to Kampung Melayu, Jakarta Timur.
    
    Use this tool when you need exact precipitation (mm), temperature, or humidity 
    for a localized risk assessment.
    """
    logger.info(f"LLM Orchestrator requested weather for adm4: {adm4_code}")
    try:
        weather_data = await bmkg_client.fetch_weather_by_adm4(adm4_code)
        # Convert to dictionary so the LLM can easily read the JSON structure
        return weather_data.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch weather tool: {e}")
        return {"error": str(e), "adm4_code": adm4_code}

    def __init__(
        self,
        cache_dir: Path = BMKG_CACHE_DIR,
        max_retries: int = BMKG_MAX_RETRIES,
        base_backoff: float = BMKG_BASE_BACKOFF,
        timeout: float = BMKG_REQUEST_TIMEOUT,
    ):
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(BMKG_MAX_CONCURRENT_REQUESTS)
        # User-Agent header complying with government API Terms of Service (Section 2.3.4)
        self.headers = {
            "User-Agent": "Diluvium-EWS/1.0 (Universitas Indonesia; Electrical Engineering Project)",
            "Accept": "application/json",
        }

# 2. CALCULATION TOOLS (Placeholder for Irgy's GeoPandas / ML work)
# ---------------------------------------------------------
@mcp.tool()
async def calculate_flood_risk(precipitation_mm: float, water_level_cm: float, area_id: str) -> dict:
    """
    Runs deterministic and ML hydrological models to estimate flood arrival time,
    expected depth (cm), and inundation radius (km).
    """
    # TODO: Import and call Irgy's engine from src.calculation.engine once merged
    return {
        "area_id": area_id,
        "estimated_arrival_hours": 2.5,
        "predicted_depth_cm": 85.0,
        "inundation_radius_km": 1.4,
        "confidence_score": 0.89,
        "status": "MOCK_DATA_PENDING_INTEGRATION"
    }

# 3. VERIFICATION & ALERTING TOOLS (Placeholder for Irgy's Telegram Webhooks)
# ---------------------------------------------------------
@mcp.tool()
async def verify_and_dispatch_alert(area_id: str, predicted_depth_cm: float, siaga_level: str) -> dict:
    """
    Audits predicted flood metrics against Jakarta's Siaga 1-4 thresholds and historical data,
    then dispatches verified alerts to Telegram and Discord.
    """
    # TODO: Import and call Irgy's verifier from src.verification.critic once merged
    return {
        "verified": True,
        "siaga_level": siaga_level,
        "dispatched_channels": ["telegram", "discord"],
        "status": "MOCK_DISPATCH_PENDING_INTEGRATION"
    }

    def _save_cache(self, adm4_code: str, data: WeatherData) -> None:
        """Saves the latest valid weather telemetry to disk for offline fallback."""
        try:
            cache_file = self._get_cache_file(adm4_code)
            cache_file.write_text(
                json.dumps(data.model_dump(mode="json"), indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Failed to write local cache for {adm4_code}: {e}")

    def _load_cache(self, adm4_code: str) -> Optional[WeatherData]:
        """Loads the last known weather telemetry from disk if the BMKG API is unreachable."""
        cache_file = self._get_cache_file(adm4_code)
        if cache_file.exists():
            try:
                raw = json.loads(cache_file.read_text(encoding="utf-8"))
                raw["is_cached"] = True
                logger.warning(f"Using cached fallback data for {adm4_code}")
                return WeatherData(**raw)
            except Exception as e:
                logger.error(f"Corrupted cache file for {adm4_code}: {e}")
        return None

    def _parse_bmkg_response(self, payload: Dict[str, Any], adm4_code: str) -> WeatherData:
        """
        Extracts the nearest forecast time slot from BMKG's nested JSON structure
        and applies safe default imputation for missing values (Risk Mitigation 1.7.e).
        """
        lokasi = payload.get("lokasi", {})
        data_list = payload.get("data", [])

        if not data_list or not data_list[0].get("cuaca"):
            raise ValueError(f"Empty 'cuaca' forecast array in BMKG response for adm4={adm4_code}")

        # Extract administrative location metadata and spatial coordinates
        loc_detail = data_list[0].get("lokasi", lokasi)
        kota = str(loc_detail.get("kotkab", "DKI Jakarta"))
        kecamatan = str(loc_detail.get("kecamatan", "Unknown"))
        kelurahan = str(loc_detail.get("desa", "Unknown"))
        lat = float(loc_detail.get("lat", -6.2088) or -6.2088)
        lon = float(loc_detail.get("lon", 106.8456) or 106.8456)

        # Flatten the 2D 'cuaca' array (grouped by day -> 3-hour intervals) into a 1D list
        cuaca_2d = data_list[0]["cuaca"]
        all_forecasts = [slot for day in cuaca_2d for slot in day if isinstance(slot, dict)]

        if not all_forecasts:
            raise ValueError(f"No valid forecast time slots found for adm4={adm4_code}")

        # Select the forecast slot closest to current local time
        now = datetime.now()
        selected_slot = all_forecasts[0]
        min_diff = float("inf")

        for slot in all_forecasts:
            dt_str = slot.get("local_datetime")
            if dt_str:
                try:
                    slot_dt = datetime.fromisoformat(dt_str)
                    diff = abs((slot_dt - now).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        selected_slot = slot
                except ValueError:
                    continue

        # Extract weather metrics with safe fallback imputation:
        # tp = Total Precipitation (mm), t = Temperature (°C),
        # hu = Humidity (%), ws = Wind Speed (km/h)
        precipitation = float(selected_slot.get("tp", 0.0) or 0.0)
        temperature = float(selected_slot.get("t", 28.0) or 28.0)
        humidity = float(selected_slot.get("hu", 75.0) or 75.0)
        wind_speed = float(selected_slot.get("ws", 5.0) or 5.0)
        weather_desc = str(
            selected_slot.get("weather_desc_en")
            or selected_slot.get("weather_desc")
            or "Cloudy"
        )

        local_dt_str = selected_slot.get("local_datetime")
        timestamp = datetime.fromisoformat(local_dt_str) if local_dt_str else now

        return WeatherData(
            adm4_code=adm4_code,
            kota=kota,
            kecamatan=kecamatan,
            kelurahan=kelurahan,
            latitude=lat,
            longitude=lon,
            precipitation=precipitation,
            temperature=temperature,
            humidity=humidity,
            windSpeed=wind_speed,
            weather_desc=weather_desc,
            timestamp=timestamp,
            is_cached=False,
        )

    async def fetch_weather_by_adm4(self, adm4_code: str) -> WeatherData:
        """
        Fetches weather telemetry for a single DKI Jakarta sub-district (adm4)
        with Exponential Backoff Retry and Local Cache Fallback.
        """
        self._validate_jakarta_adm4(adm4_code)

        async with self.semaphore:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                for attempt in range(1, self.max_retries + 1):
                    try:
                        response = await client.get(
                            BMKG_API_BASE_URL,
                            params={"adm4": adm4_code}
                        )

                        # Trigger retry on Rate Limit (429) or Server Errors (5xx)
                        if response.status_code == 429 or response.status_code >= 500:
                            raise httpx.HTTPStatusError(
                                f"Server/RateLimit Error (HTTP {response.status_code})",
                                request=response.request,
                                response=response,
                            )

                        response.raise_for_status()
                        payload = response.json()

                        weather_data = self._parse_bmkg_response(payload, adm4_code)
                        self._save_cache(adm4_code, weather_data)
                        logger.info(
                            f"[OK] {weather_data.kelurahan} ({adm4_code}) | "
                            f"Rain: {weather_data.precipitation} mm | Condition: {weather_data.weather_desc}"
                        )
                        return weather_data

                    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
                        logger.warning(
                            f"[Retry {attempt}/{self.max_retries}] Failed querying BMKG ({adm4_code}): {exc}"
                        )
                        if attempt < self.max_retries:
                            sleep_sec = self.base_backoff ** attempt
                            await asyncio.sleep(sleep_sec)

        # Fallback to local cache if all retry attempts fail
        cached = self._load_cache(adm4_code)
        if cached:
            return cached

        raise RuntimeError(f"Failed to fetch BMKG data for {adm4_code} and no local cache is available.")

    async def fetch_all_jakarta_watchlist(
        self, custom_adm4_list: Optional[List[str]] = None
    ) -> JakartaRainfallSummary:
        """
        Concurrently fetches rainfall data across all flood-prone sub-districts in DKI Jakarta
        and summarizes the highest-risk area.
        """
        target_codes = custom_adm4_list or list(JAKARTA_FLOOD_PRONE_ADM4.keys())

        tasks = [self.fetch_weather_by_adm4(code) for code in target_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_records: List[WeatherData] = []
        for code, res in zip(target_codes, results):
            if isinstance(res, WeatherData):
                valid_records.append(res)
            else:
                logger.error(f"Skipping region {code} due to error: {res}")

        if not valid_records:
            raise RuntimeError("Failed to retrieve weather telemetry for any Jakarta region.")

        highest_record = max(valid_records, key=lambda r: r.precipitation)

        return JakartaRainfallSummary(
            fetched_at=datetime.now(),
            total_locations=len(valid_records),
            max_precipitation_mm=highest_record.precipitation,
            highest_risk_area=f"{highest_record.kelurahan}, {highest_record.kecamatan} ({highest_record.kota})",
            records=valid_records,
        )


# =========================================================
# CLI Execution / General Jakarta Test:
# python -m src.ingestion.bmkg_client
# =========================================================
if __name__ == "__main__":
    async def run_test():
        client = BMKGClient()

        print("=== Running General DKI Jakarta Weather Ingestion Test ===")
        summary = await client.fetch_all_jakarta_watchlist()

        print("\n" + "=" * 65)
        print(f"Total Monitored Areas    : {summary.total_locations} sub-districts")
        print(f"Peak Precipitation       : {summary.max_precipitation_mm} mm")
        print(f"Highest Risk Area (Peak) : {summary.highest_risk_area}")
        print("=" * 65)

        print("\nRegional Summary:")
        for record in summary.records:
            print(f"- [{record.kota}] {record.kelurahan} ({record.adm4_code}): "
                  f"Rain: {record.precipitation} mm | "
                  f"Condition: {record.weather_desc} | "
                  f"Temp: {record.temperature}°C | "
                  f"Cached: {record.is_cached}")

    asyncio.run(run_test())
