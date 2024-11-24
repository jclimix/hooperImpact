import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


class DataManager:
    @staticmethod
    def load_csv(file_path):
        try:
            return pd.read_csv(file_path)
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {e}")
            return pd.DataFrame()

# class for handling team-level data
class TeamData:
    def __init__(self, season, abbreviation):
        self.season = season
        self.abbreviation = abbreviation
        self.team_info = self._load_team_info()

    def _load_team_info(self):
        file_path = f"nba_data/nba_team_data/{self.season}_{self.abbreviation}_teamdata/{self.season}_{self.abbreviation}_info.csv"
        return DataManager.load_csv(file_path)

    def get_team_name(self):
        try:
            return self.team_info.loc[
                self.team_info['TeamAbbreviation'] == self.abbreviation, 'TeamName'
            ].iloc[0]
        except IndexError:
            logging.error(f"Team abbreviation {self.abbreviation} not found in team info data.")
            return None

    def get_record(self):
        try:
            wins = self.team_info.loc[self.team_info["TeamAbbreviation"] == self.abbreviation, "Wins"].values[0]
            losses = self.team_info.loc[self.team_info["TeamAbbreviation"] == self.abbreviation, "Losses"].values[0]
            return wins, losses
        except IndexError:
            logging.error(f"Team record not found for {self.abbreviation} in {self.season}.")
            return 0, 0

# class for handling player-level data
class PlayerData:
    def __init__(self, season, player_name):
        self.season = season
        self.player_name = player_name
        self.player_info = self._load_player_info()

    def _load_player_info(self):
        file_path = f"nba_data/nba_player_info/{self.season}_all_player_info.csv"
        return DataManager.load_csv(file_path)

    def get_player_id(self):
        try:
            return self.player_info.loc[
                self.player_info['Player'] == self.player_name, 'ID'
            ].iloc[0]
        except IndexError:
            logging.error(f"Player {self.player_name} not found in {self.season} player data.")
            return "IDNotFound"

    def get_teams(self):
        player_id = self.get_player_id()
        if player_id == "IDNotFound":
            return []
        try:
            teams = self.player_info.loc[self.player_info['ID'] == player_id, 'Team'].unique().tolist()
            return [team for team in teams if not team.endswith("TM")]
        except KeyError:
            logging.error(f"Team data not found for {self.player_name} in {self.season}.")
            return []
        
    # return list of games played by a player for each team    
    def get_games_played(self):
        logging.info(f"Getting games played for {self.player_name} in {self.season}.")
        player_games_list = []

        player_teams = self.get_teams()
        if not player_teams:
            logging.warning(f"No teams found for {self.player_name}. Returning empty games list.")
            return player_games_list

        for team in player_teams:
            file_path = f"nba_data/nba_team_data/{self.season}_{team}_teamdata/{self.season}_{team}_advanced_reg.csv"
            team_adv_stats_df = DataManager.load_csv(file_path)

            if team_adv_stats_df.empty:
                logging.warning(f"Advanced stats file for team {team} not found. Skipping.")
                continue

            try:
                games_played = team_adv_stats_df.loc[
                    team_adv_stats_df["Player"] == self.player_name, "G"
                ].values[0]
                player_games_list.append(games_played)
            except IndexError:
                logging.warning(f"{self.player_name} not found in {team} advanced stats.")
            except KeyError:
                logging.error(f"'G' column not found in {team} advanced stats file.")

        return player_games_list

