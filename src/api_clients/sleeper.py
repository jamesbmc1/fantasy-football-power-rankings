from numpy import rint
import requests
import json
import os
from pathlib import Path

class SleeperAPIClient:
    def __init__(self, league_id=None):
        self.league_id = league_id
        self.session = requests.Session()
        self.baseurl = "https://api.sleeper.app/v1/"

        #This finds the directory where sleeper.py
        current_file_path = Path(__file__).resolve()

        # This moves up two levels to the project root, then into 'data'
        self.data_dir = current_file_path.parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        

    def _make_request(self, endpoint, cache_filename=None, refresh=False):
        json_data = None
        cache_path = self.data_dir / cache_filename if cache_filename else None

        if cache_filename and not refresh:
            if cache_path.exists():
                try:
                    with open(cache_path, 'r') as cache_file:
                        json_data = json.load(cache_file)
                        print(f"Loaded {cache_filename} from cache")
                        return json_data
                
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"No cache found ({e})")

        url = f"{self.baseurl}{endpoint}"
        response = self.session.get(url)
        response.raise_for_status()
        json_data = response.json()
        print(f"Fetched from API ({endpoint})")

        if cache_filename:
            with open(cache_path, 'w') as cache_file:
                json.dump(json_data, cache_file)

        return json_data
        
    #Get The User Information
    def get_league_users(self, league_id=None, refresh=False):
        target_id = league_id or self.league_id
        endpoint = f"league/{target_id}/users"
        return self._make_request(endpoint, f"users_{target_id}.json", refresh)

    #Get The League Information
    def get_league_info(self, league_id=None, refresh=False):
        target_id = league_id or self.league_id
        endpoint = f"/league/{target_id}"
        return self._make_request(endpoint, f"league_{target_id}.json", refresh)

    #Get The League Rosters
    def get_league_rosters(self, league_id=None, refresh=False):
        target_id = league_id or self.league_id
        endpoint = f"/league/{target_id}/rosters"
        return self._make_request(endpoint, f"rosters_{target_id}.json", refresh)

    #Get The League Matchups
    def get_matchups(self, week, league_id=None, refresh=False):
        target_id = league_id or self.league_id
        endpoint = f"/league/{target_id}/matchups/{week}"
        return self._make_request(endpoint, f"matchups_{target_id}_wk{week}.json", refresh)
    
    # Get all NFL players
    def get_all_nfl_players(self, refresh=False):
        endpoint = "/players/nfl"
        return self._make_request(endpoint, "nfl_players.json", refresh)
    
    # Fetches projections for every NFL player for a specific week.
    def get_weekly_projections(self, season, week, refresh=False):
        endpoint = f"/projections/nfl/regular/{season}/{week}"
        cache_file = f"projections_{season}_wk{week}.json"
        return self._make_request(endpoint, cache_file, refresh)