import pandas as pd
import numpy as np

    
# Helper to map user_id to display name
def create_users_map(users_data):
    return {u['user_id']: u['display_name'] for u in users_data}

#Helper to map roster_id to user_id
def create_rosters_map(rosters_data):
    return {r['roster_id']: r['owner_id'] for r in rosters_data}


def calculate_z_scores(df, score_column='points'):
    mean_score = df.groupby('week')[score_column].transform('mean')
    std_dev_score = df.groupby('week')[score_column].transform('std')
    
    # replace(0, 1) prevents dividing by zero!
    df['z_score'] = ((df[score_column] - mean_score) / std_dev_score.replace(0, 1)).fillna(0)
    return df
        
def get_z_score(series):
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def process_matchups_data(all_matchups_data, total_rosters):
    if not all_matchups_data:
        return pd.DataFrame()
    
    total_possible_games_per_week = total_rosters - 1

    df_all_matchups = pd.concat(all_matchups_data, ignore_index=True)

    if 'custom_points' in df_all_matchups:
        df_all_matchups['points'] = df_all_matchups['custom_points'].combine_first(df_all_matchups['points'])
    # Count only the teams actually represented in each week.
    total_possible_games_per_week = df_all_matchups.groupby('week')['roster_id'].transform('count') - 1

    # Rank Points for Week
    df_all_matchups['rank'] = df_all_matchups.groupby('week')['points'].rank(method='min', ascending=True)
    
    # Calculate All Play Record (The Record for if they played every team that week)
    df_all_matchups['all_play_wins'] = df_all_matchups['rank'] - 1
    df_all_matchups['all_play_ties'] = df_all_matchups.groupby(['week', 'points'])['roster_id'].transform('count') - 1
    df_all_matchups['all_play_losses'] = total_possible_games_per_week - df_all_matchups['all_play_wins'] - df_all_matchups['all_play_ties']

    df_all_matchups = calculate_z_scores(df_all_matchups, score_column='points')
    return df_all_matchups[['week', 'roster_id', 'matchup_id', 'points', 'all_play_wins', 'all_play_losses', 'all_play_ties', 'z_score']]


# Helper to get true record 
def get_true_record(users_data, rosters_data):
    user_map = create_users_map(users_data)
    roster_map = create_rosters_map(rosters_data)
    
    records = []
    for roster in rosters_data:
        roster_id = roster['roster_id']
        
        owner_id = roster_map.get(roster_id)
        display_name = user_map.get(owner_id, "Unknown")
        
        settings = roster.get('settings', {})
        
        records.append({
            'roster_id': roster_id,
            'owner_id': display_name,
            'wins': settings.get('wins', 0),
            'losses': settings.get('losses', 0),
            'ties': settings.get('ties', 0)
        })       

    return pd.DataFrame(records)
     

# Helper to calculate player score based on league scoring settings
def calculate_player_score(player_data, scoring_settings):
    score = 0
    for stat_key, multiplier in scoring_settings.items():
        # Look for the stat (e.g., 'pass_yd') directly in player_data
        val = player_data.get(stat_key, 0)
        score += (val * multiplier)
    return score

# Helper to get projections DataFrame
def get_projections(league_data, matchups_data, weekly_projections_data):
    scoring_settings = league_data.get('scoring_settings', {})

    projections = []
    for matchup in matchups_data:
        total_projected_points = 0
        starters = matchup.get('starters', [])
        
        if starters is None:
            starters = []
        
        for player_id in starters:
            player_data = weekly_projections_data.get(str(player_id), {})
            
            player_stats = player_data.get('stats', {})

            
            if player_stats:
                total_projected_points += calculate_player_score(player_stats, scoring_settings)
            
        projections.append({
            'roster_id': matchup['roster_id'],
            'projected_points': round(total_projected_points, 2)
        })

    return pd.DataFrame(projections)


# Aggregrates Data into Season Totals
def calculate_season_aggregates(df):
    df = df.copy()
    df['all_play_ties'] = df.get('all_play_ties', 0)
    return df.groupby('roster_id').agg({
        'all_play_wins': 'sum',
        'all_play_losses': 'sum',
        'all_play_ties': 'sum',
        'z_score': 'sum',
        'points': 'sum'
    }).reset_index()
    
# Helper to calculate power rankings
def get_power_rankings(season_df, projections_df, weights=None):
    if weights is None:
        weights = {
            'points': 0.45,
            'all_play_wins': 0.40,
            'projected_points': 0.15
        }

    merged_df = season_df.merge(projections_df, on='roster_id')
    
    merged_df['z_all_play_wins'] = get_z_score(merged_df['all_play_wins'] + 0.5 * merged_df.get('all_play_ties', 0))
    merged_df['z_points'] = get_z_score(merged_df['points'])
    merged_df['z_projected_points'] = get_z_score(merged_df['projected_points'])
    
    merged_df[['z_points', 'z_all_play_wins', 'z_projected_points']] = merged_df[['z_points', 'z_all_play_wins', 'z_projected_points']].fillna(0)

    # Calculate the weighted score
    merged_df['composite_score'] = (
        merged_df['z_all_play_wins'] * weights['all_play_wins'] +
        merged_df['z_points'] * weights['points'] +
        merged_df['z_projected_points'] * weights['projected_points']
    )

    # Scale the weighted composite around 50; its SD is not necessarily 10.
    merged_df['power_index'] = 50 + (merged_df['composite_score'] * 10) 
    merged_df['power_index'] = merged_df['power_index'].clip(0, 100)

    # Sort by the power ranking score in descending order
    ranked_df = merged_df.sort_values(by='power_index', ascending=False).reset_index(drop=True)
    ranked_df['rank'] = ranked_df['power_index'].round(4).rank(method='min', ascending=False).astype(int)
    
    return ranked_df[['rank', 'roster_id', 'power_index', 'z_points', 'z_all_play_wins', 'z_projected_points']].round(4)   


