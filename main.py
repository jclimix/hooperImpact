from all_classes import DataManager, TeamData, PlayerData, MetricsCalculator
import logging

if __name__ == "__main__":

    mode = 'test'

    if mode == 'exp':

        years = range(1977, 2025)
        for year in years:
            DataManager.export_player_metrics(str(year))

    elif mode == 'test':

        # NOTE: Make sure to pass the right variables to each method!

        season = "2022"
        player_name = "Day'Ron Sharpe"

        player_data = PlayerData(season, player_name)
        player_teams = player_data.get_teams()
        logging.info(f"Player teams: {player_teams}")

        team_data = TeamData(season, player_teams)
        team_name = team_data.get_team_names()
        logging.info(f"Team name: {team_name}")

        # metrics
        rs_pcp = MetricsCalculator.calculate_rs_pcp(season, player_name)
        rs_pcp_adjusted = MetricsCalculator.calculate_adjusted_rs_pcp(season, player_name, rs_pcp)
        ps_pcp = MetricsCalculator.calculate_ps_pcp(season, player_name)
        tps = MetricsCalculator.calculate_tps(season, player_teams)
        rs_pim = MetricsCalculator.calculate_rs_pim(season, player_name, rs_pcp)
        ps_pim = MetricsCalculator.calculate_ps_pim(season, player_name, ps_pcp)

        logging.info(f"rsPCP: {rs_pcp}")
        logging.info(f"rsPCP (adjusted): {rs_pcp_adjusted}")
        logging.info(f"psPCP: {ps_pcp}")
        logging.info(f"TPS: {tps}")
        logging.info(f"rsPIM: {rs_pim}")
        logging.info(f"psPIM: {ps_pim}")

    else:
        logging.warning(f"Improper Mode: {mode}")