from sklearn.preprocessing import StandardScaler
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import json

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
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
        
def data_transformation(output_path="customer_data.csv"):
    try:
        logging.info("Starting data preparation for csv.")
        # Read data from Amazon S3 bucket
        df = pd.read_csv('data/cleaned/customer_data.csv')

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
        
        logging.info("Scaling 'Tenure', 'Balance', 'EstimatedSalary'.")
        scaler = StandardScaler()
        df[['Tenure', 'Balance', 'EstimatedSalary']] = scaler.fit_transform(df[['Tenure', 'Balance', 'EstimatedSalary']]) 
        
        p = Path('data/transformed')
        p.mkdir(parents = True, exist_ok = True)
            
        logging.info("Saving data to S3.")
        df.to_csv(f"/opt/airflow/data/transformed/{today}/csv/{output_path}", index=False)

        bucket_name = "dmmlassignmentbucket"
        file_name = "customer_data.csv"
        s3_key = f"data/transformed/{today}/csv/{file_name}"
        upload_file(f"{settings['raw_data_path']}/data/transformed/{today}/csv/{file_name}", bucket_name, s3_key)
    except Exception as e:
        logging.error(f"Failed data transformation: {str(e)}")
    
data_transformation()
