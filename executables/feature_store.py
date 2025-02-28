import feast
from feast import Entity, FeatureView, Field, ValueType
from feast.types import Int64, Float64, Bool, String
from feast.infra.offline_stores.file_source import FileSource
from datetime import timedelta
import pandas as pd
from pathlib import Path
from fastparquet import write 
import logging
import pyodbc


def feature_store():
    server = "dmml_customer_churn_setup-sqlserver-1,1433"
    database = "customer_churn_db"
    username = "sa"
    password = "NewPASS1234"

    logging.info("Connecting to Database")
    connection = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    logging.info("Connecting to Database Successfull")
    _ = connection.cursor()
       
    query = "SELECT * FROM [customer_churn_db].[dbo].[customers]"
    logging.info("Reading data from database.")
    p = Path('data/curated')
    p.mkdir(parents = True, exist_ok = True)
    df = pd.read_sql(query, connection)
    write('data/curated/custom_features.parq', df)
    
    customer = Entity(
        name="Id",
        description="Customer ID",
        value_type = ValueType.INT64
    )

    csv_data = FileSource(
        path='data/curated/custom_features.parq',
        event_timestamp_column="Tenure"
    )

    csv_features = [
        Field(name="CreditScore", dtype=Int64, description="Credit Score of the customer")
    ]
            
    feature_view = FeatureView(
        name = "customer_churn_features",
        entities=[customer],
        ttl=timedelta(days=365),
        schema = csv_features,
        online=True,
        source=csv_data
    )
    
feature_store()
