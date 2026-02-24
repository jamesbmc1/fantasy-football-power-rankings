import pandas as pd
from pathlib import Path
import os
import sys

    
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
    return (series - series.mean()) / series.std()


def process_matchups_data(all_matchups_data, total_rosters):
    if not all_matchups_data:
        return pd.DataFrame()
    
    total_possible_games_per_week = total_rosters - 1

    df_all_matchups = pd.concat(all_matchups_data, ignore_index=True)

    # Rank Points for Week
    df_all_matchups['rank'] = df_all_matchups.groupby('week')['points'].rank(method='min', ascending=True)
    
    # Calculate All Play Record (The Record for if they played every team that week)
    df_all_matchups['all_play_wins'] = df_all_matchups['rank'] - 1
    df_all_matchups['all_play_losses'] = total_possible_games_per_week - df_all_matchups['all_play_wins']

    df_all_matchups = calculate_z_scores(df_all_matchups, score_column='points')
    return df_all_matchups

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
            player_stats = weekly_projections_data.get(str(player_id), {})
            
            if not player_stats:
                continue
            
            total_projected_points += calculate_player_score(player_stats, scoring_settings)
            
        projections.append({
            'roster_id': matchup['roster_id'],
            'projected_points': round(total_projected_points, 2)
        })

    return pd.DataFrame(projections)


# Aggregrates Data into Season Totals
def calculate_season_aggregates(df):
    return df.groupby('roster_id').agg({
        'all_play_wins': 'sum',
        'all_play_losses': 'sum', 
        'z_score': 'sum',
        'points': 'sum'
    }).reset_index()

# Helper to calculate power rankings
def get_power_rankings(season_df, record_df, projections_df, weights=None):
    if weights is None:
        weights = {
            'points': 0.5,
            'wins': 0.3,
            'projected_points': 0.2
        }

    merged_df = season_df.merge(record_df, on='roster_id').merge(projections_df, on='roster_id')

    merged_df['z_points'] = get_z_score(merged_df['points'])
    merged_df['z_wins'] = get_z_score(merged_df['wins'])
    merged_df['z_projected_points'] = get_z_score(merged_df['projected_points'])
    
    merged_df[['z_points', 'z_wins', 'z_projected_points']] = merged_df[['z_points', 'z_wins', 'z_projected_points']].fillna(0)

    # Calculate the weighted score
    merged_df['composite_score'] = (
        merged_df['z_points'] * weights['points'] +
        merged_df['z_wins'] * weights['wins'] +
        merged_df['z_projected_points'] * weights['projected_points']
    )

    # Map the Z-Score to a T-Score distribution (Mean=50, StdDev=10)
    merged_df['power_index'] = 50 + (merged_df['composite_score'] * 10) 
    merged_df['power_index'] = merged_df['power_index'].clip(0, 100)

    # Sort by the power ranking score in descending order
    ranked_df = merged_df.sort_values(by='power_index', ascending=False).reset_index(drop=True)
    ranked_df['rank'] = range(1, len(ranked_df) + 1)

    return ranked_df[['rank', 'owner_id', 'power_index', 'z_points', 'z_wins', 'z_projected_points']].round(4)   


def calculate_trend_lines(season_df, record_df, projections_df, target_owner_name):   
    trend_data = []
    max_week = int(season_df['week'].max())
    
    for wk in range(1, max_week + 1):
        matchups_slice = season_df[season_df['week'] <= wk]
        projections_slice = projections_df[projections_df['week'] <= wk]
        
        aggs = calculate_season_aggregates(matchups_slice)
        
        proj_aggs = projections_slice.groupby('roster_id')['projected_points'].sum().reset_index()
        
        rankings = get_power_rankings(aggs, record_df, proj_aggs)
        
        user_row = rankings[rankings['owner_id'] == target_owner_name]
        
        if not user_row.empty:
            trend_data.append({
                'week': wk,
                'rank': int(user_row.iloc[0]['rank']),
                'power_index': float(user_row.iloc[0]['power_index'])
            })
            
    return pd.DataFrame(trend_data)