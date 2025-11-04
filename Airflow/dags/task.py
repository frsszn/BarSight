from airflow import DAG
import pandas as pd
import datetime as dt
from datetime import timedelta
# Operators
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.empty import EmptyOperator
# untuk connect postgre dengan python
import psycopg2

DB_CONFIG = {
    'host': 'postgres',          
    'dbname': 'airflow',        
    'user': 'airflow',          
    'password': 'airflow',      
    'port': 5432
}

TABLE_NAME = 'table_m3'
RAW_FILE = '/opt/airflow/dags/P2M3_farissthira_data_raw.csv'
CLEAN_FILE = '/opt/airflow/dags/P2M3_farissthira_data_clean.csv'


def extract_data():
    """Ambil semua data dari PostgreSQL dan simpan ke CSV mentah."""
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"SELECT * FROM {TABLE_NAME};"
    df = pd.read_sql(query, conn)
    conn.close()

    df.to_csv(RAW_FILE, index=False)
    print(f"Extracted {len(df)} rows from {TABLE_NAME}")

def clean_data():
    """Cleaning dan simpan hasilnya ke CSV clean."""
    df = pd.read_csv(RAW_FILE)
    print(f"Starting data cleaning... Initial rows: {len(df)}")

    # Normalisasi nama kolom
    clean_cols = []
    for col in df.columns:
        col_clean = col.strip()                              # hapus spasi awal/akhir
        col_clean = re.sub(r'[^0-9a-zA-Z\s_]', '', col_clean) # hapus simbol aneh
        col_clean = col_clean.lower()                         # ubah jadi lowercase
        col_clean = re.sub(r'\s+', '_', col_clean)            # spasi jadi underscore
        clean_cols.append(col_clean)
    df.columns = clean_cols

    # Hapus duplikat
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    print(f"Removed {before - after} duplicate rows")

    # Handling missing values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True) # Mengembalikan Modus jika ada jika tidak ada maka Unknown
        else:
            df[col].fillna(df[col].median(), inplace=True) # Menggunakan Median

    # Simpan hasil clean
    df.to_csv(CLEAN_FILE, index=False)
    print(f"Clean data saved to {CLEAN_FILE} ({len(df)} rows)")

def load_elastic():
    df = pd.read_csv(CLEAN_FILE, index_col=0)
    es = Elasticsearch("http://elasticsearch:9200")

    actions = [
    {
        "_index": "milestone",
        "_id" : int(r['id']),
        "_source": r.to_dict()
    }
    for i, r in df.iterrows() 
    ]
    response = helpers.bulk(es, actions)
    print(response)



    

# DAG CONFIG
default_args = {
    'owner': 'farissthira',
    'start_date': dt.datetime(2024, 11, 1) - dt.timedelta(hours=7),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=5),
}


with DAG('milestone_3',
         default_args=default_args,
         schedule_interval= '10-30/10 9 * * 6',      # '0 * * * *',
         catchup= False) as dag:

    
    start_task = BashOperator(
        task_id='start_message',
        bash_command='echo "Starting BMW Sales ETL DAG..."'
    )

    extract_task = PythonOperator(
        task_id='extract_from_postgre',
        python_callable=extract_data
    )

    clean_task = PythonOperator(
        task_id='clean_bmw_data',
        python_callable=clean_data
    )

    load_es_task = PythonOperator(
        task_id='load_elastic',
        python_callable=load_elastic
    )

    stop_task = BashOperator(
        task_id='stop_message',
        bash_command='echo "BMW Sales ETL completed successfully!"'
    )

    

    start_task >> extract_task >> clean_task >> load_es_task >> stop_task


