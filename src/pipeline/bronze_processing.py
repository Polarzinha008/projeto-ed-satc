"""
Bronze – converte CSVs da Landing para Delta Lake.
Referência: Issue #5
"""

import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

DATA_PARTICAO = datetime.now().strftime("%Y-%m-%d")

TABELAS = [
    "clientes", "enderecos", "categorias", "fornecedores",
    "produtos", "cupons", "pedidos", "itens_pedido",
    "pagamentos", "avaliacoes"
]


def get_spark():
    """Configura e retorna a sessão do Spark com suporte a Delta e S3/MinIO."""
    return (
        SparkSession.builder
        .appName("Bronze Processing")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,org.apache.hadoop:hadoop-aws:3.3.4")
        .getOrCreate()
    )


def processar_tabela(spark, tabela: str):
    """Lê da Landing e grava na Bronze em formato Delta."""
    origem = f"s3a://{BUCKET}/landing/ecommerce/{tabela}/{DATA_PARTICAO}/{tabela}.csv"
    destino = f"s3a://{BUCKET}/bronze/ecommerce/{tabela}/"

    print(f"Processando tabela: {tabela}...")

    # Lê o CSV
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(origem)
    )

    # Adiciona colunas de controle
    df = (
        df.withColumn("dt_ingestao", current_timestamp())
          .withColumn("nm_arquivo_origem", lit(f"{tabela}.csv"))
    )

    # Grava em Delta
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .save(destino)
    )
    print(f"Bronze gravada: {tabela} ({df.count()} linhas)")


def executar():
    print("Iniciando processamento da Camada Bronze...\n")
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")

    for tabela in TABELAS:
        processar_tabela(spark, tabela)

    spark.stop()
    print("\n Camada Bronze concluída!")


if __name__ == "__main__":
    executar()
