import httpx
import asyncio

class SleeperAPIClient:
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.timeout = httpx.Timeout(30.0)
        self.semaphore = asyncio.Semaphore(5)

    async def _fetch(self, endpoint: str, *, base_url=None):
        async with self.semaphore:
            # Using async with here ensures connections are cleanly closed so we don't leak memory
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{base_url or self.base_url}/{endpoint}")
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
        # This feed is outside /v1 and returns rows, not a player-keyed map.
        payload = await self._fetch(
            f"projections/nfl/{season}/{week}?season_type=regular",
            base_url="https://api.sleeper.com")
        if not isinstance(payload, list):
            raise ValueError("Unexpected Sleeper projection response")
        projections = {}
        for row in payload:
            if not isinstance(row, dict) or row.get('player_id') is None:
                raise ValueError("Projection row is missing a player ID")
            player_id = str(row['player_id'])
            if player_id in projections:
                raise ValueError("Duplicate player projection")
            projections[player_id] = row
        return projections

    async def get_player_week_stats(self, player_id: str, season: str, week: int):
        payload = await self._fetch(
            f"stats/nfl/player/{player_id}?season_type=regular&season={season}&grouping=week",
            base_url="https://api.sleeper.com")
        rows = list(payload.values()) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError('Unexpected actual-stat response')
        matching = [r for r in rows if isinstance(r, dict)
                    and str(r.get('player_id')) == str(player_id)
                    and str(r.get('season')) == str(season)
                    and r.get('week') == week and r.get('season_type') == 'regular'
                    and r.get('category') == 'stat' and r.get('sport') == 'nfl']
        if len(matching) != 1:
            raise ValueError('No unique actual-stat record for the requested player/week')
        return matching[0]

    async def get_nfl_state(self):
        return await self._fetch('state/nfl')
