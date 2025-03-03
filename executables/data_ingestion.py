from pathlib import Path
import pandas as pd
import logging
import pyodbc
import time
import json

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
today = time.strftime("%d-%m-%Y")
#create log file if it does not exist
ingestion_log_file = f"{settings['logging_base_path']}/logs/data_ingestion.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=ingestion_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

def ingest_csv(filename, source):
    try:
        logging.info(f"Reading data from CSV file {filename}")
        data = pd.read_csv(f"{settings['raw_data_path']}/data/{filename}")
        p = Path(f'/opt/airflow/data/raw/{source}/{today}/csv')
        p.mkdir(parents = True, exist_ok = True)
        data.to_csv(f"/opt/airflow/data/raw/{source}/{today}/csv/{filename}", index=False)
        logging.info(f"Data from CSV {filename} ingested successfully!")
        return data
    except Exception as e:
        logging.error(f"Error ingesting CSV: {str(e)}")
        raise e
        
def ingest_database(source):
    try:
        password = settings["sql_pwd"]
        connection_string = settings["db_connection"]

        logging.info("Connecting to Database")
        connection = pyodbc.connect(connection_string + password)
        logging.info("Connecting to Database Successfull")
        _ = connection.cursor()
        
        query = "SELECT * FROM [dmml_assignment].[dbo].[customers]"
        logging.info("Reading data from database.")
        data = pd.read_sql(query, connection)
        
        connection.close()
        p = Path(f'/opt/airflow/data/raw/{source}/{today}/database')
        p.mkdir(parents = True, exist_ok = True)
        data.to_csv(f"/opt/airflow/data/raw/{source}/{today}/database/database_data.csv", index=False)
        logging.info("Data from Database ingested successfully!")
        return data
    except Exception as e:
        logging.error(f"Error ingesting database: {str(e)}")
        raise e
        
filename = 'customer_data.csv';
csv_data = ingest_csv(filename, "fintech1")
database_data = ingest_database("fintech2")
