from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """
    Pydantic data contract for BMKG weather and rainfall ingestion output
    (Aligned with Section 3.4 Class Diagram in the Project Report).
    """
    adm4_code: str = Field(..., description="Sub-district (Kelurahan/adm4) code in DKI Jakarta")
    kota: str = Field(..., description="Administrative City name in DKI Jakarta")
    kecamatan: str = Field(..., description="District (Kecamatan) name")
    kelurahan: str = Field(..., description="Sub-district (Kelurahan/Desa) name")
    latitude: float = Field(..., description="Latitude coordinate for GeoPandas spatial mapping")
    longitude: float = Field(..., description="Longitude coordinate for GeoPandas spatial mapping")
    precipitation: float = Field(..., ge=0.0, description="Rainfall amount (mm) / BMKG 'tp' parameter")
    temperature: float = Field(..., description="Air temperature (°C) / BMKG 't' parameter")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity (%) / BMKG 'hu' parameter")
    windSpeed: float = Field(..., ge=0.0, description="Wind speed (km/h) / BMKG 'ws' parameter")
    weather_desc: str = Field(..., description="Weather condition description (e.g., Light Rain, Thunderstorm)")
    timestamp: datetime = Field(..., description="Local forecast timestamp (WIB)")
    is_cached: bool = Field(default=False, description="True if loaded from local fallback cache during an API outage")


class JakartaRainfallSummary(BaseModel):
    """Aggregated rainfall summary across all monitored Jakarta locations for the AI Orchestrator."""
    fetched_at: datetime
    total_locations: int
    max_precipitation_mm: float
    highest_risk_area: Optional[str] = None
    records: List[WeatherData]