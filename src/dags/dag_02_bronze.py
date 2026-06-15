"""
DAG – Processamento para a Camada Bronze
Referência: Issue #5
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Adiciona o caminho do pipeline mapeado no Docker
sys.path.insert(0, "/opt/airflow/pipeline")
from bronze_processing import executar

with DAG(
    dag_id="dag_02_bronze",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["bronze", "ecommerce", "projeto-ed", "spark"],
) as dag:

    processamento_bronze = PythonOperator(
        task_id="processamento_bronze",
        python_callable=executar,
    )