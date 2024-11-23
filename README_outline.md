# Project Outline: HooperImpact

## 1. Core Objectives
- Develop a basketball analytics framework for calculating new player and team metrics called **PCP** and **PIM** (for both the regular season and the postseason) that show how impactful individual players actually are towards their team’s success.
- Create robust functionality to fetch, process, and display player and team statistics.

## 2. Classes and Objects
Use classes for entities requiring encapsulated data and operations, while keeping simpler processes as standalone functions.

### 2.1. Key Classes
#### **Player**
- **Attributes**: 
  - `name`
  - `id`
  - `team`
  - `season`
  - `career_stats` (DataFrame)
- **Methods**: 
  - `get_metrics()`: Fetch player metrics for a specific season.
  - `get_best_metrics()`: Identify and fetch metrics for a player’s best season (highest PER).
  - `get_worst_metrics()`: Identify and fetch metrics for a player's worst season (lowest PER).
  - `get_career_metrics()`: Scrape career data from SportsReference website.
  - `get_teams()`: Determine teams played for in a given season.

#### **Team**
- **Attributes**: 
  - `name`
  - `abbreviation`
  - `season`
  - `roster` (list of Player objects)
  - `team_stats` (DataFrame)
- **Methods**: 
  - `get_metrics()`: Fetch team metrics for a season.
  - `get_record()`: Retrieve team record.
  - `get_postseason_data()`: Retrieve postseason performance.

#### **MetricsCalculator**
- **Attributes**: None (static utility class)
- **Methods**: 
  - `calculate_PCP(mode, player_PER, team_PER)`: Compute Player Contribution Percentage.
  - `calculate_PIM(mode, PCP, team_performance_metric)`: Compute Player Impact Metric.
  - `calculate_TPP(team_wins, team_losses, playoff_depth)`: Compute Team Playoff Percentage.

## 3. Functions
Standalone functions for operations not tightly coupled to the above entities.

### 3.1. Player-Specific Functions
- `match_player(name, season)`: 
  - **Purpose**: Retrieve player ID based on name and season.
  - **Returns**: Player ID.

- `scrape_player_table(player_id)`: 
  - **Purpose**: Scrape player career stats and return as a DataFrame.

- `find_player_PER(stats_table, player_id)`: 
  - **Purpose**: Calculate and return player’s PER for regular/postseason.

### 3.2. Team-Specific Functions
- `get_team_advanced_stats(season, team_abv)`:
  - **Purpose**: Retrieve advanced stats for a team in a given season.
  - **Notes**: Handles edge cases where a player played for multiple teams.

- `find_team_PER(stats_table)`:
  - **Purpose**: Calculate total team PER, filtering out low-minute players.

- `get_team_record(season, team_abv)`:
  - **Purpose**: Fetch team’s win-loss record for the season.

### 3.3. Global Functions
- `create_results(player_metrics, team_metrics)`:
  - **Purpose**: Generate and structure results for display.

- `generate_leaderboard(year=None)`:
  - **Purpose**: Create a leaderboard for all players in a given year or across all years.

## 4. Data Flow
### 4.1. Steps for Player Functions
1. Use player name and season to find player ID (might change).
2. Scrape career stats using player ID in URL to find team played for during the given season.
3. Pull corresponding historical stats from S3 bucket; search via team and season.
4. Pull those teams’ advanced stats.
5. Calculate PER, PCP, and PIM for the player.
6. Aggregate results for player-level metrics.

### 4.2. Steps for Team Functions
1. Retrieve team roster for the season.
2. Pull team advanced stats.
3. Calculate PER, PCP, and PIM for each player.
4. Aggregate results for team-level metrics.

## 5. Data Storage Schema (S3)
### 5.1. Folder Structure
- **`nba_data`**: All historical NBA player/team data.
- **`nba_team_data`**: NBA team data with general info and stats per team.
  - `{year}_{team}_teamdata`
  - `{year}_{team}_info.csv`: Year/season, team name, record, logo address (e.g., `2010_ORL_teamdata.csv`).
  - `{year}_{team}_advanced_reg.csv`: Team roster and advanced stats including PER (e.g., `2010_ORL_advanced_reg.csv`).
  - `{year}_{team}_advanced_post.csv`: Postseason data, similar structure to advanced regular stats.

- **`nba_player_info`**: Player names and IDs by year.
  - `{year}_all_player_info.csv`: Player name, ID, team played for (e.g., `2010_all_player_info.csv`).

- **`nba_playoffs_data`**: Postseason wins and losses by year.
  - `{year}_playoff_data.csv`: Player name, ID, team played for.

### 5.2. File Naming Convention
Year-specific data organized for ease of retrieval.
- Example: `2010_ATL_advanced.csv`, `2010_all_player_info.csv`.

## 6. Metrics & Formulas

### 6.1. PCP (Player Contribution Percentage)*
- **Meaning**: A player’s contribution to their team’s performance as a percentage.
- **Formula**:
  - `rsPCP = Player PER / SUM(Team PER)`
  - `psPCP = Player PER / SUM(Team PER)` (Postseason).

### 6.2. TPS (Team Postseason Score)*
- **Meaning**: A score based on postseason wins, losses, and round progression.
- **Formula**:
  - `TPS = 0.2 + [(R1 Wins) + (R2 Wins * 1.2) + (R3 Wins * 1.4) + (R4 Wins * 1.6) - Losses]`.

### 6.3. TPP (Team Postseason Percentage)*
- **Formula**: 
  - `TPP = Team Postseason Score / 21`.

### 6.4. PIM (Player Impact Metric)*
- **Meaning**: Overall player impact on team success.
- **Formulas**:
  - Regular Season: `PIM = PCP × Win_Pct × 1000`.
  - Postseason: `PIM = PCP × TPP × 1000`.

## 7. Key Features (Subject to Change)
- **Player Lookup**: Search by name and season, display custom metrics and stats.
- **Team Lookup**: Search by name and season, display roster and aggregated custom metrics.
- **Leaderboards**: Historical and seasonal rankings sorted by custom metrics.

## 8. Notes and Edge Cases
- Handle players who switch teams mid-season.
- Handle players & teams without postseason data.
- Adapt code to differences in postseason formats across eras.
- Design for scalability across multiple seasons and data updates.
- Emphasize **clear and loosely coupled classes and objects**.
