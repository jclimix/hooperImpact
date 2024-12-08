from all_classes import DataManager

years = range(2024, 2025) # NOTE: Remember to adjust this!
for year in years:
    DataManager.export_player_metrics(str(year))
