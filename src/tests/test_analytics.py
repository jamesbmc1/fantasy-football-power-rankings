"""Analytical invariants and hand-computed examples, not implementation mirrors."""
import math
import random
import pandas as pd
import pytest
from src.services.analytics import build_snapshot, completed_week_limit, projection_frame
from src.utils.calculations import process_matchups_data, calculate_schedule_advantage, calculate_weekly_regular_standings, calculate_all_wins_standings


def example(scores, pairs=None):
    pairs = pairs or [1, 1, 2, 2]
    return [dict(roster_id=i+1, matchup_id=pairs[i], points=p, starters=[str(i+1)]) for i,p in enumerate(scores)]


def snapshot(weeks=None, projections=None):
    weeks = weeks or [(1, example([100.2, 100.8, 90, 110])), (2, example([110, 90, 100, 100]))]
    return build_snapshot({'league_id':'123', 'season':'2025','name':'Test', 'scoring_settings':{'pts':1}},
                          [{'user_id':str(i),'display_name':f'Team {i}'} for i in range(1,5)],
                          [{'roster_id':i,'owner_id':str(i)} for i in range(1,5)], weeks, projections or {}, weeks[-1][0])


def test_expected_wins_hand_calculated_with_ties_and_fractional_scores():
    data = snapshot()
    teams = {t['roster_id']: t for t in data['schedule']}
    # Team 1: week one beats 90 only (1/3); week two beats everyone (1).
    assert teams[1]['expected_wins'] == pytest.approx(4/3)
    assert teams[1]['actual_wins'] == 1
    assert teams[1]['schedule_advantage'] == pytest.approx(-1/3)
    # Team 3: zero in week one; beats 90 and ties 100 in week two (1.5/3).
    assert teams[3]['expected_wins'] == .5
    assert teams[3]['actual_wins'] == .5
    assert teams[3]['schedule_advantage'] == 0
    assert sum(t['schedule_advantage'] for t in teams.values()) == pytest.approx(0)


def test_byes_do_not_create_actual_or_expected_games():
    week = pd.DataFrame(example([100, 90, 130, 120], [1, 1, None, None])).assign(week=1)
    season = process_matchups_data([week], 4)
    result = calculate_schedule_advantage(season).set_index('roster_id')
    assert result.loc[3, 'games'] == result.loc[4, 'games'] == 0
    assert result.loc[3, 'expected_wins'] == 0
    assert result.loc[1, 'expected_wins'] == pytest.approx(1/3)
    assert calculate_weekly_regular_standings(season)['wins'].sum() == 1


def test_commissioner_override_including_zero_used_in_every_view():
    week = example([100, 90, 80, 70])
    week[0]['custom_points'] = 0
    data = snapshot([(1, week)])
    assert next(t for t in data['weekly_scores'] if t['roster_id'] == 1)['points'] == 0
    assert next(t for t in data['schedule'] if t['roster_id'] == 1)['losses'] == 1
    assert next(t for t in data['rankings'] if t['roster_id'] == 1)['rank'] == 4


def test_equal_scores_share_rank_and_never_create_nan():
    data = snapshot([(1, example([100,100,100,100]))])
    assert [t['rank'] for t in data['rankings']] == [1]*4
    assert [t['power_index'] for t in data['rankings']] == [50]*4
    assert all(t['rank_change'] is None for t in data['rankings'])
    assert all(t['expected_wins'] == .5 for t in data['schedule'])
    assert all(t['schedule_advantage'] == 0 for t in data['schedule'])


def test_movement_matches_previous_rank_and_history_matches_dashboard():
    data = snapshot()
    previous = {t['roster_id']: t for t in data['history'] if t['week'] == 1}
    latest = {t['roster_id']: t for t in data['history'] if t['week'] == 2}
    for team in data['rankings']:
        rid = team['roster_id']
        assert team['rank_change'] == previous[rid]['rank'] - team['rank']
        for field in ['power_index','rank','rank_change']:
            assert team[field] == latest[rid][field]
        total = 50 + team['scoring_contribution'] + team['all_play_contribution'] + team['projection_contribution']
        assert team['power_index'] == pytest.approx(min(100,max(0,total)), abs=.001)