def calculate_trend_lines(season_df, projections_df, target_roster_id):   
    trend_data = []
    max_week = int(season_df['week'].max())
    
    for wk in range(1, max_week + 1):
        matchups_slice = season_df[season_df['week'] <= wk]
        projections_slice = projections_df[projections_df['week'] == wk]
        
        aggs_df = calculate_season_aggregates(matchups_slice)
        
        proj_aggs = projections_slice.groupby('roster_id')['projected_points'].sum().reset_index()
        
        rankings = get_power_rankings(aggs_df, proj_aggs)
        
        user_row = rankings[rankings['roster_id'] == target_roster_id]
        
        if not user_row.empty:
            trend_data.append({
                'week': wk,
                'rank': int(user_row.iloc[0]['rank']),
                'power_index': float(user_row.iloc[0]['power_index'])
            })
            
    return pd.DataFrame(trend_data)

def calculate_weekly_regular_standings(season_df):
    """
    Calculates cumulative H2H records (Wins, Losses, PF, PA)
    from the data provided in season_df.
    """

    season_df = paired_matchups(season_df)
    opponents = season_df[['week', 'matchup_id', 'roster_id', 'points']].copy()
    opponents.columns = ['week', 'matchup_id', 'opponent_id', 'opponent_points']
    
    merged_df = season_df.merge(opponents, on=['week', 'matchup_id'])
    merged_df = merged_df[merged_df['roster_id'] != merged_df['opponent_id']]
    
    merged_df['wins'] = merged_df['points'] > merged_df['opponent_points']
    merged_df['losses'] = merged_df['points'] < merged_df['opponent_points']
    merged_df['ties'] = merged_df['points'] == merged_df['opponent_points']
    
    standings = merged_df.groupby('roster_id').agg({
        'wins': 'sum',
        'losses': 'sum',
        'ties': 'sum',
        'points': 'sum',
        'opponent_points': 'sum'
    }).reset_index()
    
    standings['win_pct'] = round((standings['wins'] + (standings['ties'] * 0.5)) / (standings['wins'] + standings['losses'] + standings['ties']), 4)
    
    return standings.sort_values(by=['win_pct', 'points'], ascending=False)

def calculate_all_wins_standings(season_df):
    df = season_df[['roster_id', 'all_play_wins', 'all_play_losses']].copy()
    df['all_play_ties'] = season_df.get('all_play_ties', 0)
    standings = df.groupby('roster_id').agg({
        'all_play_wins': 'sum',
        'all_play_losses': 'sum',
        'all_play_ties': 'sum'
    }).reset_index()
    
    standings['win_pct'] = round((standings['all_play_wins'] + 0.5 * standings['all_play_ties']) / (standings['all_play_wins'] + standings['all_play_losses'] + standings['all_play_ties']), 4)
    return standings.sort_values(by=['win_pct', 'roster_id'], ascending=[False, True])

def calculate_rival_standings(season_df, user_roster_id, rival_roster_id):
    u_id = int(user_roster_id)
    r_id = int(rival_roster_id)
    
    user_points = season_df[season_df['roster_id'] == u_id][['week', 'points']]
    rival_target_points = season_df[season_df['roster_id'] == r_id][['week', 'points']]
    
    user_points.columns = ['week', 'points_user']
    rival_target_points.columns = ['week', 'points_rival']
    
    merged_df = user_points.merge(rival_target_points, on='week')
    
    merged_df['wins'] = (merged_df['points_user'] > merged_df['points_rival']).astype(int)
    merged_df['losses'] = (merged_df['points_user'] < merged_df['points_rival']).astype(int)
    merged_df['ties'] = (merged_df['points_user'] == merged_df['points_rival']).astype(int)
    
    standings = merged_df[['wins', 'losses', 'ties', 'points_user', 'points_rival']].sum().to_frame().T
    standings['roster_id'] = u_id
    
    return standings.reset_index(drop=True)


def paired_matchups(season_df):
    """Only genuine two-team matchups; null IDs and byes are not games."""
    valid = season_df[season_df['matchup_id'].notna()].copy()
    counts = valid.groupby(['week', 'matchup_id'])['roster_id'].transform('count')
    return valid[counts == 2]


def calculate_schedule_advantage(season_df):
    """Observed H2H win equivalents minus random-opponent win equivalents.

    A bye contributes neither an actual game nor expected wins. All-play
    probability uses all other teams' scores that week, with half credit for ties.
    Median bonus games are deliberately excluded from both sides.
    """
    games = paired_matchups(season_df).copy()
    denominator = games['all_play_wins'] + games['all_play_losses'] + games['all_play_ties']
    games['expected_wins'] = (games['all_play_wins'] + .5 * games['all_play_ties']) / denominator.replace(0, np.nan)
    expected = games.groupby('roster_id')['expected_wins'].sum()
    standings = calculate_weekly_regular_standings(season_df).set_index('roster_id')
    result = pd.DataFrame(index=sorted(season_df['roster_id'].unique()))
    result.index.name = 'roster_id'
    for column in ['wins', 'losses', 'ties']:
        result[column] = standings[column].reindex(result.index).fillna(0).astype(int)
    result['games'] = result['wins'] + result['losses'] + result['ties']
    result['actual_wins'] = result['wins'] + .5 * result['ties']
    result['expected_wins'] = expected.reindex(result.index).fillna(0)
    result['schedule_advantage'] = result['actual_wins'] - result['expected_wins']
    return result.reset_index()
