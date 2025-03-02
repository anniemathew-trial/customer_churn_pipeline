from pathlib import Path
import pandas as pd
import numpy as np
import logging
import json
import time

with open("/opt/airflow/executables/settings.json", "r") as file:
        settings = json.load(file)
today = time.strftime("%d-%m-%Y")
#create log file if it does not exist
data_validation_log_file = f"{settings['logging_base_path']}/logs/data_validation.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=data_validation_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
    
def generate_csv_data_quality_report(csv_filename, output_path="csv_validation_report.csv"):
    try:
        logging.info("Starting data validation")
        data_path = f"{settings['raw_data_path']}/data/raw/{today}/csv/{csv_filename}"
        df = pd.read_csv(data_path)
        report_data = []
        logging.info("Running validation on data received from S3")
        
        for col in df.columns:
            data_type = df[col].dtype
            remarks = ""        
            # checking missing empty or null data
            missing_count = df[col].isnull().sum() + df[col].isna().sum()
                
            missing_percentage = (missing_count / len(df)) * 100
            unique_count = df[col].nunique()
            # Numeric Columns
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                max_val = df[col].max()
                mean_val = df[col].mean()
                median_val = df[col].median()
                max_allowed_value = 100
                iqr = df[col].quantile(0.75) - df[col].quantile(0.25)
                potential_outlier1 = df[df[col] < iqr*-3.5]
                potential_outlier2 = df[df[col] > iqr*3.5]
                if not (potential_outlier1.empty & potential_outlier2.empty):
                    remarks += f"{col} has {len(potential_outlier1) + len(potential_outlier2)} potential outlier rows."
                
                if col == 'tenure':
                    max_allowed_value = 80  # Example
                invalid_data = df[df[col] > max_allowed_value]
                if not invalid_data.empty:
                    remarks += f"{len(invalid_data)} rows have '{col}' > {max_allowed_value}."
                
                    
                report_data.append([col, data_type, missing_count, missing_percentage, unique_count, min_val, max_val, mean_val, median_val, remarks])
            # Categorical/Object Columns
            elif pd.api.types.is_object_dtype(df[col]):
                empty_rows = df[col].str.strip()
                empty_rows = empty_rows.replace('', np.nan)
                missing_count = empty_rows.isnull().sum() + empty_rows.isna().sum()
                missing_percentage = (missing_count / len(df)) * 100
                report_data.append([col, data_type, missing_count, missing_percentage, unique_count, None, None, None, None, remarks])
            # Boolean Columns
            elif pd.api.types.is_bool_dtype(df[col]):
                report_data.append([col, data_type, missing_count, missing_percentage, unique_count, None, None, None, None, remarks])
            # Datetime Columns
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                report_data.append([col, data_type, missing_count, missing_percentage, unique_count, None, None, None, None, remarks])
            else:
                report_data.append([col, data_type, missing_count, missing_percentage, unique_count, None, None, None, None, remarks])
        report_df = pd.DataFrame(report_data, columns=[
          "Column", "Data Type", "Missing Count", "Missing Percentage", "Unique Count",
          "Min", "Max", "Mean", "Median", "Remarks"
        ])

        logging.info("Saving metrics to S3")

        p = Path('reports')
        p.mkdir(parents = True, exist_ok = True)
        report_df.to_csv(f"reports/{output_path}", index=False)
        logging.info(f"Metrics saved to: {output_path}")
   except Exception as e:
        logging.error(f"Error validating  data: {str(e)}")


generate_csv_data_quality_report("customer_data.csv")