def test_missing_projection_stats_neutralizes_entire_league_not_just_one_team():
    partial = {'1':{'stats':{'pts':999}}, '2':{'stats':{'pts':100}}}
    data = snapshot([(1,example([100,90,80,70]))], {1:partial})
    assert all(not t['projections_available'] for t in data['rankings'])
    assert all(t['projection_contribution'] == 0 for t in data['rankings'])
    assert data['warnings']


def test_projection_availability_change_does_not_claim_rank_movement():
    full = {str(i):{'stats':{'pts':i*10}} for i in range(1,5)}
    data = snapshot(projections={2:full})
    assert all(t['projections_available'] for t in data['rankings'])
    assert all(t['rank_change'] is None for t in data['rankings'])
    assert any('movement is hidden' in w for w in data['warnings'])


def test_missing_team_stops_history_instead_of_silently_changing_opponent_pool():
    data = snapshot([(1,example([100,90,80,70])), (2,example([100,90,80,70])[:3])])
    assert data['through_week'] == 1
    assert data['weeks'] == [1]
    assert len(data['rankings']) == 4
    assert any('incomplete' in w for w in data['warnings'])


@pytest.mark.parametrize('state,expected', [
    ({'season':'2026','season_type':'pre','week':4},0),
    ({'season':'2026','season_type':'regular','week':1},0),
    ({'season':'2026','season_type':'regular','week':7},6),
    ({'season':'2026','season_type':'regular','week':17},14),
    ({'season':'2026','season_type':'post','week':1},14),
    ({'season':'2027','season_type':'pre','week':1},14),
])
def test_cutoff_excludes_current_week_and_fantasy_playoffs(state, expected):
    assert completed_week_limit({'season':'2026','settings':{'playoff_week_start':15}},state) == expected


def test_all_play_standings_sort_by_tie_adjusted_percentage():
    frame = pd.DataFrame({'roster_id':[1,2],'all_play_wins':[3,2],'all_play_losses':[3,0],'all_play_ties':[0,4]})
    assert calculate_all_wins_standings(frame).iloc[0]['roster_id'] == 2


def test_schedule_invariants_over_random_tied_scores():
    rng = random.Random(48)
    for size in [2,4,8,12]:
        frames=[]
        for week in range(1,8):
            ids=list(range(1,size+1)); rng.shuffle(ids)
            frames.append(pd.DataFrame([{'week':week,'roster_id':rid,'matchup_id':i//2+1,'points':rng.choice([0,80.1,100.8,120.2])} for i,rid in enumerate(ids)]))
        data=process_matchups_data(frames,size)
        result=calculate_schedule_advantage(data)
        assert result.actual_wins.sum() == pytest.approx(size*7/2)
        assert result.expected_wins.sum() == pytest.approx(size*7/2)
        assert result.schedule_advantage.sum() == pytest.approx(0,abs=1e-10)
        assert ((result.expected_wins >= 0) & (result.expected_wins <= 7)).all()
        assert data.all_play_wins.sum() == data.all_play_losses.sum()


def test_weekly_average_and_component_contributions_match_independent_formula():
    import statistics
    scores=[100,120,80,90]
    full={str(i):{'stats':{'pts':value}} for i,value in enumerate([90,80,110,100],1)}
    data=snapshot([(1,example(scores))], {1:full})
    assert all(t['league_average'] == 97.5 for t in data['weekly_scores'])
    points_z=(100-statistics.mean(scores))/statistics.stdev(scores)
    all_play=[2,3,0,1]
    wins_z=(2-statistics.mean(all_play))/statistics.stdev(all_play)
    proj=[90,80,110,100]
    proj_z=(90-statistics.mean(proj))/statistics.stdev(proj)
    expected=50+10*(.45*points_z+.40*wins_z+.15*proj_z)
    team=next(t for t in data['rankings'] if t['roster_id']==1)
    assert team['power_index'] == pytest.approx(expected,abs=.0001)


def test_null_week_data_is_an_explicit_empty_state():
    data=snapshot([(1,None)])
    assert data['rankings']==[] and data['through_week'] is None


def test_nonfinite_projection_stats_are_unavailable():
    full={str(i):{'stats':{'pts':100}} for i in range(1,5)}
    full['1']['stats']['pts']=float('nan')
    data=snapshot([(1,example([100,90,80,70]))],{1:full})
    assert all(t['projection_contribution']==0 for t in data['rankings'])
