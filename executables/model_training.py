from feast import FeatureStore
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from pathlib import Path
import pandas as pd
import logging
import mlflow
import pickle


#create log file if it does not exist
modelling_log_file = "/opt/airflow/logs/model_training.log"
logging.root.handlers = []
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO , filename=modelling_log_file)

# set up logging
console = logging.StreamHandler()
console.setLevel(logging.INFO)

# set a format which is simpler for console use
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)
def retrieve_data_from_feast():
    store = FeatureStore(repo_path="customer_churn_stats/feature_repo/")
    logging.info("Getting data")
    data = []
    id_range_start = 1
    id_range_end = 1000
    while True:
        entity_rows = [{"Id":id} for id in range(id_range_start,id_range_end)]  
        logging.info(f"Start and End Range: {id_range_start} to {id_range_end}")      
        features = store.get_online_features(
            features=[
                "customer_stats_fv:CreditScore",
                "customer_stats_fv:Age",
                "customer_stats_fv:Tenure",
                "customer_stats_fv:Balance",
                "customer_stats_fv:NumOfProducts",
                "customer_stats_fv:HasCrCard",
                "customer_stats_fv:IsActiveMember",
                "customer_stats_fv:EstimatedSalary",
                "customer_stats_fv:Exited",
                "customer_stats_fv:Geography_Germany",
                "customer_stats_fv:Geography_Spain",
                "customer_stats_fv:Gender_Male",
                "customer_stats_fv:CreditScoreTenureRatio",
                "customer_stats_fv:TenureAgeRatio",
                "customer_stats_fv:BalanceSEstimatedalaryRatio",
                "customer_stats_fv:BalanceAgeRatio",
                ],
            entity_rows=entity_rows
        ).to_df()
        if features["Exited"].isna().any():
            features = features.dropna(subset = ["Exited"])
        if len(features) > 0:
            data.append(features)
            id_range_start = id_range_start + id_range_end
            id_range_end = id_range_end + id_range_end
            logging.info(f"New Start and End Range: {id_range_start} to {id_range_end}")      
            
        else:
            logging.info(f"Stoping at Start and End Range: {id_range_start} to {id_range_end}")               
            break
    logging.info("Created feature data")
    final_data = pd.concat(data, ignore_index = True)
    logging.info(final_data.head())
    return final_data
  
def train_log_models():
    data = retrieve_data_from_feast();
    logging.info("received feature data")
    x = data.drop('Exited', axis=1)  # Features (all columns except 'Amount')
    y = data['Exited']  # Target variable ('Amount' column)
    x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42)  # 0.2 represents 20% test size
    logging.info("Models defined")
    
    models = { 
              "RandomForest" : RandomForestClassifier(n_estimators=100),
              "LogisticRegression" : LogisticRegression(),
              "SVM" : SVC(probability=True),
              
              }
    
    p = Path('models')
    p.mkdir(parents = True, exist_ok = True)
    mlflow.set_tracking_uri("http://localhost:5000")
    for model_name, model in models.items():
        logging.info(f"Training model {model_name}")
        
        model.fit(x_train, y_train)
        logging.info(f"Predicting model {model_name}")
        
        y_pred = model.predict(x_test)
        logging.info(f"Calculating accuracy {model_name}")
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f_score = f1_score(y_test, y_pred)
        with mlflow.start_run():
            mlflow.log_param("runName", model_name)
            mlflow.log_param("model_type", model_name)
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1_score", f_score)
            mlflow.sklearn.log_model(model, f"{model_name}_model")
            logging.info(f"Logged model {model_name}")
            
            with open(f"models/{model_name}.pkl", "wb") as f:
                pickle.dump(model,f)
            
    
def register_best_model():
    logging.info("Finding Best model")
    runs = mlflow.search_runs()
    best_run = runs.sort_values(by="metrics.f1_score", ascending=False).iloc[0]
    logging.info(f"Selected best model : {best_run}")
    best_accuracy = best_run["metrics.f1_score"]
    best_model = best_run["runName"]
    best_run_id = best_run["run_id"]
    with open("models/best_model.txt", "w") as f:
        f.write(f"Best Run ID: {best_run_id}, Best Model: {best_model}, Best Accuracy:{best_accuracy}")
    model_uri = f"runs:/{best_run_id}/{best_model}_model"
    logging.info(f"Registering best model {model_uri}")
    mlflow.register_model(model_uri, "Best_ML_Model")
    
    
    
try:    
    logging.info("Starting model training")
    train_log_models()
    logging.info("Starting best model registration")    
    register_best_model()    
    logging.info("Completed model training & registration !!")
except Exception as e:
    print(f"Error in model training: {str(e)}")




