import logging
import boto3
import time
import json

with open("settings.json", "r") as file:
        settings = json.load(file)
#create log file if it does not exist
ingestion_log_file = f"{settings["logging_base_path"]}\\logs\\data_ingestion.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=ingestion_log_file)

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
    

today = time.strftime("%d-%m-%Y")
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "dmmlassignmentbucket"
file_name = "customer_data.csv"
s3_key = f"data/raw/{today}/csv/{file_name}"
upload_file(f"{settings["raw_data_path"]}/data/{file_name}", bucket_name, s3_key)