"""
Silver – limpeza e padronização dos dados da Bronze.
Referência: Issue #6
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, trim
from pyspark.sql.types import StringType

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = os.getenv("MINIO_USER", "admin")
SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

# Dicionário com as chaves primárias de cada tabela para remover duplicatas
CHAVES_PRIMARIAS = {
    "clientes": "id_cliente",
    "enderecos": "id_endereco",
    "categorias": "id_categoria",
    "fornecedores": "id_fornecedor",
    "produtos": "id_produto",
    "cupons": "id_cupom",
    "pedidos": "id_pedido",
    "itens_pedido": "id_item",
    "pagamentos": "id_pagamento",
    "avaliacoes": "id_avaliacao",
}

def get_spark():
    """Configura e retorna a sessão do Spark com suporte a Delta e S3/MinIO."""
    return (
        SparkSession.builder
        .appName("Silver Processing")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,org.apache.hadoop:hadoop-aws:3.3.4")
        .getOrCreate()
    )

def limpar_dados(df, tabela):
    """Aplica as regras de limpeza da camada Silver."""
    # 1. Remove duplicatas com base na chave primária
    pk = CHAVES_PRIMARIAS[tabela]
    df_limpo = df.dropDuplicates([pk])
    
    # 2. Remove espaços em branco extras do início e fim de colunas de texto (trim)
    for field in df_limpo.schema.fields:
        if isinstance(field.dataType, StringType):
            df_limpo = df_limpo.withColumn(field.name, trim(df_limpo[field.name]))
            
    # 3. Adiciona a data de processamento na Silver
    df_limpo = df_limpo.withColumn("dt_processamento_silver", current_timestamp())
    
    return df_limpo

def processar_tabela(spark, tabela: str):
    """Lê da Bronze, limpa e grava na Silver em formato Delta."""
    origem = f"s3a://{BUCKET}/bronze/ecommerce/{tabela}/"
    destino = f"s3a://{BUCKET}/silver/ecommerce/{tabela}/"
    
    print(f"Processando tabela: {tabela} na camada Silver...")
    
    # Lê os dados em formato Delta da Bronze
    df = spark.read.format("delta").load(origem)
    
    # Aplica a limpeza
    df = limpar_dados(df, tabela)
    
    # Grava na Silver
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .save(destino)
    )
    print(f"Silver gravada: {tabela} ({df.count()} linhas após limpeza)")

def executar():
    print("Iniciando processamento da Camada Silver...\n")
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")
    
    for tabela in CHAVES_PRIMARIAS.keys():
        processar_tabela(spark, tabela)
        
    spark.stop()
    print("\n Camada Silver concluída!")

if __name__ == "__main__":
    executar()