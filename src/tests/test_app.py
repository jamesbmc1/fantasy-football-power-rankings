import pytest
from fastapi.testclient import TestClient
from src.app import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

@patch('src.app.fetch_base_league_data', new_callable=AsyncMock)
@patch('src.app.client.get_league_rosters', new_callable=AsyncMock)
@patch('src.app.fetch_projections_up_to_week', new_callable=AsyncMock)
@patch('src.app.fetch_matchups_up_to_week', new_callable=AsyncMock)
def test_fetch_rankings_endpoint(mock_matchups, mock_projections, mock_rosters, mock_base):
    # Setup Mocks
    mock_base.return_value = {
        "league_info": {"season": "2025", "total_rosters": 2, "scoring_settings": {}},
        "users": [{"user_id": "u1", "display_name": "User 1"}, {"user_id": "u2", "display_name": "User 2"}]
    }
    mock_rosters.return_value = [
        {"roster_id": 1, "owner_id": "u1", "settings": {"wins": 1, "losses": 0}},
        {"roster_id": 2, "owner_id": "u2", "settings": {"wins": 0, "losses": 1}}
    ]
    mock_projections.return_value = [{}] # Week 1 projections
    mock_matchups.return_value = [[
        {"roster_id": 1, "points": 100, "starters": [], "matchup_id": 1},
        {"roster_id": 2, "points": 80, "starters": [], "matchup_id": 1}
    ]] # Week 1 matchups
    
    response = client.get("/rankings/123456/1")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Check if we have rankings
    assert "power_index" in data[0]

@patch('src.app.fetch_base_league_data', new_callable=AsyncMock)
@patch('src.app.client.get_league_rosters', new_callable=AsyncMock)
@patch('src.app.fetch_projections_up_to_week', new_callable=AsyncMock)
@patch('src.app.fetch_matchups_up_to_week', new_callable=AsyncMock)
def test_fetch_trends_endpoint(mock_matchups, mock_projections, mock_rosters, mock_base):
    mock_base.return_value = {
        "league_info": {"season": "2025", "total_rosters": 2, "scoring_settings": {}},
        "users": [{"user_id": "u1", "display_name": "User 1"}, {"user_id": "u2", "display_name": "User 2"}]
    }
    mock_rosters.return_value = [
        {"roster_id": 1, "owner_id": "u1", "settings": {"wins": 1, "losses": 0}},
        {"roster_id": 2, "owner_id": "u2", "settings": {"wins": 0, "losses": 1}}
    ]
    mock_projections.return_value = [{}]
    mock_matchups.return_value = [[
        {"roster_id": 1, "points": 100, "starters": [], "matchup_id": 1},
        {"roster_id": 2, "points": 80, "starters": [], "matchup_id": 1}
    ]]
    
    # Trends endpoint: /trends/{league_id}/{target_owner_name}/{week}
    response = client.get("/trends/123456/User 1/1")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["week"] == 1

@patch('src.app.fetch_base_league_data', new_callable=AsyncMock)
@patch('src.app.client.get_league_rosters', new_callable=AsyncMock)
@patch('src.app.fetch_matchups_up_to_week', new_callable=AsyncMock)
def test_fetch_standings_endpoint(mock_matchups, mock_rosters, mock_base):
    mock_base.return_value = {
        "league_info": {"total_rosters": 2},
        "users": [{"user_id": "u1", "display_name": "User 1"}, {"user_id": "u2", "display_name": "User 2"}]
    }
    mock_rosters.return_value = [
        {"roster_id": 1, "owner_id": "u1"},
        {"roster_id": 2, "owner_id": "u2"}
    ]
    mock_matchups.return_value = [[
        {"roster_id": 1, "points": 100, "matchup_id": 1},
        {"roster_id": 2, "points": 80, "matchup_id": 1}
    ]]
    
    # Standings endpoint: /standings/{league_id}/{week}/{user_roster_id}/{target_roster_id}
    response = client.get("/standings/123456/1/1/2")
    
    assert response.status_code == 200
    data = response.json()
    assert "regular" in data
    assert "all_play" in data
    assert "rivals" in data
    assert data["rivals"][0]["wins"] == 1
