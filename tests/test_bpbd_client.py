import pytest
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.ingestion.bpbd_client import BPBDClient
from src.schemas import HydrologicalData, WaterGatesSummary


MOCK_BPBD_PAYLOAD = [
    {
        "nama_pintu_air": "Manggarai",
        "tinggi_air": 860.0,
        "status": "Siaga 2",
        "trend": "RISING",
        "tanggal": "2026-10-30T15:00:00"
    }
]


@pytest.mark.asyncio
async def test_successful_fetch_bpbd(tmp_path: Path):
    """Verify parsing and caching of BPBD floodgate data."""
    client = BPBDClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_BPBD_PAYLOAD

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        res = await client.fetch_gate_level("Manggarai")

    assert isinstance(res, HydrologicalData)
    assert res.gate_name == "Manggarai"
    assert res.water_level_cm == 860.0
    assert res.status_siaga == "Siaga 2"
    assert res.is_cached is False
    assert (tmp_path / "bpbd_manggarai.json").exists()


@pytest.mark.asyncio
async def test_bpbd_fallback_on_error(tmp_path: Path):
    """Verify fallback when BPBD API is unreachable."""
    client = BPBDClient(cache_dir=tmp_path, max_retries=1, base_backoff=0.01)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("BPBD API down")):
        res = await client.fetch_gate_level("Manggarai")

    assert isinstance(res, HydrologicalData)
    assert res.gate_name == "Manggarai"
    assert res.is_cached is True


@pytest.mark.asyncio
async def test_fetch_all_primary_gates(tmp_path: Path):
    """Verify concurrent fetch of all primary gates."""
    client = BPBDClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_BPBD_PAYLOAD

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        summary = await client.fetch_all_primary_gates()

    assert isinstance(summary, WaterGatesSummary)
    assert summary.total_gates == 5