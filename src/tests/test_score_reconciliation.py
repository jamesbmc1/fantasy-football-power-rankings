import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock

import httpx
import pytest

from src.services.score_reconciliation import reconcile_matchups, score_actual_stats, UnresolvedScore
from src.services.analytics import build_snapshot

LEAGUE = {'league_id': '123', 'season': '2026', 'scoring_settings': {
    'rec': 1, 'rec_yd': .1, 'rec_td': 6, 'bonus_rec_yd_100': 3}}


def matchup():
    return {'roster_id': 10, 'matchup_id': 1, 'points': 108.86,
            'starters': ['known', '9482'], 'starters_points': [108.86, 0],
            'players_points': {'known': 108.86}, 'custom_points': None}


def repair(rows, client=None, week=1):
    client = client or AsyncMock()
    client.get_player_week_stats.return_value = {'stats': {'gp': 1, 'rec': 6, 'rec_yd': 32}}
    return asyncio.run(reconcile_matchups(client, LEAGUE, week, rows))


def test_missing_starter_recovers_exact_mayer_points_without_mutating_upstream():
    original = matchup()
    before = deepcopy(original)
    client = AsyncMock()
    rows, notes = repair([original], client)
    assert rows[0]['points'] == 118.06
    assert original == before
    client.get_player_week_stats.assert_awaited_once_with('9482', '2026', 1)
    assert '118.06' in notes[0] and '9482' in notes[0]


@pytest.mark.parametrize('override', [0, 125.5])
def test_commissioner_overrides_are_authoritative(override):
    row = matchup(); row['custom_points'] = override
    client = AsyncMock()
    rows, notes = repair([row], client)
    assert rows[0]['custom_points'] == override and rows[0]['points'] == 108.86
    assert notes == []
    client.get_player_week_stats.assert_not_called()


def test_existing_zero_is_not_a_missing_score():
    row = matchup(); row['players_points']['9482'] = 0
    client = AsyncMock()
    rows, notes = repair([row], client)
    assert rows[0]['points'] == 108.86 and notes == []
    client.get_player_week_stats.assert_not_called()


def test_corrected_upstream_total_is_not_double_counted():
    row = matchup(); row['points'] = 118.06; row['players_points']['9482'] = 9.2
    client = AsyncMock()
    rows, notes = repair([row], client)
    assert rows[0]['points'] == 118.06 and notes == []
    client.get_player_week_stats.assert_not_called()


def test_changed_lineup_uses_selected_players_not_old_total_or_bench():
    row = matchup(); row['players_points'].update({'9482': 9.2, 'bench': 50})
    client = AsyncMock()
    rows, notes = repair([row], client)
    assert rows[0]['points'] == 118.06 and notes
    client.get_player_week_stats.assert_not_called()


def test_empty_slots_and_negative_scores_are_valid():
    row = matchup(); row.update(starters=['known', '0'], points=-2, players_points={'known': -2})
    rows, notes = repair([row])
    assert rows[0]['points'] == -2 and notes == []


@pytest.mark.parametrize('stats', [None, {}, {'gp': 0}, {'gp': 1, 'rec': float('nan')},
                                  {'gp': 1, 'rec': 6, 'rec_yd': 132}])
def test_unavailable_or_ambiguous_actual_stats_stop_the_week(stats):
    client = AsyncMock(); client.get_player_week_stats.return_value = {'stats': stats}
    rows, notes = asyncio.run(reconcile_matchups(client, LEAGUE, 1, [matchup()]))
    assert rows[0]['points'] is None and 'could not be reconciled' in notes[0]


def test_timeout_does_not_publish_stale_score():
    client = AsyncMock(); client.get_player_week_stats.side_effect = httpx.ReadTimeout('timeout')
    rows, notes = asyncio.run(reconcile_matchups(client, LEAGUE, 1, [matchup()]))
    assert rows[0]['points'] is None and notes


