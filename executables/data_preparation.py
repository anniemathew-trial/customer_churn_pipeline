from sklearn.preprocessing import StandardScaler
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns
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
data_preparation_log_file = f"{settings['logging_base_path']}/logs/data_preparation.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=data_preparation_log_file)

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
    
def prepare_data(filename,type, source, output_path):
    try:
        logging.info(f"Starting data preparation for {filename}.")
        data_path = f"{settings['raw_data_path']}/data/raw/{source}/{today}/{type}/{output_path}"
        df = pd.read_csv(data_path)
        
        
        
        logging.info("Dropping 'Estimated Salary' & 'Credit Score' with 0 & negative values")
        df.loc[(df['EstimatedSalary'] > 0) & (df['CreditScore'] > 0)].reset_index(drop=True)
        
        logging.info("Handling 'Balance', 'EstimatedSalary' empty data with mean")
        numeric_columns = ['Balance', 'EstimatedSalary'];
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].str.strip()
                df[col] = df[col].replace('', np.nan)
                df[col] = pd.to_numeric(df[col])
                df[col] = df[col].fillna(df[col].median(skipna=True))

        logging.info("Handling 'Tenure', 'Age' empty data with tenure + 18 in age and droping tenure with 0 values & negative values")
        numeric_columns = ['Age', 'Tenure'];
        for col in numeric_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].str.strip()
                df[col] = df[col].replace('', np.nan)
                df[col] = pd.to_numeric(df[col])

        logging.info("Dropping 'Tenure' less than 0 and greater than 80")
        df.loc[(df['Tenure'] >= 0) & (df['Tenure'] < 80)].reset_index(drop=True)
        
        logging.info("Handling 'Age' empty data")
        df['Age'] = df['Age'].fillna(df['Tenure'] + 18) 
        
        logging.info("Dropping 'Age' less than 18 and greater than 110")
        df.loc[(df['Age'] >= 18) & (df['Age'] < 110)].reset_index(drop=True)
               
            
        logging.info("Droping 'Surname' as it may lead to profiling, 'RowNumber', 'CustomerId' as it is not required")
        df = df.drop(["RowNumber", "CustomerId", "Surname"], axis = 1)
        
        logging.info("Making 'Geography', 'Gender' as categorical")
        categorical_columns = ['Geography', 'Gender']
        df[categorical_columns] = df[categorical_columns].astype('category')

        logging.info("Making 'HasCrCard', 'IsActiveMember', 'Exited' as integers")
        df['HasCrCard'] = df['HasCrCard'].astype(int) 
        df['IsActiveMember'] = df['IsActiveMember'].astype(int) 
        df['Exited'] = df['Exited'].astype(int) 
           
        logging.info("Saving data to S3.")
        cleaned_file_path = f"data/cleaned/{source}/{today}/{type}"
        p = Path(f"{settings['raw_data_path']}/{cleaned_file_path}")
        p.mkdir(parents = True, exist_ok = True)
        logging.info(f"Directory created at {settings['raw_data_path']}/{cleaned_file_path}")
        df.to_csv(f"{settings['raw_data_path']}/{cleaned_file_path}/{output_path}", index=False)       
        s3_client = boto3.client('s3', region_name='us-east-1')
        logging.info("Connected to s3")        
        bucket_name = "dmmlassignmentbucket"
        s3_key = f"{cleaned_file_path}/{output_path}"
        upload_file(f"{settings['raw_data_path']}/{cleaned_file_path}/{output_path}", bucket_name, s3_key)  
        logging.info("File uploaded to S3")     
        
        generate_report(df, source, type)
    except Exception as e:
        logging.error(f"Error in preparing data{str(e)}") 
        raise e
    
def generate_report(data, source, type, pdf_filename = "plots.pdf"):   
    try:
        file_path = f"{settings['raw_data_path']}/visualization/{source}/{today}/{type}"
        p = Path(file_path)
        p.mkdir(parents = True, exist_ok = True)
        with PdfPages(f"{file_path}/{pdf_filename}") as pdf:
            logging.info("Creating Pie chart")            
            labels = 'Exited', 'Retained'
            sizes = [data.Exited[data['Exited']==1].count(), data.Exited[data['Exited']==0].count()]
            explode = (0, 0.1)
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')
            plt.title("Customer Churned vs Retained", size = 20)
            pdf.savefig()
            plt.close()
            for column in data.columns:
                logging.info(f"Generating histogram for column {column}.")
                plt.figure(figsize=(8,6))
                plt.hist(data[column], bins=20, alpha=0.7, color='b', edgecolor='black')
                plt.title(f'Histogram of {column}')
                plt.xlabel(column)
                plt.ylabel('Frequency')
                plt.grid(True)
                pdf.savefig()
                plt.close()
                
            
            logging.info("Generating histogram for relation of Exited with Categorical data.") 
            fig, axarr = plt.subplots(2, 2, figsize=(20, 12))
            sns.countplot(x='Geography', hue = 'Exited',data = data, ax=axarr[0][0])
            sns.countplot(x='Gender', hue = 'Exited',data = data, ax=axarr[0][1])
            sns.countplot(x='HasCrCard', hue = 'Exited',data = data, ax=axarr[1][0])
            sns.countplot(x='IsActiveMember', hue = 'Exited',data = data, ax=axarr[1][1])
            
            logging.info("Generating box plots for relation of Exited with non Categorical data.") 
            fig, axarr = plt.subplots(3, 2, figsize=(20, 12))
            sns.boxplot(y='CreditScore',x = 'Exited', hue = 'Exited',data = data, ax=axarr[0][0])
            sns.boxplot(y='Age',x = 'Exited', hue = 'Exited',data = data , ax=axarr[0][1])
            sns.boxplot(y='Tenure',x = 'Exited', hue = 'Exited',data = data, ax=axarr[1][0])
            sns.boxplot(y='Balance',x = 'Exited', hue = 'Exited',data = data, ax=axarr[1][1])
            sns.boxplot(y='NumOfProducts',x = 'Exited', hue = 'Exited',data = data, ax=axarr[2][0])
            sns.boxplot(y='EstimatedSalary',x = 'Exited', hue = 'Exited',data = data, ax=axarr[2][1])
            
            pdf.savefig()
            plt.close()
            logging.info(f'Saved pdf in {file_path}/{pdf_filename}')
    except Exception as e:
        logging.error(f"Error in creating report{str(e)}")
        raise e
        


prepare_data("customer_data.csv", "csv", "fintech1", "customer_data.csv")
prepare_data("database_data.csv", "database", "fintech2", "database_data.csv")
