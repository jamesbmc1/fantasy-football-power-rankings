from unittest.mock import AsyncMock, Mock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


@pytest.fixture
def sleeper():
    fake = Mock()
    fake.get_league_info = AsyncMock(return_value={'league_id':'123456','name':'Test league','season':'2025','sport':'nfl','total_rosters':2,'scoring_settings':{},'settings':{'playoff_week_start':15}})
    fake.get_league_users = AsyncMock(return_value=[{'user_id':'u1','display_name':'User 1'},{'user_id':'u2','display_name':'User 2'}])
    fake.get_league_rosters = AsyncMock(return_value=[{'roster_id':1,'owner_id':'u1'},{'roster_id':2,'owner_id':'u2'}])
    fake.get_nfl_state = AsyncMock(return_value={'season':'2026','season_type':'regular','week':1})
    fake.get_matchups = AsyncMock(return_value=[{'roster_id':1,'points':100.2,'starters':[],'matchup_id':1},{'roster_id':2,'points':100.8,'starters':[],'matchup_id':1}])
    fake.get_weekly_projections = AsyncMock(return_value={})
    with patch('src.app.client', fake):
        yield fake


def test_fetch_rankings_endpoint(sleeper):
    response = client.get('/rankings/123456/1')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]['roster_id'] == 2
    assert 'power_index' in data[0]


def test_fetch_trends_endpoint(sleeper):
    response = client.get('/trends/123456/User 1/1')
    assert response.status_code == 200
    assert response.json()[0]['week'] == 1


def test_fetch_standings_endpoint(sleeper):
    response = client.get('/standings/123456/1/1/2')
    assert response.status_code == 200
    assert response.json()['rivals'][0]['losses'] == 1
    assert set(response.json()) == {'regular','all_play','rivals'}


def test_analytics_and_legacy_routes_agree(sleeper):
    analytics = client.get('/analytics/123456/2').json()
    rankings = client.get('/rankings/123456/2').json()
    trends = client.get('/trends/123456/User 1/2').json()
    standings = client.get('/standings/123456/2/1/2').json()
    assert analytics['rankings'] == rankings
    assert trends[-1]['power_index'] == next(t['power_index'] for t in rankings if t['roster_id'] == 1)
    assert analytics['regular'] == standings['regular']
    assert analytics['through_week'] == 2
    assert analytics['rankings'][0]['rank_change'] == 0


@pytest.mark.parametrize('path', ['/analytics/not-an-id/1','/analytics/123456/0','/analytics/123456/19','/standings/123456/1/1/1'])
def test_invalid_input_is_rejected_before_upstream_requests(sleeper,path):
    assert client.get(path).status_code == 422
    sleeper.get_league_info.assert_not_called()


def test_preseason_never_requests_unplayed_matchups(sleeper):
    sleeper.get_nfl_state.return_value={'season':'2025','season_type':'pre','week':3}
    response=client.get('/analytics/123456/3')
    assert response.status_code == 200
    assert response.json()['rankings'] == []
    assert response.json()['through_week'] is None
    sleeper.get_matchups.assert_not_called()


def test_current_week_clamps_to_completed_week(sleeper):
    sleeper.get_nfl_state.return_value={'season':'2025','season_type':'regular','week':3}
    data=client.get('/analytics/123456/6').json()
    assert data['requested_week'] == 6 and data['through_week'] == 2
    assert sleeper.get_matchups.await_count == 2


def test_projection_failure_does_not_break_scoring_analysis(sleeper):
    sleeper.get_weekly_projections.side_effect=httpx.ReadTimeout('timeout')
    response=client.get('/analytics/123456/1')
    assert response.status_code == 200
    assert all(not t['projections_available'] for t in response.json()['rankings'])


def test_unknown_league_and_upstream_timeout_are_helpful(sleeper):
    sleeper.get_league_info.return_value=None
    assert client.get('/analytics/123456/1').status_code == 404
    sleeper.get_league_info.side_effect=httpx.ReadTimeout('timeout')
    assert client.get('/analytics/123456/1').status_code == 503


def test_unknown_roster_and_duplicate_manager_are_rejected(sleeper):
    assert client.get('/standings/123456/1/1/99').status_code == 404
    assert client.get('/trends/123456/Unknown/1').status_code == 404
    sleeper.get_league_users.return_value[1]['display_name']='User 1'
    assert client.get('/trends/123456/User 1/1').status_code == 409


def test_old_demo_query_cannot_bypass_completed_week_cutoff(sleeper):
    sleeper.get_nfl_state.return_value={'season':'2025','season_type':'pre','week':1}
    response=client.get('/analytics/123456/1?demo=true')
    assert response.status_code == 200
    assert response.json()['rankings'] == []
    assert response.json()['through_week'] is None
    sleeper.get_matchups.assert_not_called()


def test_openapi_has_no_demo_override():
    parameters=client.get('/openapi.json').json()['paths']['/analytics/{league_id}/{week}']['get']['parameters']
    assert {p['name'] for p in parameters} == {'league_id', 'week'}
