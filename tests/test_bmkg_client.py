import pytest
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.ingestion.bmkg_client import BMKGClient
from src.schemas import WeatherData, JakartaRainfallSummary


# Mock response matching BMKG's official nested JSON structure
MOCK_BMKG_PAYLOAD = {
    "lokasi": {
        "adm1": "31",
        "adm2": "31.71",
        "adm3": "31.71.03",
        "adm4": "31.71.03.1001",
        "provinsi": "DKI Jakarta",
        "kotkab": "Kota Adm. Jakarta Pusat",
        "kecamatan": "Kemayoran",
        "desa": "Kemayoran",
        "lat": -6.1647,
        "lon": 106.8481,
    },
    "data": [
        {
            "lokasi": {
                "kotkab": "Kota Adm. Jakarta Pusat",
                "kecamatan": "Kemayoran",
                "desa": "Kemayoran",
                "lat": -6.1647,
                "lon": 106.8481,
            },
            "cuaca": [
                [
                    {
                        "local_datetime": "2026-10-30 14:00:00",
                        "t": 28.5,
                        "hu": 80.0,
                        "weather_desc": "Hujan Sedang",
                        "weather_desc_en": "Moderate Rain",
                        "ws": 10.0,
                        "tp": 18.0,
                    }
                ]
            ],
        }
    ],
}


@pytest.mark.asyncio
async def test_reject_non_jakarta_adm4(tmp_path: Path):
    """Ensure non-Jakarta adm4 codes raise ValueError."""
    client = BMKGClient(cache_dir=tmp_path)
    with pytest.raises(ValueError, match="outside DKI Jakarta"):
        await client.fetch_weather_by_adm4("32.73.01.1001")


@pytest.mark.asyncio
async def test_successful_fetch_and_caching(tmp_path: Path):
    """Verify parsing, Pydantic validation, and local cache write."""
    client = BMKGClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_BMKG_PAYLOAD

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        res = await client.fetch_weather_by_adm4("31.71.03.1001")

    assert isinstance(res, WeatherData)
    assert res.adm4_code == "31.71.03.1001"
    assert res.kelurahan == "Kemayoran"
    assert res.precipitation == 18.0
    assert res.is_cached is False

    cache_file = tmp_path / "bmkg_31_71_03_1001.json"
    assert cache_file.exists()


@pytest.mark.asyncio
async def test_fallback_to_cache_on_outage(tmp_path: Path):
    """Verify fallback to local cache during API downtime."""
    client = BMKGClient(cache_dir=tmp_path, max_retries=1, base_backoff=0.01)

    # 1. Warm cache
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_BMKG_PAYLOAD
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        await client.fetch_weather_by_adm4("31.71.03.1001")

    # 2. Simulate API failure
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("BMKG down")):
        res = await client.fetch_weather_by_adm4("31.71.03.1001")

    assert res.is_cached is True
    assert res.precipitation == 18.0


@pytest.mark.asyncio
async def test_fetch_all_jakarta_watchlist(tmp_path: Path):
    """Verify concurrent watchlist summary calculation across multiple areas."""
    client = BMKGClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_BMKG_PAYLOAD

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        summary = await client.fetch_all_jakarta_watchlist(
            custom_adm4_list=["31.71.03.1001", "31.75.03.1002"]
        )

    assert isinstance(summary, JakartaRainfallSummary)
    assert summary.total_locations == 2
    assert summary.max_precipitation_mm == 18.0