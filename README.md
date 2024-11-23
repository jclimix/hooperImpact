Project Outline: HooperImpact
-----------------------------

### 1\. Core Objectives

-   Develop a basketball analytics framework for calculating new player and team metrics called PCP and PIM (for both the regular season and the postseason) that show how impactful individual players actually are towards their team's success. 

-   Create robust functionality to fetch, process, and display player and team statistics.

* * * * *

### 2\. Classes and Objects

Use classes for entities requiring encapsulated data and operations, while keeping simpler processes as standalone functions.

#### 2.1. Key Classes

-   Player

-   Attributes: name, id, team, season, career_stats (DataFrame).

-   Methods:

-   get_metrics(): Fetch player metrics for a specific season.

-   get_best_metrics(): Identify and fetch metrics for a player's best season (highest PER).

-   get_worst_metrics(): Identify and fetch metrics for a player's worst season (lowest PER).

-   get_career_metrics(): Scrape career data from SportsReference website.

-   get_teams(): Determine teams played for in a given season.

-   Team

-   Attributes: name, abbreviation, season, roster (list of Player objects), team_stats (DataFrame).

-   Methods:

-   get_metrics(): Fetch team metrics for a season.

-   get_record(): Retrieve team record.

-   get_postseason_data(): Retrieve postseason performance.

-   MetricsCalculator

-   Attributes: None (static utility class).

-   Methods:

-   calculate_PCP(mode, player_PER, team_PER): Compute Player Contribution Percentage.

-   calculate_PIM(mode, PCP, team_performance_metric): Compute Player Impact Metric.

-   calculate_TPP(team_wins, team_losses, playoff_depth): Compute Team Playoff Percentage.

* * * * *

### 3\. Functions

Use standalone functions for operations not tightly coupled to the above entities.

#### 3.1. Player-Specific Functions

-   match_player(name, season)

-   Purpose: Retrieve player ID based on name and season.

-   Returns: Player ID.

-   scrape_player_table(player_id)

-   Purpose: Scrape player career stats and return as a DataFrame.

-   find_player_PER(stats_table, player_id)

-   Purpose: Calculate and return player's PER for regular/postseason.

#### 3.2. Team-Specific Functions

-   get_team_advanced_stats(season, team_abv)

-   Purpose: Retrieve advanced stats for a team in a given season.

-   Notes: Handles edge cases where a player played for multiple teams.

-   find_team_PER(stats_table)

-   Purpose: Calculate total team PER, filtering out low-minute players.

-   get_team_record(season, team_abv)

-   Purpose: Fetch team's win-loss record for the season.

#### 3.3. Global Functions

-   create_results(player_metrics, team_metrics)

-   Purpose: Generate and structure results for display.

-   generate_leaderboard(year=None)

-   Purpose: Create a leaderboard for all players in a given year or across all years.

* * * * *

### 4\. Data Flow

#### 4.1. Steps for Player Functions

1.  Use player name and season to find player ID (might change).

2.  Scrape career stats using player ID in URL to find team played for during the given season.

3.  Pull corresponding historical stats from S3 bucket; search via team and season.

4.  Pull those teams' advanced stats.

5.  Calculate PER, PCP, and PIM for the player.

6.  Aggregate results for player-level metrics.

#### 4.2. Steps for Team Functions

1.  Retrieve team roster for the season.

2.  Pull team advanced stats.

3.  Calculate PER, PCP, and PIM for each player.

4.  Aggregate results for team-level metrics.

* * * * *

### 5\. Data Storage Schema (S3)

#### 5.1. Folder Structure

-   nba_data (All historical NBA player/team data)

-   nba_team_data (NBA team data with general info and stats per team)

-   {year}_{team}_teamdata

