from process_player_impact import *
import duckdb

def season_to_year(season):
    parts = season.split('-')
    start_year = int(parts[0])
    end_part = parts[1]

    # Handle end part correctly based on century and start year
    if len(end_part) == 2:
        if int(end_part) < int(str(start_year)[2:]):
            # Next century case
            return str(start_year + 100)[:2] + end_part
        else:
            # Same century case
            return str(start_year)[:2] + end_part
    else:
        return str(start_year)

def rename_and_drop_columns(df):
    df = df.rename(columns={
        'player_name': 'Player',
        'age': 'Age',
        'position': 'Position',
        'team': 'Team',
        'rs_games_played': 'Reg. Season Games',
        'rs_minutes_played': 'Reg. Season Minutes',
        'ps_minutes_played': 'Postseason Minutes',
        'rs_PCP': 'Reg. Season PCP (%)',
        'ps_PCP': 'Postseason PCP (%)',
        'TPS': 'Team Postseason Score',
        'rs_PIM': 'Reg. Season PIM',
        'ps_PIM': 'Postseason PIM'
    })
    df = df.drop(columns=['player_id', 'rs_PER', 'ps_PER'])
    return df

def add_rank_column(df):
    df.insert(0, 'Rank', range(1, len(df) + 1))
    return df


def filter_players(df, metric_name='rs_PIM', min_metric=0.0, min_games=0, min_minutes=0, min_age=0, max_age=None, position=None):
    """
    Filter DataFrame by multiple criteria including position.
    
    Parameters:
        df: pandas DataFrame containing player stats
        min_games: minimum rs_games_played value (default: 0)
        min_minutes: minimum rs_minutes_played value (default: 0)
        min_age: minimum age value (default: 0)
        max_age: maximum age value (default: None - no upper limit)
        position: filter by position (default: None - all positions)
                 Can be 'G', 'F', 'C', or any combination to filter for
                 positions containing those letters
    
    Returns:
        Filtered DataFrame sorted by rs_PCP descending
    """
    # Build the age condition
    age_condition = f"CAST(age AS INTEGER) >= {min_age}"
    if max_age is not None:
        age_condition += f" AND CAST(age AS INTEGER) <= {max_age}"
    
    # Build the position condition
    position_condition = ""
    if position:
        # Handle single or multiple position filters
        if isinstance(position, str):
            position_chars = list(position.upper())  # Convert to list of characters
        else:
            position_chars = [p.upper() for p in position]  # Already a list/tuple
            
        position_clauses = []
        for char in position_chars:
            if char in ['G', 'F', 'C']:  # Validate position characters
                position_clauses.append(f"position LIKE '%{char}%'")
                
        if position_clauses:
            position_condition = f" AND ({' OR '.join(position_clauses)})"
    
    query = f"""
        SELECT *
        FROM df
        WHERE CAST({metric_name} AS FLOAT) > {min_metric}
          AND CAST(rs_games_played AS INTEGER) >= {min_games}
          AND CAST(rs_minutes_played AS FLOAT) >= {min_minutes}
          AND {age_condition}{position_condition}
        ORDER BY CAST({metric_name} AS FLOAT) DESC
    """
    
    return duckdb.query(query).df()

if __name__ == '__main__':

    season = '2022-23'
    year = season_to_year(season)

    """

    filter options:

    MIN and/or MAX age
    Position
    MIN games played
    MIN minutes played
    Metric (rs_PCP, ps_PCP, TPS, rs_PIM, ps_PIM)

    """
    impact_df = process_player_impact(year)
    filtered_impact_df = filter_players(impact_df, min_games=10, max_age=28)
    filtered_impact_df = rename_and_drop_columns(filtered_impact_df)
    filtered_impact_df = add_rank_column(filtered_impact_df)
    print(filtered_impact_df.head(60))

