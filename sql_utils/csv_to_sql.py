import pandas as pd
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

from sql_utils.sql_transfers import insert_df_to_db

def csv_to_sql(csv_file, table_name, schema):
    df = pd.read_csv(csv_file)
    insert_df_to_db(df, table_name, schema)

if __name__ == '__main__':

    csv_file = os.path.join(script_dir, '..', '..', 'data', 'testing', 'player_stats1.csv')
    table_name = 'test_data1'
    schema = 'testing'

    csv_to_sql(csv_file, table_name, schema)
