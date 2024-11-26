import pandas as pd
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(funcName)s - %(message)s',
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

    @staticmethod
    def export_player_metrics(season):
        file_path = f"nba_data/nba_player_info/{season}_all_player_info.csv"
        player_data = DataManager.load_csv(file_path)

        if player_data.empty or 'Player' not in player_data.columns:
            logging.error(f"No valid player data found in {file_path}.")
            return

        export_data = []

        # track processed players to avoid duplicates
        processed_players = set()

        for _, row in player_data.iterrows():
            player_name = row['Player']
            if player_name in processed_players:
                continue  # skip all duplicate players

            processed_players.add(player_name)
            logging.info(f"Processing metrics for player: {player_name}")

            try:
                player_obj = PlayerData(season, player_name)

                player_teams = player_obj.get_teams()

                age, position = None, None
                games_played, minutes_played = 0, 0
                reg_per, post_per = None, None

                for team in player_teams:
                    reg_file_path = f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_reg.csv"
                    post_file_path = f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_post.csv"

                    reg_data = DataManager.load_csv(reg_file_path)
                    post_data = DataManager.load_csv(post_file_path)

                    if not reg_data.empty:
                        try:
                            # get player data from regular season
                            reg_row = reg_data.loc[reg_data['Player'] == player_name].iloc[0]
                            age = reg_row.get('Age', age)
                            position = reg_row.get('Pos', position)
                            games_played += reg_row.get('G', 0)
                            minutes_played += reg_row.get('MP', 0)
                            reg_per = reg_row.get('PER', reg_per)
                        except IndexError:
                            logging.warning(f"{player_name} not found in {team} regular season stats.")

                    if not post_data.empty:
                        try:
                            # get player data from postseason 
                            post_row = post_data.loc[post_data['Player'] == player_name].iloc[0]
                            post_per = post_row.get('PER', post_per)
                        except IndexError:
                            logging.warning(f"{player_name} not found in {team} postseason stats.")

                # custom metrics
                rs_pcp = MetricsCalculator.calculate_rs_pcp(season, player_name)
                rs_pcp_adjusted = MetricsCalculator.calculate_adjusted_rs_pcp(season, player_name, rs_pcp)
                ps_pcp = MetricsCalculator.calculate_ps_pcp(season, player_name)
                tps = MetricsCalculator.calculate_tps(season, player_teams)
                rs_pim = MetricsCalculator.calculate_rs_pim(season, player_name, rs_pcp)
                ps_pim = MetricsCalculator.calculate_ps_pim(season, player_name, ps_pcp)

                # convert lists to strings or floats
                rs_pcp_str = ', '.join(map(str, rs_pcp))
                ps_pcp_str = ', '.join(map(str, ps_pcp))

                export_data.append({
                    "Player": player_name,
                    "Age": age,
                    "Position": position,
                    "Teams": ', '.join(player_teams),
                    "Games Played": games_played,
                    "Minutes Played": minutes_played,
                    "Regular Season PER": reg_per,
                    "Postseason PER": post_per,
                    "rsPCP": rs_pcp_str,
                    "rsPCP_Adjusted": rs_pcp_adjusted,
                    "psPCP": ps_pcp_str,
                    "TPS": tps,
                    "rsPIM": rs_pim,
                    "psPIM": ps_pim
                })

            except Exception as e:
                logging.error(f"Error processing metrics for player {player_name}: {e}")
                continue

        export_df = pd.DataFrame(export_data)

        print(export_df)

        export_path = f"player_exports/{season}_player_exports.csv"
        try:
            export_df.to_csv(export_path, index=False)
            logging.info(f"Exported player metrics to {export_path}.")
        except Exception as e:
            logging.error(f"Error exporting player metrics to {export_path}: {e}")

