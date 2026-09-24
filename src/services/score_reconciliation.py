"""Repair demonstrably inconsistent matchup totals without using projections.

Known league-scored player points remain authoritative. Only missing starter
entries require raw actual statistics; unsupported scoring fails closed.
"""
import math
import re

import httpx


class UnresolvedScore(ValueError):
    pass


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# These actual counting stats are sparse: an omitted event means none occurred.
SPARSE_STATS = set('''pass_yd pass_td pass_int pass_2pt pass_att pass_cmp pass_inc
pass_sack pass_fd rush_yd rush_td rush_2pt rush_att rush_fd rec rec_yd rec_td
rec_2pt rec_fd rec_tgt fum fum_lost fum_rec fum_rec_td sack int ff def_td safe
blk_kick def_2pt st_td st_fum_rec st_ff def_st_td def_st_fum_rec def_st_ff
fgm_0_19 fgm_20_29 fgm_30_39 fgm_40_49 fgm_50_59 fgm_60p xpm xpmiss
pts_allow_0 pts_allow_1_6 pts_allow_7_13 pts_allow_14_20 pts_allow_21_27
pts_allow_28_34 pts_allow_35p yds_allow_0_100 yds_allow_100_199
 yds_allow_200_299 yds_allow_300_349 yds_allow_350_399 yds_allow_400_449
 yds_allow_450_499 yds_allow_500_549 yds_allow_550p'''.split())


def score_actual_stats(stats, settings):
    if not isinstance(stats, dict) or not stats or not finite(stats.get('gp')) or stats['gp'] <= 0:
        raise UnresolvedScore('actual game statistics are unavailable')
    if not isinstance(settings, dict) or not settings:
        raise UnresolvedScore('league scoring settings are unavailable')
    total = 0.0
    for key, multiplier in settings.items():
        if not finite(multiplier):
            raise UnresolvedScore('invalid scoring multiplier')
        if not multiplier:
            continue
        if key in stats:
            value = stats[key]
        elif key == 'fgmiss' and 'fga' in stats and 'fgm' in stats:
            if not finite(stats['fga']) or not finite(stats['fgm']) or stats['fga'] < stats['fgm']:
                raise UnresolvedScore('inconsistent kicking statistics')
            value = stats['fga'] - stats['fgm']
        elif key == 'fgmiss' and 'fga' not in stats and 'fgm' not in stats:
            value = 0
        elif match := re.fullmatch(r'bonus_(pass|rush|rec)_yd_(\d+)', key):
            yards = stats.get(f'{match[1]}_yd', 0)
            if not finite(yards) or yards >= int(match[2]):
                # Do not guess whether a league's bonus tiers stack.
                raise UnresolvedScore(f'missing actual scoring category {key}')
            value = 0
        elif key in SPARSE_STATS:
            for prefix, total_key in [('pts_allow_', 'pts_allow'), ('yds_allow_', 'yds_allow')]:
                if key.startswith(prefix) and total_key in stats:
                    # Actual defensive bands are sparse one-hot flags. Sleeper
                    # sends the applicable band, not a zero for every other band.
                    # Inspect all supported bands, even ones this league doesn't score.
                    bands = [v for k, v in stats.items() if k in SPARSE_STATS and k.startswith(prefix)]
                    if (not finite(stats[total_key]) or stats[total_key] < 0
                            or not bands or not all(finite(v) and v in (0, 1) for v in bands)
                            or sum(bands) != 1):
                        raise UnresolvedScore(f'missing or inconsistent defensive scoring categories for {total_key}')
            if key.startswith('fgm_') and stats.get('fgm', 0):
                buckets = [v for k, v in stats.items() if re.fullmatch(r'fgm_(\d+_\d+|60p)', k)]
                if not all(finite(v) for v in buckets) or not finite(stats['fgm']) or not math.isclose(sum(buckets), stats['fgm'], abs_tol=1e-8):
                    raise UnresolvedScore('incomplete field-goal distance statistics')
            value = 0
        else:
            raise UnresolvedScore(f'unsupported missing scoring category {key}')
        if not finite(value):
            raise UnresolvedScore(f'invalid actual statistic {key}')
        total += value * multiplier
    if not finite(total):
        raise UnresolvedScore('invalid reconstructed score')
    return total


async def reconcile_matchups(client, league, week, matchups, names=None):
    """Return copies and visible notes. Unresolved scores stop the snapshot week."""
    if not isinstance(matchups, list):
        return matchups, []
    names = names or {}
    output, warnings, recovered = [], [], {}
    for original in matchups:
        if not isinstance(original, dict):
            output.append(original)
            continue
        row = dict(original)
        output.append(row)
        if row.get('custom_points') is not None:
            continue
        # Some historical responses omit detailed scoring; do not fabricate it.
        if 'players_points' not in row:
            continue
        label = names.get(row.get('roster_id')) or f"Roster {row.get('roster_id')}"
        try:
            player_points = row['players_points']
            starters = row.get('starters')
            if not isinstance(player_points, dict) or not isinstance(starters, list):
                raise UnresolvedScore('starter scoring data is malformed')
            occupied = [str(p) for p in starters if str(p) != '0']
            if len(set(occupied)) != len(occupied):
                raise UnresolvedScore('duplicate starters')
            scores, missing = [], []
            for pid in occupied:
                if pid in player_points:
                    value = player_points[pid]
                    if not finite(value):
                        raise UnresolvedScore(f'invalid score for starter {pid}')
                else:
                    missing.append(pid)
                    if pid not in recovered:
                        entry = await client.get_player_week_stats(pid, str(league['season']), week)
                        recovered[pid] = score_actual_stats(entry.get('stats') if isinstance(entry, dict) else None, league.get('scoring_settings'))
                    value = recovered[pid]
                scores.append(value)
            total = round(sum(scores), 2)
            if missing or not finite(row.get('points')) or not math.isclose(total, row['points'], abs_tol=.011):
                old = row.get('points')
                row['points'] = total
                warnings.append(f'Week {week}: {label} had inconsistent Sleeper lineup/score data. Rebuilt the starter total as {total:.2f} (reported total: {old}).' + (f" Recovered actual points for starter IDs: {', '.join(missing)}." if missing else ''))
        except (UnresolvedScore, httpx.HTTPError, ValueError, TypeError) as exc:
            row['points'] = None
            reason = str(exc) if isinstance(exc, UnresolvedScore) else 'actual player data could not be verified'
            warnings.append(f'Week {week}: {label} has inconsistent starter scores that could not be reconciled ({reason}). Analysis stops before this week.')
    return output, warnings
