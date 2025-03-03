import pandas as pd
import logging
import pyodbc
import json
import time

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
today = time.strftime("%d-%m-%Y")
#create log file if it does not exist
storage_log_file = "/opt/airflow/logs/data_storage.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=storage_log_file)
# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
def data_storage(filename,type, source):
    try:
        logging.info(f"Starting data storage for {filename}")
        with open("/opt/airflow/executables/settings.json", "r") as file:
            settings = json.load(file)
        password = settings["sql_pwd"]
        connection_string = settings["db_connection_storage"]

        logging.info("Connecting to Database")
        connection = pyodbc.connect(connection_string + password)
        logging.info("Connecting to Database Successfull")
        cursor = connection.cursor()


        logging.info("Reading insert script template")
        script_file_path = 'dbScripts/insert_script_template.sql'
        logging.info("Executing script to Database")
            
        with open(script_file_path, 'r') as file:
            insert_script = file.read()

        logging.info("Inserting data to database")
        data_path = f"{settings['raw_data_path']}/data/transformed/{source}/{today}/{type}/{filename}"
        df = pd.read_csv(data_path)
        df['DataSource'] = source
        df['Type'] = type
        data_tuples = df.to_records(index=False).tolist()

        cursor.executemany(insert_script, data_tuples)

        connection.commit()


        logging.info("Executed script successfully !!")

        cursor.close()
        connection.close()

        logging.info("Connection closed !!")
    except Exception as e:
        logging.error(f"Error storing data: {str(e)}")

data_storage("customer_data.csv", "csv", "fintech1")
data_storage("database_data.csv", "database", "fintech2")

