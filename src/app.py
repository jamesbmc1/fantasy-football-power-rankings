import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api_clients.sleeper import SleeperAPIClient
from src.utils.calculations import create_rosters_map, create_users_map, process_matchups_data, get_true_record, get_power_rankings, calculate_trend_lines, get_projections, calculate_season_aggregates, calculate_weekly_regular_standings, calculate_all_wins_standings, calculate_rival_standings
import asyncio
import uvicorn
from dotenv import load_dotenv


app = FastAPI(title="Fantasy Football Power Rankings API")
load_dotenv()

# Allows Communication between Python and Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://fantasy-football-power-rankings-black.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SleeperAPIClient()

async def fetch_base_league_data(league_id: str):
    league_info, users_data = await asyncio.gather(
        client.get_league_info(league_id),
        client.get_league_users(league_id),
    )
    
    return {
        "league_info": league_info,
        "users": users_data,
    }

async def fetch_matchups_up_to_week(league_id: str, current_week: int):
    tasks = [client.get_matchups(league_id, wk) for wk in range(1, current_week + 1)]
    matchups = await asyncio.gather(*tasks)
    return matchups
        
        
async def fetch_projections_up_to_week(season: str, current_week: int):
    tasks = [client.get_weekly_projections(season, wk) for wk in range(1, current_week + 1)]
    projections = await asyncio.gather(*tasks)
    return projections

def format_df_to_json(df: pd.DataFrame):
    # Helper to safely convert a Pandas DataFrame into a List of Dictionaries 
    # so FastAPI can return it as JSON to the frontend.
    return df.to_dict(orient="records")


@app.get("/rankings/{league_id}/{week}")
async def fetch_rankings(league_id: str, week: int):
    league_data = await fetch_base_league_data(league_id)
    season = league_data["league_info"]["season"]
    total_rosters = league_data["league_info"].get("total_rosters", 10)
    
    rosters_data, projections_to_week, matchups_up_to_week = await asyncio.gather(
        client.get_league_rosters(league_id),
        fetch_projections_up_to_week(season, week),
        fetch_matchups_up_to_week(league_id, week),
    )
    
    matchup_dfs = []
    for wk_idx, wk_matchups in enumerate(matchups_up_to_week):
        df = pd.DataFrame(wk_matchups)
        df['week'] = wk_idx + 1 
        matchup_dfs.append(df)
    
    season_df = process_matchups_data(matchup_dfs, total_rosters)    
    aggs_df = calculate_season_aggregates(season_df)
        
    current_matchups = matchups_up_to_week[-1]
    current_projections = projections_to_week[-1]
    projections_df = get_projections(league_data["league_info"], current_matchups, current_projections)
    
    # Generate the final rankings
    ranked_df = get_power_rankings(aggs_df, projections_df)
    
    user_map = create_users_map(league_data["users"])
    roster_map = create_rosters_map(rosters_data)
    
    ranked_df['owner_name'] = ranked_df['roster_id'].map(roster_map).map(user_map)
    
    # Return the final output to the frontend formatted as JSON
    return format_df_to_json(ranked_df)

@app.get("/trends/{league_id}/{target_owner_name}/{week}")
async def fetch_team_trends(league_id: str, target_owner_name: str, week: int):
    league_data = await fetch_base_league_data(league_id)
    season = league_data["league_info"]["season"]
    total_rosters = league_data["league_info"].get("total_rosters", 10)
    
    rosters_data, projections_to_week, matchups_up_to_week = await asyncio.gather(
        client.get_league_rosters(league_id),
        fetch_projections_up_to_week(season, week),
        fetch_matchups_up_to_week(league_id, week),
    )

    matchup_dfs = []
    for wk_idx, wk_matchups in enumerate(matchups_up_to_week):
        df = pd.DataFrame(wk_matchups)
        df['week'] = wk_idx + 1 
        matchup_dfs.append(df)
        
    user_map = create_users_map(league_data["users"])
    roster_map = create_rosters_map(rosters_data)
    
    target_user_id = next((uid for uid, name in user_map.items() if name == target_owner_name), None)
    target_roster_id = next((rid for rid, uid in roster_map.items() if uid == target_user_id), None)
        
    season_df = process_matchups_data(matchup_dfs, total_rosters)    
    
    proj_dfs = []
    for wk_idx, (wk_matchups, wk_projections) in enumerate(zip(matchups_up_to_week, projections_to_week)):
        df = get_projections(league_data["league_info"], wk_matchups, wk_projections)
        df['week'] = wk_idx + 1 
        proj_dfs.append(df)
        
    projections_df = pd.concat(proj_dfs, ignore_index=True)
        
    trend_df = calculate_trend_lines(season_df, projections_df, target_roster_id)
    
    return format_df_to_json(trend_df)

@app.get("/standings/{league_id}/{week}/{user_roster_id}/{target_roster_id}")
async def fetch_standings(league_id: str, week: int, user_roster_id: str, target_roster_id: str):


   league_data = await fetch_base_league_data(league_id)
   total_rosters = league_data["league_info"].get("total_rosters", 10)
  
   rosters_data, matchups_up_to_week = await asyncio.gather(
       client.get_league_rosters(league_id),
       fetch_matchups_up_to_week(league_id, week),
   )
  
   matchup_dfs = []
   for wk_idx, wk_matchups in enumerate(matchups_up_to_week):
       df = pd.DataFrame(wk_matchups)
       df['week'] = wk_idx + 1
       matchup_dfs.append(df)
  
   season_df = process_matchups_data(matchup_dfs, total_rosters)
  
   standings_df = calculate_weekly_regular_standings(season_df)
   all_wins_df = calculate_all_wins_standings(season_df)
  
   rivals_df = calculate_rival_standings(season_df, int(user_roster_id), int(target_roster_id))


   user_map = create_users_map(league_data["users"])
   roster_map = create_rosters_map(rosters_data)
  
   standings_df['owner_name'] = standings_df['roster_id'].map(roster_map).map(user_map)
   all_wins_df['owner_name'] = all_wins_df['roster_id'].map(roster_map).map(user_map)
  
   rivals_df['owner_name'] = rivals_df['roster_id'].map(roster_map).map(user_map)
   rivals_df['rival_name'] = int(target_roster_id)
   rivals_df['rival_name'] = rivals_df['rival_name'].map(roster_map).map(user_map)   
  
   return {
       'regular': format_df_to_json(standings_df),
       'all_play': format_df_to_json(all_wins_df),
       'rivals': format_df_to_json(rivals_df)
   }

     
if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)