"""
DAG – Processamento para a Camada Silver
Referência: Issue #6
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Adiciona o caminho do pipeline mapeado no Docker
sys.path.insert(0, "/opt/airflow/pipeline")
from silver_processing import executar

with DAG(
    dag_id="dag_03_silver",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["silver", "ecommerce", "projeto-ed", "spark"],
) as dag:

    processamento_silver = PythonOperator(
        task_id="processamento_silver",
        python_callable=executar,
    )