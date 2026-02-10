import pandas as pd
from pathlib import Path
import os
import sys
import argparse

from src.utils.calculations import get_power_rankings, get_projections, get_season_matchups_data, get_true_record, calculate_season_aggregates, get_owner_fluctuation
from src.api_clients.sleeper import SleeperAPIClient 
from src.utils.visualizer import luck_vs_skill_plot, league_standings, user_trends
from dotenv import load_dotenv


def main():
    load_dotenv()
    league_id = os.getenv("SLEEPER_LEAGUE_ID")
    season = os.getenv("SEASON")
    
    parser = argparse.ArgumentParser(prog="Sleeper Fantasy Football Power Rankings")
    parser.add_argument("current_week", type=int, help="The current week for your power rankings")
    parser.add_argument("owner_name", type=str, help="The name of the Team you want individual stats")
    args = parser.parse_args()
    
    try:
        raw_season_df = get_season_matchups_data(league_id, args.current_week)
        season_totals_data = calculate_season_aggregates(raw_season_df)
        
        projections_df = get_projections(league_id, args.current_week, season)
        record_df = get_true_record(league_id)
        
        power_rankings_df = get_power_rankings(season_totals_data, record_df, projections_df)
        trend_df = get_owner_fluctuation(league_id, args.owner_name, args.current_week)

        user_trends(trend_df, args.owner_name)
        print(power_rankings_df)
                
        luck_vs_skill_plot(power_rankings_df)
        league_standings(power_rankings_df)
    except Exception as e:
        print("There was an error: {e}")
        
        
if __name__ == "__main__":
    main()