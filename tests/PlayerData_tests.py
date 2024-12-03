import pandas as pd
from unittest.mock import patch
from all_classes import PlayerData

# Test: init PlayerData and verify attributes
def test_player_data_initialization():
    season = "2024"
    player_name = "LeBron James"
    with patch("all_classes.DataManager.load_csv") as mock_load_csv:
        mock_load_csv.return_value = pd.DataFrame()
        player_data = PlayerData(season, player_name)

    assert player_data.season == season
    assert player_data.player_name == player_name
    assert isinstance(player_data.player_info, pd.DataFrame) 


# Test: _load_player_info loads data successfully
@patch("all_classes.DataManager.load_csv")
def test_load_player_info_success(mock_load_csv):
    mock_df = pd.DataFrame({"Player": ["LeBron James"], "ID": [23], "Team": ["LAL"]})
    mock_load_csv.return_value = mock_df

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    pd.testing.assert_frame_equal(player_data.player_info, mock_df)
    mock_load_csv.assert_called_once_with(f"nba_data/nba_player_info/{season}_all_player_info.csv")


# Test: get_player_id returns correct player ID
@patch("all_classes.PlayerData._load_player_info")
def test_get_player_id_success(mock_load_player_info):
    mock_player_info = pd.DataFrame({"Player": ["LeBron James"], "ID": [23]})
    mock_load_player_info.return_value = mock_player_info

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    player_id = player_data.get_player_id()
    assert player_id == 23


# Test: get_player_id handles missing player
@patch("all_classes.PlayerData._load_player_info")
def test_get_player_id_missing_player(mock_load_player_info):
    mock_player_info = pd.DataFrame({"Player": ["Kevin Durant"], "ID": [35]})
    mock_load_player_info.return_value = mock_player_info

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    player_id = player_data.get_player_id()
    assert player_id is None  # should return None if player not found


# Test: get_teams returns correct team list
@patch("all_classes.PlayerData._load_player_info")
def test_get_teams_success(mock_load_player_info):
    mock_player_info = pd.DataFrame({
        "ID": [23, 23],
        "Player": ["LeBron James", "LeBron James"],
        "Team": ["LAL", "MIA"]
    })
    mock_load_player_info.return_value = mock_player_info

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    teams = player_data.get_teams()
    assert teams == ["LAL", "MIA"]


# Test: get_teams handles missing player data
@patch("all_classes.PlayerData._load_player_info")
def test_get_teams_missing_data(mock_load_player_info):
    mock_player_info = pd.DataFrame({"ID": [35], "Player": ["Kevin Durant"], "Team": ["BKN"]})
    mock_load_player_info.return_value = mock_player_info

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    teams = player_data.get_teams()
    assert teams == []  # should return an empty list if player not found

# Test: get_games_played handles missing "G" (games) column
@patch("all_classes.PlayerData.get_teams")
@patch("all_classes.DataManager.load_csv")
def test_get_games_played_missing_column(mock_load_csv, mock_get_teams):
    mock_get_teams.return_value = ["LAL"]

    mock_lal_stats = pd.DataFrame({"Player": ["LeBron James"]})
    mock_load_csv.return_value = mock_lal_stats

    season = "2024"
    player_name = "LeBron James"
    player_data = PlayerData(season, player_name)

    games_played = player_data.get_games_played()
    assert games_played == []  # should return an empty list if "G" column is missing
