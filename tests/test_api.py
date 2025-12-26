"""Test API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from custom_components.pihole_device_tracker.api import PiholeAPIClient


@pytest.fixture
def client():
    """Create API client for testing."""
    return PiholeAPIClient(host="192.168.1.100", api_key="test_key")


@pytest.mark.asyncio
async def test_get_devices_success(client):
    """Test successful device retrieval."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "clients": [
                    {"mac": "00:11:22:33:44:55", "name": "Device1", "ip": "192.168.1.10"}
                ]
            }
        )
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await client.async_get_devices()
        assert "clients" in result


@pytest.mark.asyncio
async def test_connection_failed(client):
    """Test connection failure."""
    result = await client.async_test_connection()
    assert not result
