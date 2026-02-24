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
    async def get_league_users(self, league_id: str):
       return await self._fetch(f"league/{league_id}/users")
            
    # 2. Pass league_id as an argument
    async def get_league_info(self, league_id: str):
        return await self._fetch(f"league/{league_id}")
        
    # 3. Pass league_id as an argument
    async def get_league_rosters(self, league_id: str):
        return await self._fetch(f"league/{league_id}/rosters")

    # 4. Pass league_id AND week
    async def get_matchups(self, league_id: str, week: int):
        return await self._fetch(f"league/{league_id}/matchups/{week}")
    
    # 5. Pass season AND week (Also removed the leading slash bug)
    async def get_weekly_projections(self, season: str, week: int):
        return await self._fetch(f"projections/nfl/regular/{season}/{week}")