# class for calculating custom metrics using player and team data above
class MetricsCalculator:

    # calculate Team Postseason Score (TPS): measures team's performance in postseason tournament
    @staticmethod
    def calculate_tps(season, team_abbreviation):
        team_data = TeamData(season, team_abbreviation)
        team_name = team_data.get_team_name()
        postseason_data = DataManager.load_csv(f"nba_data/nba_playoffs_data/{season}_playoff_data.csv")

        if team_name in postseason_data["Team"].values:
            R1_Wins = postseason_data.loc[postseason_data["Team"] == team_name, "R1_Wins"].values[0]
            R1_Losses = postseason_data.loc[postseason_data["Team"] == team_name, "R1_Losses"].values[0]
            R2_Wins = postseason_data.loc[postseason_data["Team"] == team_name, "R2_Wins"].values[0]
            R2_Losses = postseason_data.loc[postseason_data["Team"] == team_name, "R2_Losses"].values[0]
            R3_Wins = postseason_data.loc[postseason_data["Team"] == team_name, "R3_Wins"].values[0]
            R3_Losses = postseason_data.loc[postseason_data["Team"] == team_name, "R3_Losses"].values[0]
            R4_Wins = postseason_data.loc[postseason_data["Team"] == team_name, "R4_Wins"].values[0]
            R4_Losses = postseason_data.loc[postseason_data["Team"] == team_name, "R4_Losses"].values[0]

            all_rounds_losses = [R1_Losses, R2_Losses, R3_Losses, R4_Losses]
            tps = 0

            # calculate TPS based on season due to different postseason formats across eras
            if int(season) in range(1975, 1983):
                tps = 2.2 + (R1_Wins + R2_Wins * 1.2 + R3_Wins * 1.4 + R4_Wins * 1.6) - sum(all_rounds_losses)
            elif int(season) in range(1984, 2002):
                tps = 3.2 + (R1_Wins + R2_Wins * 1.2 + R3_Wins * 1.4 + R4_Wins * 1.6) - sum(all_rounds_losses)
            elif int(season) >= 2003:
                tps = 4.2 + (R1_Wins + R2_Wins * 1.2 + R3_Wins * 1.4 + R4_Wins * 1.6) - sum(all_rounds_losses)
            else:
                logging.error(f"Season ({season}) out of range.")

            return round(tps, 1)

        logging.error(f"Team {team_name} not found in postseason data.")
        return 0

    # calculate Team Postseason Percentage (TPP): expresses team's postseason performance as a percentage (TPS / maximum TPS possible)
    @staticmethod
    def calculate_tpp(season, tps):

        # TPP calculations vary by era due to different postseason formats
        if tps:
            if int(season) in range(1975, 1983):
                return round(tps / 23, 3)
            elif int(season) in range(1984, 2002):
                return round(tps / 24, 3)
            elif int(season) >= 2003:
                return round(tps / 25, 3)
        logging.error(f"TPS value is missing or season ({season}) is out of range.")
        return None

    # calculate regular season Player Contribution Percentage (rsPCP): measure of individual player's statistical contribution to their team(s) in regular season
    @staticmethod
    def calculate_rs_pcp(season, player_name):
        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()
        player_per_list = []
        team_per_sum_list = []

        for team in player_teams:
            team_stats = DataManager.load_csv(f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_reg.csv")
            try:
                player_per = team_stats.loc[team_stats["Player"] == player_name, "PER"].values[0]
                team_per_sum = team_stats.loc[team_stats["MP"] > 100, "PER"].sum()
                player_per_list.append(player_per)
                team_per_sum_list.append(team_per_sum)
            except IndexError:
                logging.warning(f"Player {player_name} not found in team stats for {team}.")
            except KeyError:
                logging.error(f"'PER' column not found in {team} stats.")

        player_pcp_list = [
            round(player_per / team_sum, 3)
            for player_per, team_sum in zip(player_per_list, team_per_sum_list)
        ]
        return player_pcp_list

    # calculate postseason Player Contribution Percentage (psPCP): measure of individual player's statistical contribution to their team(s) in postseason tournament
    @staticmethod
    def calculate_ps_pcp(season, player_name):
        """
        Calculate postseason Player Contribution Percentage (psPCP) for a given player and season.
        """
        logging.info(f"Calculating psPCP for {player_name} in {season}.")
        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()

        if not player_teams:
            logging.warning(f"No teams found for {player_name} in {season}. Returning empty psPCP list.")
            return []

        player_per_list = [] 
        team_per_sum_list = [] 

        for team in player_teams:
            file_path = f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_post.csv"
            team_adv_stats_df = DataManager.load_csv(file_path)

            if team_adv_stats_df.empty:
                logging.warning(f"Advanced postseason stats file for team {team} not found. Skipping.")
                continue

            try:
                player_per = team_adv_stats_df.loc[
                    team_adv_stats_df["Player"] == player_name, "PER"
                ]

                # Calculate sum of team PER for players with over 100 minutes played to exclude outliers/smaller sample of player performances
                team_per_sum = team_adv_stats_df.loc[
                    team_adv_stats_df["MP"] > 100, "PER"
                ].sum()

                if not player_per.empty:
                    player_per_list.append(player_per.values[0])
                    team_per_sum_list.append(round(team_per_sum, 1))
                else:
                    logging.error(f"{player_name} not found in {team}'s postseason stats for {season}.")
            except KeyError:
                logging.error(f"'PER' column not found in {team} postseason stats file for {season}.")
            except IndexError:
                logging.error(f"{player_name} not found in {team}'s stats. Skipping team {team}.")

        if not player_per_list:
            logging.error(f"No postseason PER data found for {player_name}. Returning empty psPCP list.")
            return []

        player_pcp_list = [
            round(player_per / team_sum, 3)
            for player_per, team_sum in zip(player_per_list, team_per_sum_list)
        ]

        # log PCP breakdown for debugging
        for i, team in enumerate(player_teams):
            if i < len(player_pcp_list):
                logging.debug(
                    f"{player_name}'s PCP for {team}: {round(player_pcp_list[i] * 100, 1)}%"
                )

        return player_pcp_list
    
    # calculate regular-season Player Impact Metric (rsPIM): player's overall impact on their team in the regular season
    @staticmethod
    def calculate_rs_pim(season, player_name, pcp_list):
        logging.info(f"Calculating rsPIM for {player_name} in {season}.")

        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()
        player_games_played = player_data.get_games_played()

        if not player_teams or not player_games_played:
            logging.warning(f"No teams or games data found for {player_name}. Returning 0 for rsPIM.")
            return 0

        if len(player_games_played) != len(player_teams):
            logging.error(
                f"Mismatch between teams ({len(player_teams)}) and games played ({len(player_games_played)})."
            )
            return 0

        team_win_pct_list = []

        # calculate win percentages for each team
        for team in player_teams:
            team_data = TeamData(season, team)
            wins, losses = team_data.get_record()

            if wins + losses == 0:
                logging.error(f"Invalid win/loss record for team {team}. Skipping.")
                team_win_pct_list.append(0)
                continue

            win_pct = wins / (wins + losses)
            team_win_pct_list.append(round(win_pct, 3))

        numerator = 0
        pim_list = []

        # calculate PIM for each team
        for i, team in enumerate(player_teams):
            pim = pcp_list[i] * team_win_pct_list[i] * 1000
            pim_list.append(round(pim, 3))

        # adjust PIM based on games played for each team
        for i, team in enumerate(player_teams):
            numerator_component = pim_list[i] * player_games_played[i]
            numerator += numerator_component

        denominator = sum(player_games_played)

        if denominator == 0:
            logging.error("No games played across all teams. Cannot calculate adjusted rsPIM.")
            return 0

        pim_adjusted = numerator / denominator
        return round(pim_adjusted, 1)
    
    # calculate postseason Player Impact Metric (psPIM): player's overall impact on their team in the postseason
    @staticmethod
    def calculate_ps_pim(season, player_name, pcp_list):
        logging.info(f"Calculating psPIM for {player_name} in {season}.")

        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()

        if not player_teams:
            logging.warning(f"No teams found for {player_name} in {season}. Returning 0 for psPIM.")
            return 0

        if not pcp_list or len(pcp_list) != len(player_teams):
            logging.error(
                f"Mismatch between PCP list length ({len(pcp_list)}) and teams ({len(player_teams)})."
            )
            return 0

        # Identify the player's last postseason team
        postseason_team = player_teams[-1]
        logging.info(f"Postseason team for {player_name}: {postseason_team}")

        tps = MetricsCalculator.calculate_tps(season, postseason_team)
        if tps == 0:
            logging.warning(f"TPS for {postseason_team} in {season} is 0. Returning 0 for psPIM.")
            return 0

        tpp = MetricsCalculator.calculate_tpp(season, tps)
        if tpp is None:
            logging.warning(f"TPP for {postseason_team} in {season} is invalid. Returning 0 for psPIM.")
            return 0

        # Calculate PIM using the player's PCP for the last team
        pim = pcp_list[-1] * tpp * 1000
        return round(pim, 1)

# main-to-be
season = "2015"
player_name = "Stephen Curry"
team_abbreviation = "GSW"

team_data = TeamData(season, team_abbreviation)
team_name = team_data.get_team_name()
logging.info(f"Team name: {team_name}")

player_data = PlayerData(season, player_name)
player_teams = player_data.get_teams()
logging.info(f"Player teams: {player_teams}")

rs_pcp = MetricsCalculator.calculate_rs_pcp(season, player_name)
ps_pcp = MetricsCalculator.calculate_ps_pcp(season, player_name)
tps = MetricsCalculator.calculate_tps(season, team_abbreviation)
tpp = MetricsCalculator.calculate_tpp(season, tps)
rs_pim = MetricsCalculator.calculate_rs_pim(season, player_name, rs_pcp)
ps_pim = MetricsCalculator.calculate_ps_pim(season, player_name, ps_pcp)

# NOTE: Make sure to pass the right variables to each method!

logging.info(f"rsPCP: {rs_pcp}")
logging.info(f"psPCP: {ps_pcp}")
logging.info(f"TPS: {tps}")
logging.info(f"TPP: {tpp}")
logging.info(f"rsPIM: {rs_pim}")
logging.info(f"psPIM: {ps_pim}")
