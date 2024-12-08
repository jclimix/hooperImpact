import duckdb
import pandas as pd
from all_classes import DataManager
import unicodedata
import logging


def normalize_unicode_column(value):
    if isinstance(value, str):
        try:
            return unicodedata.normalize("NFKC", value.encode("latin1").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            return unicodedata.normalize("NFKC", value)
    return value


def normalize_unicode(df):
    for col in df.select_dtypes(include=[object]):
        df[col] = df[col].apply(normalize_unicode_column)
    return df


def convert_season_string(season):
    try:
        start_year, end_year_suffix = season.split("-")
        end_year = str(int(start_year) + 1)
        return end_year
    except ValueError:
        raise ValueError(f"Invalid season format: {season}. Expected format 'YYYY-YY'.")


def create_view(
    view_type, table_name="player_table", player_search=None, team_abbreviation=None
):
    main_select = f"""
        SELECT 
            Player,
            Age,
            Position,
            Teams,
            Games AS "Games Played",
            rsMinutesPlayed AS "Regular Season Minutes Played",
            psMinutesPlayed AS "Postseason Minutes Played",
            rsPER AS "Regular Season PER",
            psPER AS "Postseason PER",
            CAST(rsPCP_Adjusted AS DOUBLE) * 100 AS "Adjusted Regular Season PCP (%)",
            CAST(psPCP AS DOUBLE) * 100 AS "Postseason PCP (%)",
            CAST(TPS AS DOUBLE) * 100 AS "Team Postseason Score",
            rsPIM AS "Regular Season PIM",
            psPIM AS "Postseason PIM"
        FROM {table_name}
    """

    minutes_filter = "WHERE rsMinutesPlayed > 200 AND psMinutesPlayed > 100"
    player_filter = f" AND Player ILIKE '%{player_search}%'" if player_search else ""
    team_filter = (
        f" AND Teams ILIKE '%{team_abbreviation}%'" if team_abbreviation else ""
    )
    guards_filter = " AND Position ILIKE '%G%'"
    forwards_filter = " AND Position ILIKE '%F%'"
    centers_filter = " AND Position ILIKE '%C%'"
    over10_rsPCP = " AND rsPCP_Adjusted > 0.10"
    over20_rsPCP = " AND rsPCP_Adjusted > 0.20"
    over10_psPCP = " AND psPCP > 0.10"
    over20_psPCP = " AND psPCP > 0.20"
    over100_rsPIM = " AND rsPIM > 100"
    over100_psPIM = " AND psPIM > 100"
    range60_99_rsPIM = " AND rsPIM > 60 AND rsPIM < 100"
    range60_99_psPIM = " AND psPIM > 60 AND psPIM < 100"

    views = {
        "raw": f"CREATE VIEW player_metrics_view AS SELECT * FROM {table_name};",
        "default": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter};",
        "player_filter": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {player_filter};",
        "team_filter": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {team_filter};",
        "guards_only": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {guards_filter};",
        "forwards_only": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {forwards_filter};",
        "centers_only": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {centers_filter};",
        "over10_rsPCP": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over10_rsPCP};",
        "over20_rsPCP": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over20_rsPCP};",
        "over10_psPCP": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over10_psPCP};",
        "over20_psPCP": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over20_psPCP};",
        "over100_rsPIM": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over100_rsPIM};",
        "over100_psPIM": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {over100_psPIM};",
        "range60_99_rsPIM": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {range60_99_rsPIM};",
        "range60_99_psPIM": f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {range60_99_psPIM};",
    }

    return views.get(view_type, views["default"])


def get_data(season, view_type="default", player_search=None, team_abbreviation=None):
    file_path = f"player_exports/{season}_player_exports.csv"
    try:
        df = DataManager.load_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        logging.warning(
            f"UnicodeDecodeError encountered. Retrying with 'latin1' encoding: {file_path}"
        )
        df = DataManager.load_csv(file_path, encoding="latin1")

    if df.empty:
        logging.error(f"Failed to load data or data is empty: {file_path}")
        return pd.DataFrame()

    df = normalize_unicode(df)

    con = duckdb.connect(":memory:")
    con.register("player_table", df)

    sql_view = create_view(
        view_type, player_search=player_search, team_abbreviation=team_abbreviation
    )
    con.execute(sql_view)

    result = con.execute("SELECT * FROM player_metrics_view").df()

    con.close()
    return result


if __name__ == "__main__":

    result_df = pd.DataFrame()
    selected_season = "2023-24"
    view_type = "default" # change this to select 'mode' which returns predefined SQL views w/filters
    player_search = ""

    if player_search != "":
        view_type = "player_filter"

    if selected_season != "":
        selected_season = convert_season_string(selected_season)

    logging.info(f"view_type: {view_type}")
    logging.info(f"player_search: {player_search}")

    if selected_season:
        result_df = get_data(selected_season, view_type=view_type, player_search=player_search)
        print(result_df) # this will be passed to an HTML file for live site
