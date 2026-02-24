import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api_clients.sleeper import SleeperAPIClient
from src.utils.calculations import process_matchups_data, get_true_record, get_power_rankings, calculate_trend_lines, get_projections, calculate_season_aggregates
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
        "https://fantasy-football-power-rankings-8vb.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = SleeperAPIClient()

async def fetch_base_league_data(league_id: str):
    """
    Helper to fetch the static league data that doesn't change week-to-week.
    Returns: A tuple or dict containing users, rosters, and league info.
    """
    league_info, users_data = await asyncio.gather(
        client.get_league_info(league_id),
        client.get_league_users(league_id),
    )
    
    return {
        "league_info": league_info,
        "users": users_data,
    }

async def fetch_matchups_up_to_week(league_id: str, current_week: int):
    """
    Helper to concurrently fetch matchup data from week 1 to current_week.
    
    Returns: A list of matchup data for each week.
    """
    tasks = [client.get_matchups(league_id, wk) for wk in range(1, current_week + 1)]
    matchups = await asyncio.gather(*tasks)
    return matchups
        
        
async def fetch_projections_up_to_week(season: str, current_week: int):
    """
    Helper to concurrently fetch projection data from week 1 to current_week.
    Returns: A list or dictionary of projections mapped by week.
    """
    tasks = [client.get_weekly_projections(season, wk) for wk in range(1, current_week + 1)]
    projections = await asyncio.gather(*tasks)
    return projections

def format_df_to_json(df: pd.DataFrame):
    """
    Helper to safely convert a Pandas DataFrame into a List of Dictionaries
    so FastAPI can return it as JSON to the frontend.
    """
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
    
    record_df = get_true_record(league_data["users"], rosters_data)
    
    current_matchups = matchups_up_to_week[-1]
    current_projections = projections_to_week[-1]
    projections_df = get_projections(league_data["league_info"], current_matchups, current_projections)
    
    # Generate the final rankings
    ranked_df = get_power_rankings(aggs_df, record_df, projections_df)
    
    # FIX: Return the final output to the frontend formatted as JSON
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
        
    season_df = process_matchups_data(matchup_dfs, total_rosters)    
    
    proj_dfs = []
    for wk_idx, (wk_matchups, wk_projections) in enumerate(zip(matchups_up_to_week, projections_to_week)):
        df = get_projections(league_data["league_info"], wk_matchups, wk_projections)
        df['week'] = wk_idx + 1 
        proj_dfs.append(df)
        
    projections_df = pd.concat(proj_dfs, ignore_index=True)
    
    record_df = get_true_record(league_data["users"], rosters_data)
    
    trend_df = calculate_trend_lines(season_df, record_df, projections_df, target_owner_name)
    
    return format_df_to_json(trend_df)
    

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    
    
    