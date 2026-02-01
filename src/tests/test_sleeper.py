import pandas as pd
import pytest
from unittest.mock import MagicMock, mock_open, patch 
import json

from src.api_clients.sleeper import SleeperAPIClient

def test_make_request_without_cache_file(tmp_path):
    with patch('src.api_clients.sleeper.requests.Session') as MockSession:

        # Set up Instance
        mock_session_instance = MockSession.return_value

        # Setup up Response
        mock_response = MagicMock()
        mock_response.json.return_value = {"League Name": "Test League"}

        mock_session_instance.get.return_value = mock_response

        client = SleeperAPIClient(league_id="123")
        client.data_dir = tmp_path

        client._make_request('test/endpoint', cache_filename=None, refresh=True)
        
        mock_session_instance.get.assert_called_once_with('https://api.sleeper.app/v1/test/endpoint')


def test_make_request_with_cache_file(tmp_path):
    with patch('src.api_clients.sleeper.requests.Session') as MockSession:

        mock_instance = MockSession.return_value
        mock_instance.get.return_value.json.return_value = {"League Name": "Test League"}

        client = SleeperAPIClient(league_id="123")
        client.data_dir = tmp_path
        cache_filename = 'test_cache.json'

        cache_file = tmp_path / cache_filename
        with open(cache_file, "w") as f:
            json.dump({"League Name": "Cached Data"}, f)

        # First call to create the cache
        result = client._make_request('test/endpoint', cache_filename=cache_filename, refresh=False)

        # Ensure the file was created
        assert result == {"League Name": "Cached Data"}

        mock_instance.get.assert_not_called()