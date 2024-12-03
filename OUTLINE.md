### Project Outline: HooperImpact

---

## **1. Core Objectives**
- Build a robust basketball analytics framework to evaluate **Player Contribution Percentage (PCP)** and **Player Impact Metric (PIM)**, offering insights into player contributions and team success.
- Leverage historical NBA data to process, calculate, and display advanced player and team metrics for both regular and postseason performance.

---

## **2. Classes and Objects**
### 2.1 **DataManager**
Centralized class for handling file operations and data ingestion, with methods to handle edge cases such as missing files or encoding errors.

- **Attributes**: None
- **Key Methods**:
  - `load_csv(file_path, encoding='utf-8')`: Loads a CSV file with fallback for encoding errors.
  - `export_player_metrics(season)`: Generates and saves player metrics for a given season, handling duplicates and missing data.

### 2.2 **PlayerData**
Handles operations and data retrieval for individual players.

- **Attributes**:
  - `season`: NBA season as a string.
  - `player_name`: Name of the player.
  - `player_info`: DataFrame containing player information.
- **Key Methods**:
  - `_load_player_info()`: Loads player data from CSVs.
  - `get_player_id()`: Fetches player ID.
  - `get_teams()`: Retrieves all teams the player played for in a given season.
  - `get_games_played()`: Fetches games played by the player per team.

### 2.3 **TeamData**
Manages team-level data and associated operations.

- **Attributes**:
  - `season`: NBA season.
  - `abbreviations`: List of team abbreviations.
  - `team_info`: DataFrame containing team details.
- **Key Methods**:
  - `_load_team_info()`: Loads team-specific information.
  - `get_team_names()`: Retrieves full team names based on abbreviations.
  - `get_records()`: Fetches win-loss records for a team.

### 2.4 **MetricsCalculator**
Dedicated to calculating advanced basketball metrics for players and teams.

- **Key Methods**:
  - `calculate_rs_pcp(season, player_name)`: Computes regular season **Player Contribution Percentage**.
  - `calculate_ps_pcp(season, player_name)`: Computes postseason **Player Contribution Percentage**.
  - `calculate_rs_pim(season, player_name, pcp_list)`: Calculates regular season **Player Impact Metric**.
  - `calculate_ps_pim(season, player_name, pcp_list)`: Calculates postseason **Player Impact Metric**.
  - `calculate_tps(season, teams_list)`: Computes **Team Postseason Score (TPS)**.
  - `calculate_adjusted_rs_pcp(season, player_name, pcp_list)`: Adjusts **rsPCP** across multiple teams for a single player.

---

## **3. Functions**
### 3.1 **Player-Specific Functions**
- **`match_player(name, season)`**:
  - Matches a player's name to their ID for a given season.
- **`scrape_player_table(player_id)`**:
  - Scrapes career stats and returns a DataFrame.
- **`find_player_PER(stats_table, player_id)`**:
  - Fetches player’s **PER** for regular or postseason.

### 3.2 **Team-Specific Functions**
- **`get_team_advanced_stats(season, team_abv)`**:
  - Pulls advanced stats for a specific team in a season.
- **`find_team_PER(stats_table)`**:
  - Computes total team PER, filtering out low-minute players.
- **`get_team_record(season, team_abv)`**:
  - Fetches win-loss records for a team.

### 3.3 **Global Functions**
- **`create_results(player_metrics, team_metrics)`**:
  - Structures results for display or export.
- **`generate_leaderboard(year=None)`**:
  - Produces leaderboards for selected seasons.

---

## **4. Data Flow**
### 4.1 **Player Data Workflow**
1. Match player name to ID using `PlayerData`.
2. Retrieve player metrics (regular and postseason).
3. Compute custom metrics (**PCP**, **PIM**) using `MetricsCalculator`.
4. Aggregate results for output.

### 4.2 **Team Data Workflow**
1. Retrieve team stats and roster using `TeamData`.
2. Calculate metrics for individual players.
3. Aggregate metrics to evaluate team-level performance.

---

## **5. Data Storage Schema**
### **5.1 Folder Structure**
- **`nba_data`**: Core NBA data.
  - `nba_player_info`: Player information and statistics.
  - `nba_team_data`: Team statistics and advanced metrics.
  - `nba_playoffs_data`: Postseason results.
- **`player_exports`**: Season-specific player metrics for export.

### **5.2 File Naming Conventions**
- Player info: `{season}_all_player_info.csv`
- Team stats: `{season}_{team}_teamdata.csv`
- Playoff data: `{season}_playoff_data.csv`

---

## **6. Metrics**
### 6.1 **Player Contribution Percentage (PCP)**
- **Meaning**: A player’s contribution to their team’s success based on individual and team PER.
- **Formulas**:
  - `rsPCP = Player_PER / SUM(Team_PER)`
  - `psPCP = Player_PER / SUM(Team_PER)`

### 6.2 **Player Impact Metric (PIM)**
- **Meaning**: Quantifies a player’s impact on team success.
- **Formulas**:
  - Regular Season: `rsPIM = rsPCP × WinPct × 1000`
  - Postseason: `psPIM = psPCP × TPS × 1000`

### 6.3 **Team Postseason Score (TPS)**
- **Meaning**: A weighted measure of postseason performance.
- **Formula**:
  - `TPS = (Weighted Wins + Advancement Bonus) / (Games Played + Normalization Constant)`
