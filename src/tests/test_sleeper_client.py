import asyncio
from unittest.mock import patch

import httpx
import pytest

from src.api_clients.sleeper import SleeperAPIClient
from src.services.analytics import build_snapshot, projection_frame


def test_projection_feed_request_and_index_contribution():
    async def run():
        def respond(request):
            assert str(request.url) == 'https://api.sleeper.com/projections/nfl/2026/1?season_type=regular'
            return httpx.Response(200, json=[
                {'player_id': 'QB1', 'stats': {'pass_yd': 200, 'pass_td': 2}},
                {'player_id': 'QB2', 'stats': {'pass_yd': 100, 'pass_td': 1}},
            ])
        http_client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        with patch('src.api_clients.sleeper.httpx.AsyncClient', return_value=http_client):
            payload = await SleeperAPIClient().get_weekly_projections('2026', 1)
        league = {'league_id': '123', 'season': '2026', 'scoring_settings': {'pass_yd': .04, 'pass_td': 4}}
        matchups = [{'roster_id': i, 'matchup_id': 1, 'points': 100, 'starters': [f'QB{i}']} for i in [1, 2]]
        frame, available = projection_frame(league, matchups, payload)
        assert available
        assert frame.projected_points.tolist() == [16, 8]
        data = build_snapshot(league, [], [{'roster_id': 1}, {'roster_id': 2}], [(1, matchups)], {1: payload}, 1)
        teams = {t['roster_id']: t for t in data['rankings']}
        # Equal actual scores isolate the 15% projection component.
        assert teams[1]['power_index'] == pytest.approx(50 + 1.5 / 2**.5, abs=.0001)
        assert teams[2]['power_index'] == pytest.approx(50 - 1.5 / 2**.5, abs=.0001)
        assert all(t['projections_available'] for t in teams.values())
    asyncio.run(run())


def test_draft_position_only_entries_are_not_zero_point_projections():
    frame, available = projection_frame(
        {'scoring_settings': {'pass_yd': .04}},
        [{'roster_id': 1, 'starters': ['123']}],
        {'123': {'stats': {'adp_dd_ppr': 999}}})
    assert not available
    assert frame.projected_points.tolist() == [0]


@pytest.mark.parametrize('wrong', [False, True])
def test_actual_stats_client_selects_requested_week_and_rejects_projections(wrong):
    async def run():
        def respond(request):
            assert str(request.url) == 'https://api.sleeper.com/stats/nfl/player/9482?season_type=regular&season=2026&grouping=week'
            return httpx.Response(200, json={'1': {'player_id': '9482', 'week': 1, 'season': '2026',
                'season_type': 'regular', 'sport': 'nfl', 'category': 'proj' if wrong else 'stat',
                'stats': {'gp': 1, 'rec': 6, 'rec_yd': 32}}, '2': None})
        http_client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        with patch('src.api_clients.sleeper.httpx.AsyncClient', return_value=http_client):
            if wrong:
                with pytest.raises(ValueError):
                    await SleeperAPIClient().get_player_week_stats('9482', '2026', 1)
            else:
                row = await SleeperAPIClient().get_player_week_stats('9482', '2026', 1)
                assert row['stats']['rec'] == 6
    asyncio.run(run())
