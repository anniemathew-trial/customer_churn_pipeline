from feast import Entity, Field, FeatureView, FileSource, ValueType
from datetime import datetime, timezone, timedelta
from feast.types import Int32, Int64, Float64
from fastparquet import write 
import pandas as pd
import logging
import pyodbc
import json

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
#create log file if it does not exist
data_transformation_log_file = f"{settings['logging_base_path']}/logs/feature_store.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=data_transformation_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
try:
        password = settings["sql_pwd"]
        connection_string = settings["db_connection_storage"]

        logging.info("Connecting to Database")
        connection = pyodbc.connect(connection_string + password)
        logging.info("Connecting to Database Successfull")
        _ = connection.cursor()
        
        query = "SELECT * FROM [customer_churn_db].[dbo].[customers]"
        logging.info("Reading data from database.")
        data = pd.read_sql(query, connection)
        write('data/customer_features.parq', data)
        logging.info("Data collection from database successfull!!")
        
except Exception as e:
    logging.info("Data collection from database failed {str(e)}!!")

try:
        logging.info("Declaring an entity for the dataset")
        customer = Entity(
            name="Id", 
            value_type=ValueType.INT64, 
            description="The ID of the customer"
            )
        
        logging.info("Declaring the source for raw feature data")
        file_source = FileSource(
            path=r"data/customer_features.parq",
            event_timestamp_column="CreatedOn",
        )
        
        logging.info("Defining the features in a feature view")
        customer_stats_fv = FeatureView(
            name="customer_stats_fv",
            ttl=timedelta(days=1),
            entities=[customer],
            schema =[
                Field(name="Id", dtype=Int64),
                Field(name="CreditScore", dtype=Int64),
                Field(name="Age", dtype=Int32),
                Field(name="Tenure", dtype=Float64),        
                Field(name="Balance", dtype=Float64),        
                Field(name="NumOfProducts", dtype=Int32),        
                Field(name="HasCrCard", dtype=Int32),        
                Field(name="IsActiveMember", dtype=Int32),        
                Field(name="EstimatedSalary", dtype=Float64),        
                Field(name="Exited", dtype=Int32),        
                Field(name="Geography_Germany", dtype=Float64),        
                Field(name="Geography_Spain", dtype=Float64),        
                Field(name="Gender_Male", dtype=Float64),        
                Field(name="CreditScoreTenureRatio", dtype=Float64),        
                Field(name="TenureAgeRatio", dtype=Float64),        
                Field(name="BalanceSEstimatedalaryRatio", dtype=Float64),        
                Field(name="BalanceAgeRatio", dtype=Float64),        
                ],    
            source=file_source
        )
        logging.info("Feature view creation successfull!!")
        
except Exception as e:
    logging.info("Feature view creation failed {str(e)}!!")
