import pandas as pd
from pathlib import Path
import os
import sys

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.api_clients.sleeper import SleeperAPIClient

# Helper to get matchup data as DataFrame
def get_dataframe_for_matchups(league_id, week, refresh=False):
        if not refresh and os.path.exists(f'data/matchups_{league_id}_wk{week}.json'):
            df = pd.read_json(f'data/matchups_{league_id}_wk{week}.json')[['roster_id', 'points', 'matchup_id']]
            return df
        
        client = SleeperAPIClient(league_id=league_id)
        matchups = client.get_matchups(week=week, refresh=refresh)
        df = pd.read_json(f'data/matchups_{league_id}_wk{week}.json')[['roster_id', 'points', 'matchup_id']]
        return df


# Helper to calculate Z-Scores for points within each week
def calculate_z_scores(df, score_column='points'):
    mean_score = df.groupby('week')[score_column].transform('mean')
    std_dev_score = df.groupby('week')[score_column].transform('std')
    df['z_score'] = ((df[score_column] - mean_score) / std_dev_score).fillna(0)
    return df
        

def get_season_matchups_data(league_id, week):
    all_week_matchups = []
    client = SleeperAPIClient(league_id=league_id)
    number_of_players = len(client.get_league_rosters())
    total_possible_games_per_week = number_of_players - 1

    
    for wk in range(1, week + 1):
        df_matchups = get_dataframe_for_matchups(league_id, wk)
        df_matchups['week'] = wk
        all_week_matchups.append(df_matchups)

    df_all_matchups = pd.concat(all_week_matchups, ignore_index=True)
    print("\n--- All Matchups Data ---")
    print(df_all_matchups)

    # Calculate the rank for each team within their specific week
    # We use method='min' to handle ties (e.g., if two teams tie for 1st, they both get rank 1)
    # 14 is highest 1 is lowest value
    df_all_matchups['rank'] = df_all_matchups.groupby('week')['points'].rank(method='min', ascending=True)
    df_all_matchups['all_play_wins'] = df_all_matchups['rank'] - 1
    df_all_matchups['all_play_losses'] = total_possible_games_per_week - df_all_matchups['all_play_wins']

    df_all_matchups = calculate_z_scores(df_all_matchups, score_column='points')
    return df_all_matchups

# Helper to map roster_id to owner name
def id_to_name(client, roster_id):
    rosters = client.get_league_rosters()
    users = client.get_league_users()
    roster_map = {roster['roster_id']: roster['owner_id'] for roster in rosters}
    user_map = {user['user_id']: user['display_name'] for user in users}
    owner_id = roster_map.get(roster_id, 'Unknown')
    return user_map.get(owner_id, 'Unknown')

# Helper to get true records from the API
def get_true_record(league_id):
     client = SleeperAPIClient(league_id=league_id)
     rosters = client.get_league_rosters()
     true_records = []

     for roster in rosters:
        roster_id = roster['roster_id']
        username = id_to_name(client, roster_id)
        wins = roster['settings'].get('wins', 0)
        losses = roster['settings'].get('losses', 0)
        ties = roster['settings'].get('ties', 0)
        true_records.append({
            'roster_id': roster_id,
            'owner_id': username,
            'wins': wins,
            'losses': losses,
            'ties': ties
        })       

        df = pd.DataFrame(true_records)
        
     return df
     

# Helper to calculate player score based on league scoring settings
def calculate_player_score(player_data, scoring_settings):
    score = 0
    for stat_key, multiplier in scoring_settings.items():
        # Look for the stat (e.g., 'pass_yd') directly in player_data
        val = player_data.get(stat_key, 0)
        score += (val * multiplier)
    return score

# Helper to get projections DataFrame
def get_projections(league_id, week, season):
    client = SleeperAPIClient(league_id=league_id)
    
    #Fetch the league's custom scoring rules
    league_data = client.get_league_info() 
    scoring_settings = league_data.get('scoring_settings', {})

    matchups = client.get_matchups(week=week)
    
    # This should return the raw stats for every player, not just pre-calculated points
    projections_map = client.get_weekly_projections(season, week)

    projections = []
    for matchup in matchups:
        total_projected_points = 0
        for player_id in matchup['starters']:
            player_data = projections_map.get(str(player_id), {})

            # No projection/free agent
            if not player_data:
                continue  

            # Use the new helper to calculate score based on league rules
            player_score = calculate_player_score(player_data, scoring_settings)
            total_projected_points += player_score
            
        projections.append({
            'roster_id': matchup['roster_id'],
            'projected_points': round(total_projected_points, 2)
        })

    return pd.DataFrame(projections)

def get_z_score(series):
    return (series - series.mean()) / series.std()

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

    # Merge the df on 'roster_id'
    merged_df = season_df.merge(record_df, on='roster_id').merge(projections_df, on='roster_id')

    merged_df['z_points'] = get_z_score(merged_df['points'])
    merged_df['z_wins'] = get_z_score(merged_df['wins'])
    merged_df['z_projected_points'] = get_z_score(merged_df['projected_points'])

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

def get_season_projection_data(league_id, current_week, season):
    all_projections = []
    
    for wk in range(1, current_week + 1):
        weekly_df = get_projections(league_id, wk, season)
        weekly_df['week'] = wk
        all_projections.append(weekly_df)
        
        if not all_projections:
            return pd.DataFrame()
        
    return pd.concat(all_projections, ignore_index=True)


def get_owner_fluctuation(league_id, target_name, current_week):
    season = os.getenv("SEASON")
    full_season_data = get_season_matchups_data(league_id, current_week)
    record_df = get_true_record(league_id)
    full_season_projections = get_season_projection_data(league_id, current_week, season)
    
    fluctuation_data = []

    for wk in range(1, current_week + 1):
        historical_filter = full_season_data[full_season_data['week'] <= wk]
        historical_agg = calculate_season_aggregates(historical_filter)
        
        proj_filter = full_season_projections[full_season_projections['week'] <= wk]
        prog_agg = proj_filter.groupby('roster_id')['projected_points'].sum().reset_index()
        
        historical_ranks = get_power_rankings(historical_agg, record_df, prog_agg)
    
        user_row = historical_ranks[historical_ranks['owner_id'] == target_name]        
        if not user_row.empty:
            fluctuation_data.append({
                'week': wk,
                'owner_id': target_name,
                'rank': user_row.iloc[0]['rank'],
                'power_index': user_row.iloc[0]['power_index']
            })

    return pd.DataFrame(fluctuation_data) 