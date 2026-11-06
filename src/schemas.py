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

class CalculationInput(BaseModel):
    """
    Input contract for the Hydrological Calculation Engine.
    """
    katulampa_level_cm: float = Field(..., ge=0.0, description="Water level at Katulampa gate (cm)")
    depok_level_cm: float = Field(..., ge=0.0, description="Water level at Depok gate (cm)")
    manggarai_level_cm: float = Field(..., ge=0.0, description="Water level at Manggarai gate (cm)")
    rainfall_rate_mm: float = Field(..., ge=0.0, description="Current rainfall rate in the target area (mm)")
    area_id: str = Field(..., description="Target Kelurahan (adm4) code")

class HazardPrediction(BaseModel):
    """
    Output contract for the Calculation Agent's spatial and temporal predictions.
    """
    area_id: str = Field(..., description="Target Kelurahan (adm4) code")
    estimated_arrival_hours: float = Field(..., ge=0.0, description="Estimated time until flood arrival (hours)")
    predicted_depth_cm: float = Field(..., ge=0.0, description="Predicted maximum inundation depth (cm)")
    inundation_radius_km: float = Field(..., ge=0.0, description="Estimated geographic spread radius (km)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Statistical confidence score of the prediction")

class HydrologicalData(BaseModel):
    """
    Pydantic data contract for BPBD DKI water level telemetry
    (Aligned with Section 3.4 Class Diagram in the Project Report).
    """
    gate_name: str = Field(..., description="Name of the water gate / AWLR station")
    river_name: str = Field(..., description="Name of the river basin")
    water_level_cm: float = Field(..., description="Current water level in centimeters")
    status_siaga: str = Field(..., description="Official status: Normal, Siaga 3, Siaga 2, Siaga 1")
    trend: str = Field(default="STABLE", description="Water level trend: RISING, FALLING, or STABLE")
    timestamp: datetime = Field(..., description="Observation timestamp")
    is_cached: bool = Field(default=False, description="True if loaded from local cache fallback")


class WaterGatesSummary(BaseModel):
    """Aggregated water level summary across primary Jakarta floodgates."""
    fetched_at: datetime
    total_gates: int
    highest_status: str
    critical_gate: Optional[str] = None
    records: List[HydrologicalData]