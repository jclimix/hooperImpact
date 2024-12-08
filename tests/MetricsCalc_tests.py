from unittest.mock import patch
import pandas as pd
from all_classes import MetricsCalculator

# Test: TPS
@patch("all_classes.DataManager.load_csv")
@patch("all_classes.TeamData.get_team_names")
def test_calculate_tps_success(mock_get_team_names, mock_load_csv):
    mock_get_team_names.return_value = ["Los Angeles Lakers"]
    mock_postseason_data = pd.DataFrame({
        "Team": ["Los Angeles Lakers"],
        "R1_Wins": [4], "R1_Losses": [3],
        "R2_Wins": [4], "R2_Losses": [2],
        "R3_Wins": [4], "R3_Losses": [1],
        "R4_Wins": [4], "R4_Losses": [3]
    })
    mock_load_csv.return_value = mock_postseason_data

    season = "2024"
    teams_list = ["LAL"]
    tps = MetricsCalculator.calculate_tps(season, teams_list)

    assert round(tps, 3) == 0.821, f"Expected TPS 0.821, but got {tps}"

# Test: rsPCP
@patch("all_classes.DataManager.load_csv")
@patch("all_classes.PlayerData.get_teams")
def test_calculate_rs_pcp_one_team(mock_get_teams, mock_load_csv):
    mock_get_teams.return_value = ["LAL"]
    mock_lal_stats = pd.DataFrame({
        "Player": ["LeBron James", "Player B"],
        "PER": [30.0, 10.0],
        "MP": [500, 200]  # both players qualify for team PER sum (MP > 100)
    })

    mock_load_csv.return_value = mock_lal_stats

    season = "2024"
    player_name = "LeBron James"
    rs_pcp = MetricsCalculator.calculate_rs_pcp(season, player_name)

    # assert expected rsPCP value
    # LAL: player PER = 30.0, team PER sum = 30.0 + 10.0 = 40.0 --> rsPCP = 30.0 / 40.0 = 0.75
    expected_rs_pcp = [0.75]
    assert rs_pcp == expected_rs_pcp, f"Expected rsPCP {expected_rs_pcp}, but got {rs_pcp}"

# Test: psPCP
@patch("all_classes.DataManager.load_csv")
@patch("all_classes.PlayerData.get_teams")
def test_calculate_rs_pcp_multiple_players(mock_get_teams, mock_load_csv):
    mock_get_teams.return_value = ["LAL"]

    mock_lal_stats = pd.DataFrame({
        "Player": ["LeBron James", "Player B", "Player C"],
        "PER": [30.0, 20.0, 10.0],
        "MP": [500, 300, 150]  # players qualify for team PER sum (MP > 100)
    })

    mock_load_csv.return_value = mock_lal_stats

    season = "2024"
    player_name = "LeBron James"
    rs_pcp = MetricsCalculator.calculate_rs_pcp(season, player_name)

    # assert expected rsPCP value
    # LAL: 
    #   - LeBron’s PER = 30.0
    #   - Team PER sum = 30.0 (LeBron) + 20.0 (Player B) + 10.0 (Player C) = 60.0
    #   - rsPCP = 30.0 / 60.0 = 0.5

    expected_rs_pcp = [0.5]
    assert rs_pcp == expected_rs_pcp, f"Expected rsPCP {expected_rs_pcp}, but got {rs_pcp}"

# Test: rsPIM
@patch("all_classes.TeamData.get_records")
@patch("all_classes.PlayerData.get_games_played")
@patch("all_classes.PlayerData.get_teams")
@patch("all_classes.DataManager.load_csv")
def test_calculate_rs_pim_success(mock_load_csv, mock_get_teams, mock_get_games_played, mock_get_records):
    mock_get_teams.return_value = ["LAL"]

    mock_get_games_played.return_value = [50]

    mock_get_records.return_value = [(30, 20)]  # 30 wins, 20 losses -> win_pct = 30 / (30 + 20) = 0.6

    mock_lal_stats = pd.DataFrame({
        "Player": ["LeBron James"],
        "MP": [600]
    })
    mock_load_csv.return_value = mock_lal_stats

    season = "2024"
    player_name = "LeBron James"
    pcp_list = [0.3] # example PCP

    rs_pim = MetricsCalculator.calculate_rs_pim(season, player_name, pcp_list)

    # assert expected rsPIM value
    # win_pct = 0.6, rsPIM = 0.3 (PCP) * 0.6 (win_pct) * 1000 = 180.0

    expected_rs_pim = 180.0
    assert rs_pim == expected_rs_pim, f"Expected rsPIM {expected_rs_pim}, but got {rs_pim}"

# Test: psPIM
@patch("all_classes.DataManager.load_csv")
@patch("all_classes.PlayerData.get_teams")
@patch("all_classes.MetricsCalculator.calculate_tps")
def test_calculate_ps_pim_success(mock_calculate_tps, mock_get_teams, mock_load_csv):
    mock_get_teams.return_value = ["LAL"]

    mock_postseason_stats = pd.DataFrame({
        "Player": ["LeBron James"],
        "MP": [150]  # played more than 100 minutes
    })
    mock_load_csv.return_value = mock_postseason_stats

    # mock TPS calculation with example value
    mock_calculate_tps.return_value = 1.5

    season = "2024"
    player_name = "LeBron James"
    pcp_list = [0.35]  # Example PCP

    ps_pim = MetricsCalculator.calculate_ps_pim(season, player_name, pcp_list)

    # assert expected psPIM value
    # psPIM = pcp_list[-1] * TPS * 1000 = 0.35 * 1.5 * 1000 = 525.0

    expected_ps_pim = 525.0
    assert ps_pim == expected_ps_pim, f"Expected psPIM {expected_ps_pim}, but got {ps_pim}"

# Test: adjusted rsPCP
@patch("all_classes.PlayerData.get_games_played")
@patch("all_classes.PlayerData.get_teams")
def test_calculate_adjusted_rs_pcp_success(mock_get_teams, mock_get_games_played):
    mock_get_teams.return_value = ["LAL", "MIA"]

    mock_get_games_played.return_value = [50, 30]  # 50 games with LAL, 30 games with MIA

    season = "2024"
    player_name = "LeBron James"
    pcp_list = [0.2, 0.3]  # example PCP values for teams LAL and MIA

    rs_pcp_adjusted = MetricsCalculator.calculate_adjusted_rs_pcp(season, player_name, pcp_list)

    # assert expected adjusted rsPCP value

    # numerator = (0.2 * 50) + (0.3 * 30) = 10 + 9 = 19
    # denominator = 50 + 30 = 80
    # adjusted rsPCP = numerator / denominator = 19 / 80 = 0.237
    
    expected_rs_pcp_adjusted = 0.237
    assert rs_pcp_adjusted == expected_rs_pcp_adjusted, f"Expected adjusted rsPCP {expected_rs_pcp_adjusted}, but got {rs_pcp_adjusted}"