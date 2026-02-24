import httpx
import asyncio

class SleeperAPIClient:
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.timeout = httpx.Timeout(30.0)
        self.semaphore = asyncio.Semaphore(5)

    async def _fetch(self, endpoint: str):
        async with self.semaphore:
            # Using async with here ensures connections are cleanly closed so we don't leak memory
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/{endpoint}")
                response.raise_for_status()  # Instantly catches any bad responses from Sleeper
                return response.json()

    async def get_league_info(self, league_id: str):
        return await self._fetch(f"league/{league_id}")

    async def get_league_users(self, league_id: str):
        return await self._fetch(f"league/{league_id}/users")

    async def get_league_rosters(self, league_id: str):
        return await self._fetch(f"league/{league_id}/rosters")

    async def get_matchups(self, league_id: str, week: int):
        return await self._fetch(f"league/{league_id}/matchups/{week}")

    async def get_weekly_projections(self, season: str, week: int):
        # Projections use the sport-specific endpoint
        return await self._fetch(f"projections/nfl/{season}/{week}")