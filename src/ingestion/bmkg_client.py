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

@mcp.tool()
async def get_jakarta_flood_watchlist_summary() -> dict:
    """
    Concurrently fetches rainfall data across ALL monitored flood-prone sub-districts 
    in DKI Jakarta. 
    
    Use this tool to get a macro-level view of Jakarta's weather and to identify 
    the 'highest_risk_area' with the peak precipitation before drilling down into specific areas.
    """
    logger.info("LLM Orchestrator requested full Jakarta watchlist summary")
    try:
        summary = await bmkg_client.fetch_all_jakarta_watchlist()
        return summary.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Failed to fetch watchlist summary tool: {e}")
        return {"error": str(e)}

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

if __name__ == "__main__":
    logger.info("Starting Diluvium FastMCP Server...")
    # Runs the server using standard input/output (stdio), which is how the Gemini orchestrator script will communicate with it locally.
    mcp.run()