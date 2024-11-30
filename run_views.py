import duckdb
import pandas as pd
from all_classes import DataManager
import unicodedata
import logging


def normalize_unicode_column(value):
    """
    Normalize a single string value using Unicode normalization.
    """
    if isinstance(value, str):
        try:
            return unicodedata.normalize('NFKC', value.encode('latin1').decode('utf-8'))
        except (UnicodeEncodeError, UnicodeDecodeError):
            return unicodedata.normalize('NFKC', value)
    return value


def normalize_unicode(df):
    """
    Normalize Unicode characters in all string columns of a DataFrame.
    """
    for col in df.select_dtypes(include=[object]):  # Process only string columns
        df[col] = df[col].apply(normalize_unicode_column)
    return df


def create_view(view_type, table_name="player_table", player_search=None, team_abbreviation=None):
    """
    Create a SQL view for player metrics with dynamic view types and optional filtering.
    """
    # Base SELECT query
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
            rsPCP AS "Regular Season PCP",
            CAST(rsPCP_Adjusted AS DOUBLE) * 100 AS "Adjusted Regular Season PCP (%)",
            CAST(psPCP AS DOUBLE) * 100 AS "Postseason PCP (%)",
            CAST(TPS AS DOUBLE) * 100 AS "Total Player Score (%)",
            rsPIM AS "Regular Season PIM",
            psPIM AS "Postseason PIM"
        FROM {table_name}
    """

    # Base filter for minutes
    minutes_filter = """
    WHERE rsMinutesPlayed > 200 AND psMinutesPlayed > 100
    """

    # Optional player search filter
    player_filter = f" AND Player LIKE '%{player_search}%'" if player_search else ""

    # Optional team filter
    team_filter = f" AND Teams LIKE '%{team_abbreviation}%'" if team_abbreviation else ""

    # View definitions
    views = {
        'raw': f"CREATE VIEW player_metrics_view AS SELECT * FROM {table_name};",
        'default': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter};",
        'best_reg_season_PCP': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} ORDER BY rsPCP DESC;",
        'best_postseason_PCP': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} ORDER BY psPCP DESC;",
        'best_reg_season_PIM': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} ORDER BY rsPIM DESC;",
        'best_postseason_PIM': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} ORDER BY psPIM DESC;",
        'player_filter': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {player_filter};",
        'team_filter': f"CREATE VIEW player_metrics_view AS {main_select} {minutes_filter} {team_filter};",
    }

    # Return the SQL statement for the specified view type
    return views.get(view_type, views['default'])


def get_data(season, view_type='default', player_search=None, team_abbreviation=None):
    """
    Load data for a given season, normalize it, and create a SQL view.
    """
    file_path = f"player_exports/{season}_player_exports.csv"
    try:
        # Load CSV with explicit encoding
        df = DataManager.load_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback to a different encoding
        logging.warning(f"UnicodeDecodeError encountered. Retrying with 'latin1' encoding: {file_path}")
        df = DataManager.load_csv(file_path, encoding="latin1")

    if df.empty:
        logging.error(f"Failed to load data or data is empty: {file_path}")
        return

    # Normalize Unicode characters
    df = normalize_unicode(df)

    # Initialize DuckDB connection and register the table
    con = duckdb.connect(":memory:")
    con.register("player_table", df)

    # Create the desired view
    sql_view = create_view(view_type, player_search=player_search, team_abbreviation=team_abbreviation)
    con.execute(sql_view)

    # Query the created view
    result = con.execute("SELECT * FROM player_metrics_view").df()
    print("DuckDB Result:")
    print(result)

    con.close()


# Execute the function with the specified season, view type, player search, and team filter
season = '2024'
view_type = 'player_filter'
player_search = 'Shai'
team_abbreviation = None
get_data(season, view_type, player_search, team_abbreviation)