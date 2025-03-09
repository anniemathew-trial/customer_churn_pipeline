from sklearn.preprocessing import StandardScaler
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import json
import time
import boto3

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
today = time.strftime("%d-%m-%Y")
#create log file if it does not exist
data_transformation_log_file = f"{settings['logging_base_path']}/logs/data_transformation.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=data_transformation_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

def upload_file(file_name, bucket, object_name=None):
    
    if object_name is None:
        object_name = file_name
    s3_client = boto3.client(
        's3', 
        aws_access_key_id = settings["id"],
        aws_secret_access_key = settings["key"],
        region_name='us-east-1')
    _ = s3_client.upload_file(file_name, bucket, object_name)
        
def data_transformation(filename, type, source):
    try:
        logging.info("Starting data transformation for csv.")
        data_path = f"{settings['raw_data_path']}/data/cleaned/{source}/{today}/{type}/{filename}"
        df = pd.read_csv(data_path)

        df.loc[df.HasCrCard == 0, 'HasCrCard'] = -1
        df.loc[df.IsActiveMember == 0, 'IsActiveMember'] = -1
        #One-Hot encoding for Categorical Variables
        df = pd.get_dummies(df, columns=['Geography', 'Gender'], drop_first=True)    
        

        #Feature creation
        df['CreditScoreTenureRatio'] = df['CreditScore']/(df['Tenure'])
        df['CreditScoreTenureRatio'].replace([np.inf, -np.inf], 0, inplace=True)        
        df['CreditScoreTenureRatio'] = df['CreditScoreTenureRatio'].fillna(0)        
        df['CreditScoreTenureRatio'] = df['CreditScoreTenureRatio'].astype('float')
        
        df['TenureAgeRatio'] = df['Tenure']/(df['Age']) #standardizing tenure by age
        df['TenureAgeRatio'].replace([np.inf, -np.inf], 0, inplace=True)        
        df['TenureAgeRatio'] = df['TenureAgeRatio'].fillna(0)
        df['TenureAgeRatio'] = df['TenureAgeRatio'].astype('float')
        
        df['BalanceSEstimatedalaryRatio'] = df['Balance']/(df['EstimatedSalary'])
        df['BalanceSEstimatedalaryRatio'].replace([np.inf, -np.inf], 0, inplace=True)        
        df['BalanceSEstimatedalaryRatio'] = df['BalanceSEstimatedalaryRatio'].fillna(0)
        df['BalanceSEstimatedalaryRatio'] = df['BalanceSEstimatedalaryRatio'].astype('float')
        
        df['BalanceAgeRatio'] = df['Balance']/(df['Age'])
        df['BalanceAgeRatio'].replace([np.inf, -np.inf], 0, inplace=True)        
        df['BalanceAgeRatio'] = df['BalanceAgeRatio'].fillna(0)
        df['BalanceAgeRatio'] = df['BalanceAgeRatio'].astype('float')
        
        logging.info("Scaling 'Balance', 'EstimatedSalary'.")
        scaler = StandardScaler()
        df[['Balance', 'EstimatedSalary']] = scaler.fit_transform(df[['Balance', 'EstimatedSalary']]) 
              
        logging.info("Saving data to S3.")
        transformed_file_path = f"data/transformed/{source}/{today}/{type}"
        p = Path(transformed_file_path)
        p.mkdir(parents = True, exist_ok = True)
        df.to_csv(f"{settings['raw_data_path']}/{transformed_file_path}/{filename}", index=False)       
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = "dmmlassignmentbucket"
        s3_key = f"{transformed_file_path}/{filename}"
        upload_file(f"{settings['raw_data_path']}/{transformed_file_path}/{filename}", bucket_name, s3_key)        

    except Exception as e:
        logging.error(f"Failed data transformation: {str(e)}")
    
data_transformation("customer_data.csv", "csv", "fintech1")
data_transformation("database_data.csv", "database", "fintech2")
