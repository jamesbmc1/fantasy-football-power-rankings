import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from src.utils.calculations import (
    calculate_player_score,
    get_projections,
    get_power_rankings
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
def sample_season_df():
    data = {
        "roster_id": [1, 2],
        "owner_id": ["user_1", "user_2"],
        "points": [1200, 1000],
        "all_play_wins": [5, 10],
        "z_score": [1.2, -0.5]
    }

    return pd.DataFrame(data)

@pytest.fixture
def sample_record_df():
    data = {
        "roster_id": [1, 2],
        "wins": [8, 4],
        "losses": [4, 8],
    }

    return pd.DataFrame(data)

@pytest.fixture
def sample_projections_df():
    data = {
        "roster_id": [1, 2],
        "projected_points": [120, 140.42]
    }

    return pd.DataFrame(data)


@pytest.fixture
def get_matchup_response():
    return [
        {
            "roster_id": 1,
            "starters": [101, 102]
        },
        {
            "roster_id": 2,
            "starters": [201]
        }
    ]

@pytest.fixture
def get_projections_response():
    return {
        #QB
        "101": {"pass_td": 2, "pass_yd": 250},
        #WR
        "102": {"rec": 6, "rush_yd": 80, "rush_td": 1},
        #Player on Bye
        "201": {},
        #Not A PlayerID
        "999": None
    }

def test_calculate_player_score(mock_league_scoring):
    #Player data simulating a QB with 2 passing TDs and 250 passing yards
    player_data_1 = {
        "pass_td": 2,
        "pass_yd": 250
    }

    #Bye Week for player
    player_data_2 = {}

    expected_score_1 = (2 * mock_league_scoring["pass_td"]) + (250 * mock_league_scoring["pass_yd"])
    calculated_score_1 = calculate_player_score(player_data_1, mock_league_scoring)

    expected_score_2 = 0
    calculated_score_2 = calculate_player_score(player_data_2, mock_league_scoring)

    assert calculated_score_1 == expected_score_1
    assert calculated_score_2 == expected_score_2
    

def test_get_projections(mock_league_scoring, get_matchup_response, get_projections_response):
    with patch('src.utils.calculations.SleeperAPIClient') as MockClient:
        # Mock Client
        mock_client_instance = MockClient.return_value
        
        mock_client_instance.get_league_info.return_value = {
            "league_id": "test_league",
            "scoring_settings": mock_league_scoring
        }
        mock_client_instance.get_matchups.return_value = get_matchup_response
        mock_client_instance.get_weekly_projections.return_value = get_projections_response

        # Run the function
        df_projections = get_projections(league_id="test_league", week=2, season=2025)

        # Verify the math matches
        expected_data = {
            "roster_id": [1, 2],
            "projected_points": [38.0, 0.0]
        }
        expected_df = pd.DataFrame(expected_data)

        pd.testing.assert_frame_equal(
            df_projections.sort_values('roster_id').reset_index(drop=True),
            expected_df.sort_values('roster_id').reset_index(drop=True)
        )


def test_get_power_rankings(sample_season_df, sample_record_df, sample_projections_df):
    rankings_df = get_power_rankings(
        season_df=sample_season_df,
        record_df=sample_record_df,
        projections_df=sample_projections_df
    )

    expected_cols = ['roster_id', 'owner_id', 'power_ranking_score']
    assert list(rankings_df.columns) == expected_cols

    # The DataFrame must be returned sorted by score (Highest first)
    top_score = rankings_df.iloc[0]['power_ranking_score']
    bottom_score = rankings_df.iloc[-1]['power_ranking_score']
    
    assert top_score >= bottom_score

    assert 0 <= top_score <= 100
    assert 0 <= bottom_score <= 100