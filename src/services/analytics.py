"""One calculation snapshot for rankings, standings, charts and team detail."""
import asyncio
import math
from datetime import datetime, timezone

import httpx
import pandas as pd
from fastapi import HTTPException

from src.utils.calculations import (
    process_matchups_data, calculate_season_aggregates, get_power_rankings,
    get_projections, calculate_schedule_advantage, calculate_weekly_regular_standings,
    calculate_all_wins_standings,
)


def completed_week_limit(league, state):
    """Conservative cutoff: current NFL week is excluded until state rolls over."""
    season, current = int(league['season']), int(state['season'])
    playoff_start = int(league.get('settings', {}).get('playoff_week_start', 0) or 0)
    end = min(18, playoff_start - 1) if playoff_start > 0 else 18
    if season < current:
        return end
    if season > current or state.get('season_type') == 'pre':
        return 0
    if state.get('season_type') == 'post':
        return end
    if state.get('season_type') != 'regular':
        raise ValueError('Unknown NFL season state')
    return max(0, min(end, int(state['week']) - 1))


def projection_frame(league, matchups, payload):
    """Use projections only when every occupied starter has a stats object."""
    available = isinstance(payload, dict) and bool(league.get('scoring_settings'))
    for matchup in matchups:
        starters = [str(p) for p in (matchup.get('starters') or []) if str(p) != '0']
        if not starters:
            available = False
        for player in starters:
            entry = payload.get(player, {}) if isinstance(payload, dict) else {}
            stats = entry.get('stats') if isinstance(entry, dict) else None
            if not isinstance(stats, dict) or not stats:
                available = False
            elif any(not isinstance(v, (int, float)) or not math.isfinite(v) for k, v in stats.items() if k in league.get('scoring_settings', {})):
                available = False
    frame = get_projections(league, matchups, payload) if available else pd.DataFrame(
        [{'roster_id': m['roster_id'], 'projected_points': 0.0} for m in matchups])
    return frame, available


def records(frame):
    # JSON-safe conversion preserves explicit null instead of NaN/Infinity.
    import json
    return json.loads(frame.to_json(orient='records', double_precision=10))