class TeamData:
    def __init__(self, season, abbreviations):
        self.season = season
        self.abbreviations = abbreviations  # *should* be a list of teams using abbreviation as identifiers
        self.team_info = self._load_team_info()

    def _load_team_info(self):
        all_team_info = []
        for abbreviation in self.abbreviations:
            file_path = f"nba_data/nba_team_data/{self.season}_{abbreviation}_teamdata/{self.season}_{abbreviation}_info.csv"
            try:
                team_data = DataManager.load_csv(file_path)
                all_team_info.append(team_data)
            except FileNotFoundError:
                logging.error(f"File not found for team {abbreviation} in season {self.season}.")
        return pd.concat(all_team_info, ignore_index=True) if all_team_info else pd.DataFrame()

    def get_team_names(self):
        team_names = []
        for abbreviation in self.abbreviations:
            try:
                team_name = self.team_info.loc[
                    self.team_info['TeamAbbreviation'] == abbreviation, 'TeamName'
                ].iloc[0]
                team_names.append(team_name)
            except IndexError:
                logging.error(f"Team abbreviation {abbreviation} not found in team info data.")
                team_names.append(None)
        return team_names

    def get_records(self):
        records = []
        logging.info(f"Getting records for all team abbreviations: {self.abbreviations}")
        for abbreviation in self.abbreviations:
            try:
                wins = self.team_info.loc[
                    self.team_info["TeamAbbreviation"] == abbreviation, "Wins"
                ].values[0]
                losses = self.team_info.loc[
                    self.team_info["TeamAbbreviation"] == abbreviation, "Losses"
                ].values[0]
                records.append((wins, losses))
            except IndexError:
                logging.error(f"Team record not found for {abbreviation} in {self.season}.")
                records.append((0, 0))
        return records

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
        
    # return list of games played by a player for EACH team    
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
    def calculate_tps(season, teams_list):
        if isinstance(teams_list, str):
            teams_list = [teams_list]
            
        if not teams_list:
            logging.error("The given teams list is empty.")
            return 0

        last_team_abbreviation = teams_list[-1]
        logging.info(f"Calculating TPS for {last_team_abbreviation} in {season}.")

        team_data = TeamData(season, [last_team_abbreviation])
        team_name = team_data.get_team_names()[-1] 

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

            # check for first-round bye
            if R1_Wins == 0 and R1_Losses == 0:
                logging.info(f"{team_name} had a first-round bye in {season}.")

                # adjust for bye: start from the second round
                total_games_played = (R2_Wins + R2_Losses) + (R3_Wins + R3_Losses) + (R4_Wins + R4_Losses)
                weighted_wins = (R2_Wins * 1.2) + (R3_Wins * 1.4) + (R4_Wins * 1.6)
            else:
                # typical case with no first-round bye
                total_games_played = (R1_Wins + R1_Losses) + (R2_Wins + R2_Losses) + (R3_Wins + R3_Losses) + (R4_Wins + R4_Losses)
                weighted_wins = (R1_Wins * 1.0) + (R2_Wins * 1.2) + (R3_Wins * 1.4) + (R4_Wins * 1.6)

            # determine advancement bonus
            if R4_Wins > R4_Losses:
                advancement_bonus = 3.0  # NBA Champion
            elif R3_Wins > R3_Losses:
                advancement_bonus = 2.0  # Reached NBA Finals
            elif R2_Wins > R2_Losses:
                advancement_bonus = 1.0  # Reached Conference Finals
            else:
                advancement_bonus = 0.0  # Eliminated in First Round

            tps = (weighted_wins + advancement_bonus) / (total_games_played + 4)  # add 4 for normalization
            return round(tps, 3)

        logging.error(f"Team {team_name} not found in postseason data.")
        # teams not found means they did not qualify for the postseason and receive a TPS of zero
        return 0

    # calculate regular season Player Contribution Percentage (rsPCP): measure of individual player's statistical contribution to their team(s) in regular season
    @staticmethod
    def calculate_rs_pcp(season, player_name):
        logging.info(f"Calculating rsPCP for {player_name} in {season}.")
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
        logging.info(f"Calculating psPCP for {player_name} in {season}.")
        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()

        if not player_teams:
            logging.warning(f"No teams found for {player_name} in {season}. Returning psPCP list with 0.")
            return [0]

        player_per_list = []
        team_per_sum_list = []

        for team in player_teams:
            file_path = f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_post.csv"
            team_adv_stats_df = DataManager.load_csv(file_path)

            if team_adv_stats_df.empty:
                logging.warning(f"Advanced postseason stats file for team {team} not found. Skipping.")
                continue

            try:
                # get player's PER
                player_per = team_adv_stats_df.loc[
                    team_adv_stats_df["Player"] == player_name, "PER"
                ]
                if not player_per.empty:
                    player_per_list.append(player_per.values[0])
                else:
                    logging.warning(f"{player_name} not found in {team}'s postseason stats for {season}.")
                    player_per_list.append(0)

                # get team's total PER for players with over 100 minutes played
                team_per_sum = team_adv_stats_df.loc[
                    team_adv_stats_df["MP"] > 100, "PER"
                ].sum()
                team_per_sum_list.append(round(team_per_sum, 1))
            except KeyError:
                logging.error(f"'PER' column not found in {team} postseason stats file for {season}.")
            except IndexError:
                logging.error(f"{player_name} not found in {team}'s stats. Skipping team {team}.")

        if not player_per_list:
            logging.error(f"No postseason PER data found for {player_name}. Returning psPCP list with 0.")
            return [0]

        if not team_per_sum_list:
            logging.error(f"No team PER data found for teams in {player_name}'s postseason. Returning psPCP list with 0.")
            return [0]

        player_pcp_list = [
            round(player_per / team_sum, 3) if team_sum > 0 else 0
            for player_per, team_sum in zip(player_per_list, team_per_sum_list)
        ]

        # log PCP breakdown for debugging
        for i, team in enumerate(player_teams):
            if i < len(player_pcp_list):
                logging.debug(
                    f"{player_name}'s PCP for {team}: {round(player_pcp_list[i] * 100, 1)}%"
                )

        # if PCP is NaN then return list with 0

        for pcp in player_pcp_list:
            if np.isnan(pcp):
                return [0]
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
            team_data = TeamData(season, [team])
            records = team_data.get_records()
            if records:
                wins, losses = records[0]
            else:
                wins, losses = 0, 0

            if wins + losses == 0:
                logging.error(f"Invalid win/loss record for team {team}. Skipping.")
                team_win_pct_list.append(0)
                continue

            win_pct = wins / (wins + losses)
            team_win_pct_list.append(round(win_pct, 3))

        total_min_played = 0

        for team in player_teams:
            team_data = DataManager.load_csv(f"nba_data/nba_team_data/{season}_{team}_teamdata/{season}_{team}_advanced_reg.csv")
            min_played = team_data.loc[team_data["Player"] == player_name, "MP"]
            total_min_played += float(min_played.iloc[0])
            
        if float(total_min_played) < 200:
            logging.warning(f"Player has played less than 200 regular season minutes ({total_min_played} minutes).")
            logging.warning(f"Returning an rsPIM of 0.")
            return 0

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
        
        if len(pcp_list) == 0:
            logging.warning(f"The length of the passed PCP list is 0, meaning the player given did not play in the {season} postseason.\nReturning 0 for psPIM.")
            return 0

        if not pcp_list or len(pcp_list) != len(player_teams):
            logging.error(
                f"Mismatch between PCP list length ({len(pcp_list)}) and teams ({len(player_teams)})."
            )
            return 0
        
        player_postseason_team = player_teams[-1]
        postseason_data = DataManager.load_csv(f"nba_data/nba_team_data/{season}_{player_postseason_team}_teamdata/{season}_{player_postseason_team}_advanced_post.csv")
        player_min_played = postseason_data.loc[postseason_data["Player"] == player_name, "MP"]
        
        if float(player_min_played.iloc[0]) < 100:
            logging.warning(f"Player has played less than 100 postseason minutes ({player_min_played} minutes).")
            logging.warning(f"Returning a psPIM of 0.")
            return 0

        # identify the player's last team in list since that will be the team they're on during the postseason
        postseason_team = player_teams[-1]
        logging.info(f"Postseason team for {player_name}: {postseason_team}")

        tps = MetricsCalculator.calculate_tps(season, postseason_team)
        if tps == 0:
            logging.warning(f"TPS for {postseason_team} in {season} is 0. Returning 0 for psPIM.")
            return 0

        # calculate PIM using the player's PCP for the last team
        pim = pcp_list[-1] * tps * 1000
        return round(pim, 1)
    
    def calculate_adjusted_rs_pcp(season, player_name, pcp_list):
        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()
        player_games_played_list = player_data.get_games_played()
        numerator = 0
        i = 0
        
        for team in enumerate(player_teams):
            numerator_component = pcp_list[i] * player_games_played_list[i]
            numerator += numerator_component
            i += 1

        denominator = sum(player_games_played_list)

        if denominator == 0:
            logging.error("No games played across all teams. Cannot calculate adjusted rsPCP.")
            return 0

        rs_pcp_adjusted = numerator / denominator
        return round(rs_pcp_adjusted, 3)