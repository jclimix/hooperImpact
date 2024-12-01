import pandas as pd
from unittest.mock import patch
from all_classes import TeamData

# Test: Initialize TeamData and verify attributes
def test_team_data_initialization():
    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)
    
    assert team_data.season == season
    assert team_data.abbreviations == abbreviations
    assert isinstance(team_data.team_info, pd.DataFrame)

# Test: _load_team_info loads data
@patch("all_classes.DataManager.load_csv")
def test_load_team_info_success(mock_load_csv):
    mock_df_lal = pd.DataFrame({"TeamAbbreviation": ["LAL"], "TeamName": ["Los Angeles Lakers"], "Wins": [50], "Losses": [32]})
    mock_df_bos = pd.DataFrame({"TeamAbbreviation": ["BOS"], "TeamName": ["Boston Celtics"], "Wins": [48], "Losses": [34]})
    
    mock_load_csv.side_effect = [mock_df_lal, mock_df_bos]

    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    expected_df = pd.concat([mock_df_lal, mock_df_bos], ignore_index=True)
    pd.testing.assert_frame_equal(team_data.team_info, expected_df)
    assert mock_load_csv.call_count == 2

# Test: _load_team_info handles missing files
@patch("all_classes.DataManager.load_csv", side_effect=FileNotFoundError)
def test_load_team_info_file_not_found(mock_load_csv):
    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    assert team_data.team_info.empty
    assert mock_load_csv.call_count == len(abbreviations)

# Test: get_team_names returns correct team names
@patch("all_classes.TeamData._load_team_info")
def test_get_team_names(mock_load_team_info):
    mock_team_info = pd.DataFrame({
        "TeamAbbreviation": ["LAL", "BOS"],
        "TeamName": ["Los Angeles Lakers", "Boston Celtics"]
    })
    mock_load_team_info.return_value = mock_team_info

    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    team_names = team_data.get_team_names()
    assert team_names == ["Los Angeles Lakers", "Boston Celtics"]

# Test: get_team_names handles missing team data
@patch("all_classes.TeamData._load_team_info")
def test_get_team_names_missing_data(mock_load_team_info):
    mock_team_info = pd.DataFrame({
        "TeamAbbreviation": ["LAL"],
        "TeamName": ["Los Angeles Lakers"]
    })
    mock_load_team_info.return_value = mock_team_info

    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    team_names = team_data.get_team_names()
    assert team_names == ["Los Angeles Lakers", None]

# Test: get_records returns correct win-loss records
@patch("all_classes.TeamData._load_team_info")
def test_get_records(mock_load_team_info):
    mock_team_info = pd.DataFrame({
        "TeamAbbreviation": ["LAL", "BOS"],
        "Wins": [50, 48],
        "Losses": [32, 34]
    })
    mock_load_team_info.return_value = mock_team_info

    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    records = team_data.get_records()
    assert records == [(50, 32), (48, 34)]

# Test: get_records handles missing win-loss data
@patch("all_classes.TeamData._load_team_info")
def test_get_records_missing_data(mock_load_team_info):
    mock_team_info = pd.DataFrame({
        "TeamAbbreviation": ["LAL"],
        "Wins": [50],
        "Losses": [32]
    })
    mock_load_team_info.return_value = mock_team_info

    season = "2024"
    abbreviations = ["LAL", "BOS"]
    team_data = TeamData(season, abbreviations)

    records = team_data.get_records()
    assert records == [(50, 32), (0, 0)]  # Default to (0, 0) for missing data