def build_snapshot(league, users, rosters, weeks, projections, requested_week, warnings=None):
    warnings = list(warnings or [])
    owners = {u['user_id']: u.get('display_name') or u.get('username') for u in users}
    names = {r['roster_id']: owners.get(r.get('owner_id')) or f"Team {r['roster_id']}" for r in rosters}
    roster_ids = set(names)
    frames, accepted = [], []
    for wk, matchups in weeks:
        matchups = matchups if isinstance(matchups, list) else []
        if not all(isinstance(m, dict) for m in matchups):
            matchups = []
        ids = [m.get('roster_id') for m in matchups]
        valid = len(ids) == len(roster_ids) and set(ids) == roster_ids and len(ids) >= 2
        for m in matchups:
            score = m.get('custom_points') if m.get('custom_points') is not None else m.get('points')
            valid = valid and isinstance(score, (int, float)) and math.isfinite(score)
        if not valid:
            warnings.append(f'Week {wk} has incomplete score data. Analysis stops before that week.')
            break
        frames.append(pd.DataFrame(matchups).assign(week=wk))
        accepted.append((wk, matchups))
    result = {
        'league_id': str(league['league_id']), 'league_name': league.get('name', 'Sleeper league'),
        'season': str(league['season']), 'requested_week': requested_week,
        'through_week': accepted[-1][0] if accepted else None,
        'weeks': [w for w, _ in accepted], 'warnings': warnings,
        'rankings': [], 'history': [], 'weekly_scores': [], 'schedule': [], 'regular': [], 'all_play': [],
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }
    if not accepted:
        warnings.append('No completed regular-season weeks are available for this selection.')
        return result
    season = process_matchups_data(frames, len(rosters))
    from src.utils.calculations import paired_matchups
    unpaired = len(season) - len(paired_matchups(season))
    if unpaired:
        warnings.append(f'{unpaired} team-week entries have no valid two-team matchup. Their scores remain in all-play rankings, but they contribute no H2H game or expected win.')
    previous = None
    previous_available = None
    for wk, matchups in accepted:
        frame, available = projection_frame(league, matchups, projections.get(wk))
        cumulative = season[season.week <= wk]
        ranking = get_power_rankings(calculate_season_aggregates(cumulative), frame)
        schedule = calculate_schedule_advantage(cumulative).set_index('roster_id')
        avg = float(season[season.week == wk].points.mean())
        week_rows = season[season.week == wk].set_index('roster_id')
        ranking['owner_name'] = ranking.roster_id.map(names)
        ranking['rank_change'] = ranking.apply(
            lambda row: int(previous.loc[row.roster_id, 'rank'] - row['rank'])
            if previous is not None and available == previous_available else None, axis=1)
        ranking['projections_available'] = available
        # Use the returned standardized values so contribution labels reconcile
        # with the displayed score to rounding precision.
        ranking['scoring_contribution'] = ranking.z_points * 4.5
        ranking['all_play_contribution'] = ranking.z_all_play_wins * 4.0
        ranking['projection_contribution'] = ranking.z_projected_points * 1.5
        ranking['unclipped_index'] = 50 + ranking.scoring_contribution + ranking.all_play_contribution + ranking.projection_contribution
        for row in records(ranking):
            rid = row['roster_id']
            own = week_rows.loc[rid]
            actual = schedule.loc[rid]
            result['history'].append({**row, 'week': wk, 'points': float(own.points), 'league_average': avg,
                                      **{k: float(actual[k]) for k in ['wins', 'losses', 'ties', 'actual_wins', 'expected_wins', 'schedule_advantage']}})
        if not available:
            warnings.append(f'Week {wk}: complete starter projections unavailable. The 15% projection contribution is neutral for every team; scoring and all-play retain their 45% and 40% weights.')
        if previous is not None and available != previous_available:
            warnings.append(f'Week {wk}: rank movement is hidden because projection availability changed from the previous week.')
        previous = ranking.set_index('roster_id')
        previous_available = available
        result['rankings'] = records(ranking)
    weekly = season.copy()
    weekly['owner_name'] = weekly.roster_id.map(names)
    weekly['league_average'] = weekly.groupby('week').points.transform('mean')
    result['weekly_scores'] = records(weekly)
    for key, fn in [('schedule', calculate_schedule_advantage), ('regular', calculate_weekly_regular_standings), ('all_play', calculate_all_wins_standings)]:
        table = fn(season)
        table['owner_name'] = table.roster_id.map(names)
        result[key] = records(table)
    if league.get('settings', {}).get('league_average_match'):
        warnings.append('Records here count head-to-head matchups only; your league’s extra median game is excluded from both actual and expected wins.')
    return result


async def load_analytics(client, league_id, requested_week):
    league, users, rosters, state = await asyncio.gather(
        client.get_league_info(league_id), client.get_league_users(league_id),
        client.get_league_rosters(league_id), client.get_nfl_state())
    if not isinstance(league, dict) or not league.get('season'):
        raise HTTPException(404, 'League not found. Check your Sleeper league ID.')
    if league.get('sport', 'nfl') != 'nfl' or league.get('season_type', 'regular') != 'regular':
        raise HTTPException(422, 'This analysis supports NFL regular-season leagues.')
    league = {**league, 'league_id': league_id}
    try:
        limit = min(requested_week, completed_week_limit(league, state))
        start = max(1, int(league.get('settings', {}).get('start_week', 1) or 1))
    except (ValueError, TypeError, KeyError):
        raise HTTPException(503, 'Could not determine completed weeks from Sleeper. Try again later.')
    warnings = []
    if limit < requested_week:
        warnings.append(f'You selected week {requested_week}. Analysis uses completed regular-season weeks only, currently through week {limit}. The current NFL week is included after Sleeper advances to the next week.')
    week_numbers = list(range(start, limit + 1))
    matchups = await asyncio.gather(*(client.get_matchups(league_id, w) for w in week_numbers))
    async def optional_projections(w):
        try:
            return await client.get_weekly_projections(league['season'], w)
        except (httpx.HTTPError, ValueError, TypeError):
            return None
    projection_data = await asyncio.gather(*(optional_projections(w) for w in week_numbers))
    return build_snapshot(league, users or [], rosters or [], list(zip(week_numbers, matchups)),
                          dict(zip(week_numbers, projection_data)), requested_week, warnings)
