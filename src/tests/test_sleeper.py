import pytest
from src.api_clients.sleeper import SleeperAPIClient
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.anyio
async def test_get_league_info():
    client = SleeperAPIClient()
    mock_response = {"name": "Test League"}
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        
        mock_get.return_value = mock_resp
        
        result = await client.get_league_info("123456")
        
        assert result == mock_response
        assert mock_get.called

@pytest.mark.anyio
async def test_get_matchups():
    client = SleeperAPIClient()
    mock_response = [{"roster_id": 1, "points": 150}]
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        
        mock_get.return_value = mock_resp
        
        result = await client.get_matchups("123456", 1)
        
        assert result == mock_response
        assert "matchups/1" in mock_get.call_args[0][0]