def test_known_bonus_and_kicking_aggregate_are_scored():
    assert score_actual_stats({'gp': 1, 'rec': 6, 'rec_yd': 132, 'bonus_rec_yd_100': 1}, LEAGUE['scoring_settings']) == pytest.approx(22.2)
    assert score_actual_stats({'gp': 1, 'fga': 3, 'fgm': 2}, {'fgmiss': -1}) == -1
    with pytest.raises(UnresolvedScore):
        score_actual_stats({'gp': 1, 'fgm': 2, 'fgm_20_29': 1}, {'fgm_50_59': 5})


def test_repaired_score_flows_into_all_analytics_and_unresolved_week_stops_history():
    opponent = {'roster_id': 2, 'matchup_id': 1, 'points': 116, 'starters': ['other'], 'players_points': {'other': 116}}
    rows, notes = repair([matchup(), opponent])
    data = build_snapshot(LEAGUE, [], [{'roster_id': 10}, {'roster_id': 2}], [(1, rows)], {}, 1, notes)
    own = lambda key: next(t for t in data[key] if t['roster_id'] == 10)
    assert own('regular')['wins'] == 1
    assert own('regular')['points'] == own('weekly_scores')['points'] == own('history')['points'] == 118.06
    assert own('all_play')['all_play_wins'] == 1
    assert own('schedule')['expected_wins'] == 1
    assert own('rankings')['rank'] == 1
    broken = deepcopy(rows); broken[0]['points'] = None
    later = build_snapshot(LEAGUE, [], [{'roster_id': 10}, {'roster_id': 2}], [(1, rows), (2, broken)], {}, 2)
    assert later['through_week'] == 1
    assert len(later['history']) == 2


def test_sparse_defense_bands_score_only_applicable_categories():
    settings = {'sack': 1, 'pts_allow_0': 5, 'pts_allow_14_20': 1,
                'pts_allow_28_34': -1, 'yds_allow_0_100': 5,
                'yds_allow_200_299': 2, 'yds_allow_350_399': -1}
    stats = {'gp': 1, 'sack': 4, 'pts_allow': 17, 'pts_allow_14_20': 1,
             'yds_allow': 285, 'yds_allow_200_299': 1}
    assert score_actual_stats(stats, settings) == 7


def test_valid_defense_band_need_not_be_scored_by_league():
    stats = {'gp': 1, 'pts_allow': 30, 'pts_allow_28_34': 1,
             'yds_allow': 329, 'yds_allow_300_349': 1}
    assert score_actual_stats(stats, {'pts_allow_0': 5, 'yds_allow_200_299': 2}) == 0


@pytest.mark.parametrize('bands', [{}, {'pts_allow_14_20': 0},
    {'pts_allow_14_20': 1, 'pts_allow_7_13': 1}, {'pts_allow_14_20': float('nan')}])
def test_incomplete_or_invalid_defense_bands_still_fail_closed(bands):
    with pytest.raises(UnresolvedScore):
        score_actual_stats({'gp': 1, 'pts_allow': 17, **bands}, {'pts_allow_0': 5})


def test_week_two_defense_recovery_does_not_block_analysis():
    client = AsyncMock()
    client.get_player_week_stats.return_value = {'stats': {'gp': 1, 'sack': 4,
        'pts_allow': 17, 'pts_allow_14_20': 1, 'yds_allow': 285, 'yds_allow_200_299': 1}}
    league = {**LEAGUE, 'scoring_settings': {'sack': 1, 'pts_allow_0': 5,
              'pts_allow_14_20': 1, 'yds_allow_200_299': 2, 'yds_allow_350_399': -1}}
    row = {**matchup(), 'starters': ['known', 'GB']}
    rows, notes = asyncio.run(reconcile_matchups(client, league, 2, [row]))
    assert rows[0]['points'] == 115.86
    assert 'Rebuilt' in notes[0]
