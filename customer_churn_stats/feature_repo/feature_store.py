from feast import Entity, Field, FeatureView, FileSource, ValueType
from datetime import datetime, timezone, timedelta
from feast.types import Int32, Int64, Float64
from fastparquet import write 
import pandas as pd
import logging
import pyodbc
try:
        server = "dmml_customer_churn_setup-sqlserver-1,1433"
        database = "dmml_assignment"
        username = "sa"
        password = "NewPASS1234"

        logging.info("Connecting to Database")
        connection = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
        logging.info("Connecting to Database Successfull")
        _ = connection.cursor()
        
        query = "SELECT * FROM [customer_churn_db].[dbo].[customers]"
        logging.info("Reading data from database.")
        data = pd.read_sql(query, connection)
        print(data.head())
        write('data/customer_features.parq', data)
        
        
except Exception as e:
    print("failed")
# Declaring an entity for the dataset
customer = Entity(
    name="Id", 
    value_type=ValueType.INT64, 
    description="The ID of the customer"
    )

# Declaring the source for raw feature data
file_source = FileSource(
    path=r"data/customer_features.parq",
    event_timestamp_column="CreatedOn",
)

# Defining the features in a feature view
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
