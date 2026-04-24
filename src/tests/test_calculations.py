import pandas as pd
import pytest

from src.utils.calculations import (
    calculate_player_score,
    get_projections,
    get_power_rankings,
    calculate_season_aggregates,
    process_matchups_data,
    calculate_weekly_regular_standings,
    calculate_all_wins_standings,
    calculate_rival_standings
)

@pytest.fixture
def mock_league_scoring():
    return {
        "pass_td": 4.0,
        "pass_yd": 0.04,
        "rec": 1.0,
        "rush_yd": 0.1,
        "rush_td": 6.0    
    }

@pytest.fixture
def sample_league_data(mock_league_scoring):
    return {
        "scoring_settings": mock_league_scoring,
        "season": "2025",
        "total_rosters": 2
    }

@pytest.fixture
def sample_season_df():
    data = {
        "roster_id": [1, 2],
        "points": [120.0, 100.0],
        "all_play_wins": [1, 0],
        "all_play_losses": [0, 1],
        "z_score": [1.0, -1.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_projections_df():
    data = {
        "roster_id": [1, 2],
        "projected_points": [120.0, 140.0]
    }
    return pd.DataFrame(data)

def test_calculate_player_score(mock_league_scoring):
    player_data = {"pass_td": 2, "pass_yd": 250}
    expected_score = (2 * 4.0) + (250 * 0.04)
    assert calculate_player_score(player_data, mock_league_scoring) == expected_score

def test_get_projections(sample_league_data, mock_league_scoring):
    matchups = [
        {"roster_id": 1, "starters": ["101"]},
        {"roster_id": 2, "starters": ["201"]}
    ]
    weekly_projections = {
        "101": {"stats": {"pass_td": 1, "pass_yd": 200}}, # 4 + 8 = 12
        "201": {"stats": {"rush_td": 1, "rush_yd": 50}}  # 6 + 5 = 11
    }
    df = get_projections(sample_league_data, matchups, weekly_projections)
    assert df.loc[df['roster_id'] == 1, 'projected_points'].values[0] == 12.0
    assert df.loc[df['roster_id'] == 2, 'projected_points'].values[0] == 11.0

def test_get_power_rankings(sample_season_df, sample_projections_df):
    rankings_df = get_power_rankings(sample_season_df, sample_projections_df)
    assert 'power_index' in rankings_df.columns
    assert rankings_df.iloc[0]['rank'] == 1
    assert rankings_df.iloc[0]['roster_id'] == 1

def test_calculate_season_aggregates():
    data = {
        'roster_id': [1, 1, 2, 2],
        'all_play_wins': [1, 1, 0, 0],
        'all_play_losses': [0, 0, 1, 1],
        'z_score': [1.0, 1.0, -1.0, -1.0],
        'points': [100, 110, 80, 90]
    }
    df = pd.DataFrame(data)
    aggs = calculate_season_aggregates(df)
    assert aggs.loc[aggs['roster_id'] == 1, 'points'].values[0] == 210
    assert aggs.loc[aggs['roster_id'] == 2, 'all_play_wins'].values[0] == 0

def test_process_matchups_data():
    matchup_wk1 = [
        {'roster_id': 1, 'points': 100},
        {'roster_id': 2, 'points': 120}
    ]
    
    df = pd.DataFrame(matchup_wk1).assign(week=1)

    df['matchup_id'] = 1
    processed = process_matchups_data([df], 2)
    assert 'all_play_wins' in processed.columns
    assert processed.loc[processed['roster_id'] == 2, 'all_play_wins'].values[0] == 1

def test_calculate_weekly_regular_standings():
    data = {
        'week': [1, 1, 2, 2],
        'matchup_id': [1, 1, 1, 1],
        'roster_id': [1, 2, 1, 2],
        'points': [100, 120, 110, 90]
    }
    df = pd.DataFrame(data)
    standings = calculate_weekly_regular_standings(df)
    assert standings.loc[standings['roster_id'] == 1, 'wins'].values[0] == 1
    assert standings.loc[standings['roster_id'] == 1, 'points'].values[0] == 210

def test_calculate_all_wins_standings():
    data = {
        'roster_id': [1, 2],
        'all_play_wins': [5, 3],
        'all_play_losses': [2, 4]
    }
    df = pd.DataFrame(data)
    standings = calculate_all_wins_standings(df)
    assert standings.iloc[0]['roster_id'] == 1
    assert standings.iloc[0]['win_pct'] == round(5/7, 4)

def test_calculate_rival_standings():
    data = {
        'week': [1, 1, 2, 2],
        'roster_id': [1, 2, 1, 2],
        'points': [100, 120, 110, 90]
    }
    df = pd.DataFrame(data)
    rival_standings = calculate_rival_standings(df, 1, 2)
    assert rival_standings.iloc[0]['wins'] == 1
    assert rival_standings.iloc[0]['losses'] == 1
    assert rival_standings.iloc[0]['points_user'] == 210
    assert rival_standings.iloc[0]['points_rival'] == 210
