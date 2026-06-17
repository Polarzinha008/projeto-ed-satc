"""
DAG – Processamento para a Camada Gold
Referência: Issue #7
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Adiciona o caminho do pipeline mapeado no Docker
sys.path.insert(0, "/opt/airflow/pipeline")
from gold_processing import executar

with DAG(
    dag_id="dag_04_gold",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["gold", "ecommerce", "projeto-ed", "spark"],
) as dag:

    processamento_gold = PythonOperator(
        task_id="processamento_gold",
        python_callable=executar,
    )
