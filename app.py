from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from filter_player_impact import filter_players, rename_and_drop_columns, add_rank_column, season_to_year
from process_player_impact import process_player_impact
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

def get_version():
    try:
        with open('version.txt', 'r') as f:
            version = f.read().strip()
        return version
    except Exception as e:
        print(f"Error reading version file: {e}")
        return "v?.?.?"

version = get_version()

@app.route('/')
def index():
    # filter options for the form
    positions = ['G', 'F', 'C', 'G/F', 'F/C', 'G/F/C']
    metrics = {
        'rs_PIM': 'Reg. Season PIM',
        'ps_PIM': 'Postseason PIM',
        'rs_PCP': 'Reg. Season PCP (%)',
        'ps_PCP': 'Postseason PCP (%)',
        'TPS': 'Team Postseason Score'
    }
    
    # seasons list from 1969-70 to 2024-25 in format "1969-70"
    start_year = 1969
    end_year = 2024
    seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(start_year, end_year+1)]
    
    return render_template('index.html', positions=positions, metrics=metrics, seasons=seasons, version=version)

@app.route('/results', methods=['POST'])
def results():
    if request.method == 'POST':

        season = request.form.get('season', '2008-09')
        year = season_to_year(season)
        min_age = int(request.form.get('min_age', 0))
        max_age = request.form.get('max_age', '')
        position = request.form.get('position', None)
        min_games = int(request.form.get('min_games', 20))
        min_minutes = int(request.form.get('min_minutes', 0))
        metric = request.form.get('metric', 'rs_PIM')
        min_metric = float(request.form.get('min_metric', 0.0))
        
        # empty max_age to None
        if max_age == '':
            max_age = None
        else:
            max_age = int(max_age)
            
        # process data
        try:
            # get the df for the selected year
            impact_df = process_player_impact(year)
            
            # apply filters
            filtered_df = filter_players(
                impact_df, 
                metric_name=metric,
                min_metric=min_metric,
                min_games=min_games, 
                min_minutes=min_minutes,
                min_age=min_age, 
                max_age=max_age, 
                position=position
            )
            
            # rename columns for display
            display_df = rename_and_drop_columns(filtered_df)

            display_df = add_rank_column(display_df)
            
            # convert df to HTML table
            table_html = display_df.to_html(classes='table table-striped', index=False)
            
            return render_template(
                'results.html', 
                table=table_html, 
                season=season,
                version=version,
                filters={
                    'min_age': min_age,
                    'max_age': max_age if max_age else "No limit",
                    'position': position if position else "All",
                    'min_games': min_games,
                    'min_minutes': min_minutes,
                    'metric': metric,
                    'min_metric': min_metric
                }
            )
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('index.html', error=error_message)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8006)