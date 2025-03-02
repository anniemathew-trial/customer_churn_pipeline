from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow import DAG

from airflow.operators.bash import BashOperator

default_args = {
    "owner": "Mathew Annie Thampy (2023DC04283)"
}


with DAG(
    dag_id="customer_churn_ml_pipeline",
    start_date=days_ago(1),
    schedule_interval="0 8 * * *", # Daily at 8:00 AM UTC
    catchup=False,
) as dag:
    pull_task = BashOperator(
        task_id="pull_latest_codes",
	bash_command="cd /opt/airflow && dvc pull && git pull",
    )
	
    data_ingestion_task = BashOperator(
        task_id = 'data_ingestion_task',
        bash_command = """python /opt/airflow/executables/data_ingestion.py && \
			NOW=$(date '+%d-%m-%Y') &&\
			cd /opt/airflow && \
			git add logs && \
   			git status && \
                        git commit -m "Updated data ingestion" -a && \
                        git push
                    """,
    )
    
    raw_data_storage_task = BashOperator(
        task_id = 'raw_data_storage_task',
        bash_command = """
			cd /opt/airflow &&\
                        python /opt/airflow/executables/raw_data_storage.py && \
			git rm -r --cached 'opt/airflow/data/raw' && \
			git commit -m "stop tracking data/raw"
                        dvc add /opt/airflow/data/raw && \
                        git add /opt/airflow/data/raw.dvc && \
			git add logs &&\   
   			git status && \
                        git commit -m "Updated raw data storage" -a && \
                        dvc push && git push
                    """
    )
	
    data_validation_task = BashOperator(
        task_id = 'data_validation_task',
        bash_command = """
			cd /opt/airflow &&\
                        dvc pull /opt/airflow/data/raw
                        python /opt/airflow/executables/data_validation.py && \
			git add logs && \   
			git add reports && \
   			git status && \
                        git commit -m "Updated validation" -a && \
                        dvc push && git push
                    """
    )

    data_preparation_task = BashOperator(
        task_id = 'data_preparation_task',
        bash_command = """
			cd /opt/airflow &&\
			python /opt/airflow/executables/data_preparation.py && \
                        dvc add /opt/airflow/data/cleaned && \
                        git add /opt/airflow/data/cleaned.dvc && \
			git add logs && \   
			git add visualization && \
   			git status && \
                        git commit -m "Updated cleaned data version" -a && \
                        dvc push && git push
                    """
    )

    data_transformation_task = BashOperator(
        task_id = 'data_transformation_task',
        bash_command = """
			cd /opt/airflow &&\
                        dvc pull /opt/airflow/data/cleaned
                        python /opt/airflow/executables/data_transformation.py && \
                        dvc add /opt/airflow/data/transformed && \
                        git add /opt/airflow/data/transformed.dvc && \
			git add logs && \
   			git status && \
                        git commit -m "Updated transformed data version" -a && \
                        dvc push && git push
                    """
    )

    data_storage_task = BashOperator(
        task_id = 'data_storage_task',
        bash_command = """
			cd /opt/airflow
                        dvc pull /opt/airflow/data/transformed
                        python /opt/airflow/executables/data_storage.py && \
			git add logs && \
   			git status && \
                        git commit -m "Updated stored data version" -a && \
                        dvc push && git push
                    """
    )

    feature_store_task = BashOperator(
        task_id = 'feature_store_task',
        bash_command = """
			cd /opt/airflow/customer_churn_stats/feature_repo && \
                        feast apply && \
                        feast materialize-incremental $(date -u +'%Y-%m-%dT%H:%M:%S') && \
      			git add /opt/airflow/logs
   			git status && \
                        git commit -m "Updated feature store" -a && \
                        git push
                    """
    )

    model_training_task = BashOperator(
            task_id = 'model_training_task',
            bash_command = """
	    		cd /opt/airflow
       			    python /opt/airflow/executables/model_training.py && \
	      		    git add logs && \
	      		    git add mlruns && \
	        	    git status && \
                            git commit -m "Trained model version" -a && \    
			    git push
                        """
    )

pull_task >> data_ingestion_task >> raw_data_storage_task >> data_validation_task >> data_preparation_task >> data_transformation_task >> data_storage_task >> feature_store_task >> model_training_task
