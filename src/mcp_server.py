import logging
from fastmcp import FastMCP

# Import Sutan's Ingestion Clients
from src.ingestion.bmkg_client import BMKGClient
from src.ingestion.bpbd_client import BPBDClient

# Import Irgy's Hydrological Calculation Engine & Schemas
from src.calculation.engine import (
    HydrologicalCalculationEngine,
    structure_historical_flood_data,
    PROCESSED_DIR,
)
from src.schemas import CalculationInput

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)
logger = logging.getLogger("Diluvium.MCPServer")

# Initialize the central FastMCP server for Diluvium
mcp = FastMCP("diluvium-mcp-server")

# Ensure processed historical flood CSV exists before initializing calculation engine
if not (PROCESSED_DIR / "structured_flood_history.csv").exists():
    logger.info("Initializing structured historical flood dataset (KAN-19)...")
    structure_historical_flood_data()

# Instantiate shared singleton clients
bmkg_client = BMKGClient()
bpbd_client = BPBDClient()
calc_engine = HydrologicalCalculationEngine()


# ---------------------------------------------------------
# 1. INGESTION TOOLS (Data Terbuka BMKG)
# ---------------------------------------------------------
@mcp.tool()
async def get_specific_area_weather(adm4_code: str = "31.75.03.1001") -> dict:
    """
    Fetches live rainfall telemetry and weather forecasts from BMKG for a specific 
    Jakarta Kelurahan (adm4_code).
    Default '31.75.03.1001' corresponds to Kampung Melayu, Jakarta Timur.
    """
    logger.info(f"LLM Orchestrator requested weather for adm4: {adm4_code}")
    try:
        weather_data = await bmkg_client.fetch_weather_by_adm4(adm4_code)
        return weather_data.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch weather tool: {e}")
        return {"error": str(e), "adm4_code": adm4_code}


@mcp.tool()
async def get_jakarta_flood_watchlist_summary() -> dict:
    """
    Concurrently fetches rainfall data across all monitored flood-prone sub-districts 
    in DKI Jakarta and returns the peak rainfall location.
    """
    logger.info("LLM Orchestrator requested full Jakarta watchlist summary")
    try:
        summary = await bmkg_client.fetch_all_jakarta_watchlist()
        return summary.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch watchlist summary tool: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------
# 2. INGESTION TOOLS (BPBD DKI Jakarta)
# ---------------------------------------------------------
@mcp.tool()
async def get_bpbd_water_levels(gate_name: str = "Manggarai") -> dict:
    """
    Fetches real-time AWLR river water level (cm) and official Siaga status from BPBD DKI Jakarta.
    Available gates: Katulampa, Depok, Manggarai, Karet, Pasar Ikan.
    """
    logger.info(f"LLM Orchestrator requested BPBD water level for: {gate_name}")
    try:
        data = await bpbd_client.fetch_gate_level(gate_name)
        return data.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch BPBD tool: {e}")
        return {"error": str(e), "gate_name": gate_name}


@mcp.tool()
async def get_all_bpbd_floodgates_summary() -> dict:
    """
    Fetches water levels across all primary Jakarta floodgates to identify the most critical river basin.
    """
    logger.info("LLM Orchestrator requested all BPBD floodgates summary")
    try:
        summary = await bpbd_client.fetch_all_primary_gates()
        return summary.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch BPBD summary tool: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------
# 3. CALCULATION TOOLS (Irgy's Hydrological Calculation Engine)
# ---------------------------------------------------------
@mcp.tool()
async def calculate_flood_risk(
    area_id: str = "31.75.03.1001",
    rainfall_rate_mm: float = 42.5,
    katulampa_level_cm: float = 80.0,
    depok_level_cm: float = 180.0,
    manggarai_level_cm: float = 760.0,
) -> dict:
    """
    Runs deterministic and spatial hydrological models (GeoPandas + Jakarta Open Data)
    to estimate flood arrival time (hours), predicted inundation depth (cm),
    inundation radius (km), and statistical confidence score (0.0 - 1.0).
    """
    logger.info(
        f"Running HydrologicalCalculationEngine for {area_id} "
        f"(rain={rainfall_rate_mm}mm, manggarai={manggarai_level_cm}cm)"
    )
    try:
        calc_input = CalculationInput(
            area_id=area_id,
            rainfall_rate_mm=rainfall_rate_mm,
            katulampa_level_cm=katulampa_level_cm,
            depok_level_cm=depok_level_cm,
            manggarai_level_cm=manggarai_level_cm,
        )
        prediction = calc_engine.calculate_hazard(calc_input)
        return prediction.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Calculation engine failed: {e}")
        return {"error": str(e), "area_id": area_id}


# ---------------------------------------------------------
# 4. VERIFICATION & ALERTING TOOLS (Placeholder for Irgy & Radya's Critic/Notifier)
# ---------------------------------------------------------
@mcp.tool()
async def verify_and_dispatch_alert(
    area_id: str,
    predicted_depth_cm: float,
    siaga_level: str
) -> dict:
    """
    Audits predicted flood metrics against Jakarta's Siaga 1-4 thresholds and historical data,
    then dispatches verified alerts to Telegram and Discord.
    """
    # TODO: Connect to src.verification.critic & notifier once completed
    return {
        "verified": True,
        "area_id": area_id,
        "predicted_depth_cm": predicted_depth_cm,
        "siaga_level": siaga_level,
        "dispatched_channels": ["telegram", "discord"],
        "status": "MOCK_DISPATCH_PENDING_INTEGRATION"
    }


if __name__ == "__main__":
    logger.info("Starting Diluvium FastMCP Server...")
    mcp.run()