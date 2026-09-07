"""HTTP routes over a shared, regular-season analytics pipeline."""
import httpx
import pandas as pd
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from src.api_clients.sleeper import SleeperAPIClient
from src.services.analytics import load_analytics, records
from src.utils.calculations import calculate_rival_standings

load_dotenv()
app = FastAPI(title='Fantasy Football Power Rankings API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173',
                   'https://fantasy-football-power-rankings-black.vercel.app'],
    allow_credentials=True, allow_methods=['GET'], allow_headers=['*'],
)
client = SleeperAPIClient()


async def league_snapshot(league_id, week):
    try:
        return await load_analytics(client, league_id, week)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(404, 'League or score data not found on Sleeper.') from exc
        raise HTTPException(502, 'Sleeper could not return league data. Please try again.') from exc
    except httpx.RequestError as exc:
        raise HTTPException(503, 'Sleeper is temporarily unreachable. Please try again.') from exc


@app.get('/analytics/{league_id}/{week}')
async def fetch_analytics(league_id: str = Path(pattern=r'^\d+$'), week: int = Path(ge=1, le=18)):
    return await league_snapshot(league_id, week)


# Retain existing API URLs, but route all calculations through the same snapshot.
@app.get('/rankings/{league_id}/{week}')
async def fetch_rankings(league_id: str = Path(pattern=r'^\d+$'), week: int = Path(ge=1, le=18)):
    return (await league_snapshot(league_id, week))['rankings']


@app.get('/trends/{league_id}/{target_owner_name}/{week}')
async def fetch_team_trends(target_owner_name: str, league_id: str = Path(pattern=r'^\d+$'), week: int = Path(ge=1, le=18)):
    data = await league_snapshot(league_id, week)
    teams = [t for t in data['rankings'] if t['owner_name'] == target_owner_name]
    if not data['rankings']:
        return []
    if not teams:
        raise HTTPException(404, 'Manager not found in this league.')
    if len(teams) > 1:
        raise HTTPException(409, 'Multiple teams share this manager name. Open a roster from the rankings page.')
    rid = teams[0]['roster_id']
    return [{k: row[k] for k in ['week', 'rank', 'power_index']} for row in data['history'] if row['roster_id'] == rid]


@app.get('/standings/{league_id}/{week}/{user_roster_id}/{target_roster_id}')
async def fetch_standings(user_roster_id: int, target_roster_id: int,
                          league_id: str = Path(pattern=r'^\d+$'), week: int = Path(ge=1, le=18)):
    if user_roster_id == target_roster_id:
        raise HTTPException(422, 'Choose two different managers.')
    data = await league_snapshot(league_id, week)
    names = {t['roster_id']: t['owner_name'] for t in data['rankings']}
    if not names:
        return {'regular': [], 'all_play': [], 'rivals': []}
    if user_roster_id not in names or target_roster_id not in names:
        raise HTTPException(404, 'Selected roster not found in this league.')
    rivalry = calculate_rival_standings(pd.DataFrame(data['weekly_scores']), user_roster_id, target_roster_id)
    rivalry['owner_name'] = names[user_roster_id]
    rivalry['rival_name'] = names[target_roster_id]
    return {'regular': data['regular'], 'all_play': data['all_play'], 'rivals': records(rivalry)}


if __name__ == '__main__':
    uvicorn.run('src.app:app', host='0.0.0.0', port=8000, reload=True)
