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
        task_id="pull",
	bash_command="cd /opt/airflow && dvc pull && git pull",
    )
    # Data ingestion and raw data storage to Amazon S3 using DVC
    data_ingestion_task = BashOperator(
        task_id = 'data_ingestion_task',
        bash_command = """python /opt/airflow/executables/data_ingestion.py && \
			cd /opt/airflow && \
			git rm -r --cached 'data/raw'
			git commit -m "stop tracking data/raw"
                        dvc add /opt/airflow/data/raw && \
                        git add /opt/airflow/data/raw.dvc && \
                        git commit -m "Updated raw data version" -a && \
                        dvc push && git push
                    """,
    )
    
    data_validation_task = BashOperator(
        task_id = 'data_validation_task',
        bash_command = """
			cd /opt/airflow
                        dvc pull /opt/airflow/data/raw
                        python /opt/airflow/executables/data_validation.py && \
			git rm -r --cached 'reports'
			git commit -m "stop tracking reports"
                        dvc add /opt/airflow/reports/csv_validation_report.csv && \
                        git add /opt/airflow/reports/csv_validation_report.csv.dvc && \
                        git commit -m "Updated validation" && \
                        dvc push && git push
                    """
    )

    data_preparation_task = BashOperator(
        task_id = 'data_preparation_task',
        bash_command = """
			cd /opt/airflow
			python /opt/airflow/executables/data_preparation.py && \
                        dvc add /opt/airflow/data/cleaned && \
                        dvc add /opt/airflow/visualization && \
                        git add /opt/airflow/data/cleaned.dvc && \
                        git add /opt/airflow/visualization.dvc && \
                        git commit -m "Updated cleaned data version" && \
                        dvc push
                    """
    )

    data_transformation_task = BashOperator(
        task_id = 'data_transformation_task',
        bash_command = """
			cd /opt/airflow
                        dvc pull /opt/airflow/data/cleaned
                        python /opt/airflow/executables/data_transformation.py && \
                        dvc add /opt/airflow/data/transformed && \
                        git add /opt/airflow/data/transformed.dvc && \
                        git commit -m "Updated transformed data version" && \
                        dvc push
                    """
    )

    data_storage_task = BashOperator(
        task_id = 'data_storage_task',
        bash_command = """
			cd /opt/airflow
                        dvc pull /opt/airflow/data/transformed
                        python /opt/airflow/executables/data_storage.py && \
                        dvc add /opt/airflow/data/storage && \
                        git add /opt/airflow/data/storage.dvc && \
                        git commit -m "Updated stored data version" && \
                        dvc push
                    """
    )

    feature_store_task = BashOperator(
        task_id = 'feature_store_task',
        bash_command = """
			cd /opt/airflow
                        feast init
                        python /opt/airflow/executables/feature_store.py && \
                        dvc add /opt/airflow/data/features && \
                        git add /opt/airflow/data/features.dvc && \
                        git commit -m "Updated feature store" && \
                        dvc push
                    """
    )

    model_training_task = BashOperator(
            task_id = 'model_training_task',
            bash_command = """
	    		cd /opt/airflow
	    		    python /opt/airflow/executables/model_training.py && \
                            dvc add /opt/airflow/models/model.pki && \
                            git add /opt/airflow/models/model.pki.dvc && \
                            git commit -m "Trained model version" && \
                            dvc push
                        """
    )
    model_evaluation_task = BashOperator(
            task_id = 'model_evaluation_task',
            bash_command = """
	    		cd /opt/airflow
                            dvc pull /opt/airflow/models/model.pkl 
                            python /opt/airflow/executables/model_evaluation.py && \
                            dvc add /opt/airflow/reports/evaluation.csv && \
                            git add /opt/airflow/reports/evaluation.csv.dvc && \
                            git commit -m "Updated model evaluation report" && \
                            dvc push
                        """
    )

pull_task >> data_ingestion_task >> data_validation_task >> data_preparation_task >> data_transformation_task >> data_storage_task >> feature_store_task
feature_store_task >> model_training_task >> model_evaluation_task
