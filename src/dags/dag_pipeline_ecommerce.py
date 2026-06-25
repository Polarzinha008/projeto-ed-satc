"""
DAG – Pipeline E-commerce (Arquitetura Medalhão)
Orquestra todas as camadas em uma única DAG: Landing -> Bronze -> Silver -> Gold
"""
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# Adiciona o caminho do pipeline mapeado no Docker
sys.path.insert(0, "/opt/airflow/pipeline")
from landing import executar as executar_landing
from bronze_processing import executar as executar_bronze
from silver_processing import executar as executar_silver
from gold_processing import executar as executar_gold

with DAG(
    dag_id="dag_pipeline_ecommerce",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["ecommerce", "projeto-ed", "spark", "medalhao"],
) as dag:
    ingestao_landing = PythonOperator(
        task_id="ingestao_landing",
        python_callable=executar_landing,
    )
    processamento_bronze = PythonOperator(
        task_id="processamento_bronze",
        python_callable=executar_bronze,
    )
    processamento_silver = PythonOperator(
        task_id="processamento_silver",
        python_callable=executar_silver,
    )
    processamento_gold = PythonOperator(
        task_id="processamento_gold",
        python_callable=executar_gold,
    )

    (
        ingestao_landing
        >> processamento_bronze
        >> processamento_silver
        >> processamento_gold
    )
