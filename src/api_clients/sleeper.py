from numpy import rint
import requests
import json
import os
import time
import sys
import httpx
from fastapi import HTTPException

class SleeperAPIClient:
    def __init__(self):
        
        self.base_url = "https://api.sleeper.app/v1/"
        self.league_id = os.getenv("SLEEPER_LEAGUE_ID")
        self.season = os.getenv("SEASON")
        self.players_file = "nfl_players_cache.json"
        
    async def _fetch(self, endpoint: str):
        url = f"{self.base_url}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as exc:
                # This handles the "Response came back, but it was an error"
                error_msg = f"Sleeper API Error: {exc.response.text}"
                status = exc.response.status_code
                
                if status == 404:
                    raise HTTPException(status_code=404, detail=f"Resource not found at {endpoint}")
                
                raise HTTPException(status_code=status, detail=error_msg)

            except httpx.RequestError as exc:
                # This handles "No Internet" or "DNS Failed"
                raise HTTPException(status_code=503, detail=f"Network Error: {str(exc)}")
        
        
    #Get The User Information
    async def get_league_users(self):
       return await self._fetch(f"league/{self.league_id}/users")
            

    #Get The League Information
    async def get_league_info(self):
        return await self._fetch(f"league/{self.league_id}")
        

    #Get The League Rosters
    async def get_league_rosters(self):
        return await self._fetch(f"league/{self.league_id}/rosters")

    #Get The League Matchups
    async def get_matchups(self, week: int):
        return await self._fetch(f"league/{self.league_id}/matchups/{week}")
    
    # Fetches projections for every NFL player for a specific week.
    async def get_weekly_projections(self, week: int):
        return await self._fetch(f"/projections/nfl/regular/{self.season}/{week}")
    
    # # Get all NFL players
    # async def get_all_nfl_players(self):
    #     is_fresh = False
        
    #     if os.path.exists(self.players_file):
    #         file_age = time.time() - os.path.getmtime(self.players_file)
            
    #         # Less than 3 days old
    #         if file_age < 259200:
    #             is_fresh = True

    #     if is_fresh:
    #         print("Loading players from local cache (Fresh < 3 days)...")
    #         with open(self.players_file, 'r') as f:
    #             return json.load(f)
        
    #     print("Fetching players from Sleeper API (this takes a moment)...")
    #     data = await self._fetch("players/nfl")
        
    #     with open(self.players_file, 'w') as f:
    #         json.dump(data, f)
            
    #     return data