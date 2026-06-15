"""
DAG – Ingestão para Landing Zone
Referência: Issue #3
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Adiciona o caminho do pipeline mapeado no Docker para o Airflow encontrar o script
sys.path.insert(0, "/opt/airflow/pipeline")
from landing import executar

with DAG(
    dag_id="dag_01_landing",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["landing", "ecommerce", "projeto-ed"],
) as dag:

    ingestao_landing = PythonOperator(
        task_id="ingestao_landing",
        python_callable=executar,
    )