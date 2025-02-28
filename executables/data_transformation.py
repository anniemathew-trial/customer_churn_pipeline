from sklearn.preprocessing import StandardScaler
from pathlib import Path
import pandas as pd
import logging
#create log file if it does not exist
data_transformation_and_storage_log_file = "/opt/airflow/logs/data_transformation.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=data_transformation_and_storage_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.ERROR)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

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
        df['TenureAgeRatio'] = df['Tenure']/(df['Age']) #standardizing tenure by age
        df['BalanceSEstimatedalaryRatio'] = df['Balance']/(df['EstimatedSalary'])
        df['BalanceAgeRatio'] = df['Balance']/(df['Age'])
        
        logging.info("Scaling 'Tenure', 'Balance', 'EstimatedSalary'.")
        scaler = StandardScaler()
        df[['Tenure', 'Balance', 'EstimatedSalary']] = scaler.fit_transform(df[['Tenure', 'Balance', 'EstimatedSalary']]) 
        
        p = Path('data/transformed')
        p.mkdir(parents = True, exist_ok = True)
            
        logging.info("Saving data to S3.")
        df.to_csv(f"data/transformed/{output_path}", index=False)
    except Exception as e:
        logging.error(f"Failed data transformation: {str(e)}")
    
data_transformation()