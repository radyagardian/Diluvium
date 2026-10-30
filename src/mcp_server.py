import logging
from fastmcp import FastMCP

from src.ingestion.bmkg_client import BMKGClient

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)
logger = logging.getLogger("Diluvium.MCPServer")

# Initialize the central FastMCP server for Diluvium
mcp = FastMCP("diluvium-mcp-server")

# Instantiate BMKG Client
bmkg_client = BMKGClient()


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


# 2. INGESTION TOOLS (BPBD DKI Jakarta - Pending BPBD Client Integration)
# ---------------------------------------------------------
@mcp.tool()
async def get_bpbd_water_levels(gate_name: str = "Manggarai") -> dict:
    """
    Fetches real-time AWLR river water level (cm) and official Siaga status from BPBD DKI Jakarta.
    """
    # TODO: Connect to src.ingestion.bpbd_client once completed
    return {
        "gate_name": gate_name,
        "water_level_cm": 760.0,
        "official_status": "Siaga 3",
        "status": "MOCK_DATA_PENDING_INTEGRATION"
    }


# 3. CALCULATION TOOLS (Placeholder for Irgy's GeoPandas / ML work)
# ---------------------------------------------------------
@mcp.tool()
async def calculate_flood_risk(precipitation_mm: float, water_level_cm: float, area_id: str) -> dict:
    """
    Runs deterministic and ML hydrological models to estimate flood arrival time,
    expected depth (cm), and inundation radius (km).
    """
    # TODO: Connect to src.calculation.engine once completed
    return {
        "area_id": area_id,
        "estimated_arrival_hours": 2.5,
        "predicted_depth_cm": 85.0,
        "inundation_radius_km": 1.4,
        "confidence_score": 0.89,
        "status": "MOCK_DATA_PENDING_INTEGRATION"
    }


# 4. VERIFICATION & ALERTING TOOLS (Placeholder for Irgy & Radya's Critic/Notifier)
# ---------------------------------------------------------
@mcp.tool()
async def verify_and_dispatch_alert(area_id: str, predicted_depth_cm: float, siaga_level: str) -> dict:
    """
    Audits predicted flood metrics against Jakarta's Siaga 1-4 thresholds and historical data,
    then dispatches verified alerts to Telegram and Discord.
    """
    # TODO: Connect to src.verification.critic & notifier once completed
    return {
        "verified": True,
        "siaga_level": siaga_level,
        "dispatched_channels": ["telegram", "discord"],
        "status": "MOCK_DISPATCH_PENDING_INTEGRATION"
    }


if __name__ == "__main__":
    logger.info("Starting Diluvium FastMCP Server...")
    mcp.run()