-   {year}_{team}_info.csv (Contains year/season, team name, record, image address for team's logo) ex. 2010_ORL_teamdata.csv

-   {year}_{team}_advanced_reg.csv (Contains team roster along with player name, age, games played, minutes played, other advanced stats including PER) ex. 2010_ORL_advanced_reg.csv

-   {year}_{team}_advanced_post.csv (Contains exact same info as above, but for the postseason) ex. 2010_ORL_advanced_post.csv

-   nba_player_info (Player names and IDs by year)

-   {year}_all_player_info.csv (Contains player name, ID, team played for) ex. 2010_all_player_info.csv

-   nba_playoffs_data (Postseason wins and losses by year).

-   {year}_playoff_data.csv (Contains player name, ID, team played for) ex. 2010_playoff_data.csv

#### 5.2. File Naming Convention

-   Year-specific data organized for ease of retrieval.

-   Example:

-   2010_ATL_advanced.csv

-   2010_all_player_info.csv

* * * * *

### 6\. (Main) Metrics & Formulas

NOTE: Metrics with a red asterisk (*) at the end were created by me and are the "value added" of this project.

#### 6.0.1. PER (Player Efficiency Rating)

Meaning: A metric that combines all of a player's contributions into a single number. [John Hollinger created the PER ](https://www.espn.com/nba/columns/story?columnist=hollinger_john&id=2850240)in 1995 using a complex formula that adds positive stats and subtracts negative ones. The PER is mathematically adjusted so that the league average will always be 15 across every season.

#### 6.1. PCP (Player Contribution Percentage)*

Meaning: Refers to a player's contribution to their team's overall performance expressed as a percent.

For example, let's say LeBron James (when he was on the Cleveland Cavaliers) has a PER of 22 for the 2009-10 season, and the entire Cavaliers team has a PER sum of 178 (including LeBron's). This means LeBron's Player Contribution Percentage would be 22 divided by 178 which is .124 or 12.4%. Since a player's PER is counted separately in the regular season and the postseason, a player can have both a regular season PCP (rsPCP) and a postseason PCP (psPCP).

-   Formulas:

-   rsPCP: regular season PCP

-   rsPCP = Player PER / SUM(Team PER (excluding players with less than 100 total minutes for that year/season))

-   psPCP: postseason PCP

-   psPCP = Player PER / SUM(Team PER (excluding players with less than 2 total games played for that year/season))

6.2. TPS (Team Postseason Score)*

Meaning: Refers to a team's performance in the postseason based on their wins, losses, and the round that each took place in. The score rewards teams for wins, especially as they progress through the rounds while also penalizing losses.

Context: During the NBA postseason (since 1977), there are 4 rounds that take place between the top 16 teams (8 from the Eastern Conference and 8 from the Western Conference) in the postseason. The winner is declared that year/season's champion. These rounds are classified as "First Round", "Conference Semifinals", "Conference Finals", and "Finals". For simplicity, these rounds are referred to as Round 1, 2, 3, and 4 respectively. Teams advance to the next round by winning 4 games before their opponent and, conversely, are eliminated if their opponent reaches 4 wins before them.

-   Formula:

-   TPS = 0.2 + [ (R1 Wins) + (R2 Wins * 1.2) + (R3 Wins * 1.4) + (R4 Wins * 1.6) - Losses ]

-   The base score (minimum possible score) is 0.2 (if a team has no wins and is eliminated in the first round). This is so the maximum score is a whole integer (21) as well as to differentiate players on teams that made it to the postseason from players on teams that didn't qualify (who will have a TPS of 0).

-   The max score (maximum possible score) is 21 (if a team progresses through every round without any losses).

6.3. TPP (Team Postseason Percentage)*

Meaning: Refers to a team's performance in the postseason based on their Team Postseason Score.

-   Formula:\
    TPP = Team Postseason Score / 21

#### 6.4. PIM (Player Impact Metric)*

Meaning: Refers to a player's overall impact on their team based on their individual production without their teammates (using PCP) and team performance (using either win percentage for the regular season or TPP for the postseason).

-   Formula (Regular Season):

-   PIM = PCP × Win_Pct × 1000

-   Formula (Postseason):

-   PIM = PCP × TPP × 1000

Metrics Summary

PCP is a simple measure of a player's production relative to the rest of their team using the already developed metric PER. A player's PCP and their team's win percentage are factored together to create a player's regular season PIM, a measure of a player's overall impact on their team. During the postseason, a player's PCP and their TPP (a measure of a team's performance in the postseason) are used to create the player's postseason PIM.

* * * * *

### 7\. Key Features (subject to change)

-   Player Lookup

-   Search by name and season, display custom metrics and stats.

-   Team Lookup

-   Search by name and season, display roster and aggregated custom metrics.

-   Leaderboards

-   Historical and seasonal rankings sorted by custom metrics.

* * * * *

### 8\. Notes and Edge Cases

-   Handle players who switch teams mid-season.

-   Handle players & teams without postseason data.

-   Handle postseason data across different eras when the format involved less games and less teams.

-   Design code for scalability across multiple seasons and data updates.

-   Emphasis on using CLEARLY DEFINED classes & objects that are loosely coupled.
