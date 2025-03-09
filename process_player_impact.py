import pandas as pd
import re, os, sys
from loguru import logger

script_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

from sql_utils.sql_transfers import extract_table_to_df

def get_player_info(df: pd.DataFrame) -> pd.DataFrame:
    """Extract basic player information columns."""
    return df[['player_id', 'player_name', 'age', 'position']]

def add_column_from_match(df1: pd.DataFrame, df2: pd.DataFrame, column_name: str, new_column_name: str) -> pd.DataFrame:
    """Add a column from df2 to df1 based on player_id match."""
    if df2 is None:
        df1[new_column_name] = 0
        return df1
    
    # Simplify by using pandas operations more efficiently
    df2_dedup = df2.drop_duplicates(subset='player_id', keep='first')
    merged_df = pd.merge(df1, df2_dedup[['player_id', column_name]], on='player_id', how='left')
    merged_df[new_column_name] = merged_df[column_name].fillna(0)
    
    return merged_df.drop(columns=[column_name])

def add_teams_column(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Add team information to player data, excluding numbered team entries."""
    if 'team' not in df2.columns or 'player_id' not in df2.columns:
        return df1
        
    # Define a regex pattern to match 'XTM' where X is a number
    pattern = re.compile(r'\dTM')
    
    # Group by 'player_id' and filter out team names matching the pattern
    teams_df = df2.groupby('player_id')['team'].apply(
        lambda x: ', '.join([team for team in x if not pattern.match(team)])
    ).reset_index()
    
    # Merge and handle missing values
    merged_df = pd.merge(df1, teams_df, on='player_id', how='left')
    merged_df['team'] = merged_df['team'].fillna('')
    
    return merged_df.drop_duplicates(subset='player_id', keep='first')

def _calculate_pcp(df: pd.DataFrame, per_column: str, pcp_column: str) -> pd.DataFrame:
    """Calculate Player Contribution Percentage based on PER values."""
    # Ensure PER is numeric
    df[per_column] = pd.to_numeric(df[per_column], errors='coerce').fillna(0)
    
    # Create a helper column with team lists
    df['team_list'] = df['team'].apply(lambda x: x.split(', ') if x else [])
    
    # Calculate PCP for each player
    pcp_values = []
    
    for _, row in df.iterrows():
        player_per = row[per_column]
        teams = row['team_list']
        
        if not teams or player_per == 0:
            pcp_values.append(0)
            continue
            
        team_pcps = []
        for team in teams:
            # Calculate total PER for the current team
            team_total_per = df[df['team_list'].apply(lambda x: team in x)][per_column].sum()
            
            # Calculate PCP if team has positive total PER
            if team_total_per > 0:
                team_pcps.append((player_per / team_total_per) * 100)
                
        # Average the PCP values across teams
        avg_pcp = round(sum(team_pcps) / len(team_pcps), 1) if team_pcps else 0
        pcp_values.append(avg_pcp)
    
    # Add calculated PCP to dataframe and clean up
    df[pcp_column] = pcp_values
    
    return df.drop(columns=['team_list'])

def calculate_rs_pcp(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate regular season Player Contribution Percentage."""
    return _calculate_pcp(df, 'rs_PER', 'rs_PCP')

def calculate_ps_pcp(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate postseason Player Contribution Percentage."""
    return _calculate_pcp(df, 'ps_PER', 'ps_PCP')

def calculate_tps(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Calculate Team Playoff Score for each player based on their latest team."""
    if df2 is None:
        df1['TPS'] = 0.0
        return df1

    # Define round weights and advancement bonuses
    round_weights = {'r1_wins': 1.0, 'r2_wins': 1.2, 'r3_wins': 1.4, 'r4_wins': 1.6}
    advancement_bonus = {'r2': 1, 'r3': 2, 'r4': 3}
    
    # Create TPS column
    df1['TPS'] = 0.0
    
    for idx, player in df1.iterrows():
        # Get the latest team the player played for
        latest_team = player['team'].split(', ')[-1] if player['team'] else ''
        
        # Find team data
        team_data = df2[df2['abbreviation'] == latest_team]
        if team_data.empty:
            continue
            
        team_data = team_data.iloc[0]
        
        # Calculate weighted wins and games played
        weighted_wins = sum(team_data.get(round_col, 0) * weight 
                         for round_col, weight in round_weights.items() if round_col in team_data)
        
        # Calculate games played (wins + losses)
        games_played = sum(team_data.get(round_col, 0) for round_col in round_weights 
                       if round_col in team_data)
        games_played += sum(team_data.get(round_col.replace('wins', 'losses'), 0) 
                        for round_col in round_weights if round_col.replace('wins', 'losses') in team_data)
        
        # Determine advancement bonus
        adv_bonus = 0
        for round_num, bonus in sorted(advancement_bonus.items(), reverse=True):
            round_played = team_data.get(f'{round_num}_wins', 0) > 0 or team_data.get(f'{round_num}_losses', 0) > 0
            if round_played:
                adv_bonus = bonus
                break
        
        # Calculate TPS
        if games_played > 0:
            tps = (weighted_wins + adv_bonus) / (games_played + 4)
            df1.at[idx, 'TPS'] = round(tps, 3)
            
    return df1

def calculate_rs_pim(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """Calculate regular season Player Impact Metric."""
    # Create rs_PIM column
    df1['rs_PIM'] = 0.0
    
    for idx, player in df1.iterrows():
        teams = player['team'].split(', ') if player['team'] else []
        rs_pcp = player['rs_PCP']
        
        win_pcts = []
        
        for team in teams:
            team_data = df2[df2['abbreviation'] == team]
            if team_data.empty:
                continue
                
            team_data = team_data.iloc[0]
            wins = team_data['wins']
            losses = team_data['losses']
            total_games = wins + losses
            
            if total_games > 0:
                win_pcts.append(wins / total_games)
        
        # Calculate rs_PIM
        if win_pcts:
            avg_win_pct = sum(win_pcts) / len(win_pcts)
            df1.at[idx, 'rs_PIM'] = round(rs_pcp * avg_win_pct * 10, 1)
            
    return df1

def calculate_ps_pim(df1: pd.DataFrame) -> pd.DataFrame:
    """Calculate postseason Player Impact Metric."""
    # Calculate ps_PIM directly based on ps_PCP and TPS
    df1['ps_PIM'] = round(df1['ps_PCP'] * df1['TPS'] * 10, 1)
    return df1

def process_player_impact(year):
    """Process player statistics and calculate derived metrics."""
    # Extract data from database
    reg_season_per_stats_df = extract_table_to_df(f'{year}_reg_season_stats', 'per_game_stats')
    # postseason_per_stats_df = extract_table_to_df(f'{year}_postseason_stats', 'per_game_stats')
    reg_season_adv_stats_df = extract_table_to_df(f'{year}_reg_season_stats', 'advanced_stats')
    postseason_adv_stats_df = extract_table_to_df(f'{year}_postseason_stats', 'advanced_stats')
    league_standings_df = extract_table_to_df(f'{year}_standings', 'standings')
    playoffs_bracket_df = extract_table_to_df(f'{year}_playoffs_bracket', 'playoffs')

    # Build results dataframe step by step
    player_df = get_player_info(reg_season_per_stats_df)
    player_df = add_teams_column(player_df, reg_season_per_stats_df)
    
    # Add stats columns
    columns_to_add = [
        (reg_season_per_stats_df, 'games_played', 'rs_games_played'),
        (reg_season_adv_stats_df, 'minutes_played', 'rs_minutes_played'),
        (postseason_adv_stats_df, 'minutes_played', 'ps_minutes_played'),
        (reg_season_adv_stats_df, 'player_efficiency_rating', 'rs_PER'),
        (postseason_adv_stats_df, 'player_efficiency_rating', 'ps_PER')
    ]
    
    for source_df, source_col, target_col in columns_to_add:
        player_df = add_column_from_match(player_df, source_df, source_col, target_col)
    
    # Calculate derived metrics
    player_df = calculate_rs_pcp(player_df)
    player_df = calculate_ps_pcp(player_df)
    player_df = calculate_tps(player_df, playoffs_bracket_df)
    player_df = calculate_rs_pim(player_df, league_standings_df)
    player_df = calculate_ps_pim(player_df)
    
    return player_df

if __name__ == '__main__':
    year = 2024
    results_df = process_player_impact(year)
    print(results_df.head(35))