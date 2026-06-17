"""
Gold – camada de negócio a partir da Silver.
Referência: Issue #7
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = os.getenv("MINIO_USER", "admin")
SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

def get_spark():
    """Configura e retorna a sessão do Spark com suporte a Delta e S3/MinIO."""
    return (
        SparkSession.builder
        .appName("Gold Processing")
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

def executar():
    print("Iniciando processamento da Camada Gold...")
    spark = get_spark()

    itens = spark.read.format("delta").load(f"s3a://{BUCKET}/silver/ecommerce/itens_pedido/")
    produtos = spark.read.format("delta").load(f"s3a://{BUCKET}/silver/ecommerce/produtos/")
    categorias = spark.read.format("delta").load(f"s3a://{BUCKET}/silver/ecommerce/categorias/")
    pedidos = spark.read.format("delta").load(f"s3a://{BUCKET}/silver/ecommerce/pedidos/")

    # junto pedidos p/ descartar cancelados e calculo a receita correta (qtd * preço)
    base = (
        itens.join(pedidos, "id_pedido")
            .filter(col("status_pedido") != "Cancelado")
            .join(produtos, "id_produto")
            .join(categorias, "id_categoria")
            .withColumn("receita", col("quantidade") * col("preco_unitario"))
    )

    # mart 1: faturamento por categoria (com nome de coluna decente)
    fat_categoria = base.groupBy("nome_categoria").agg(sum("receita").alias("receita_total"))
    fat_categoria.write.format("delta").mode("overwrite").save(f"s3a://{BUCKET}/gold/ecommerce/faturamento_por_categoria/")

    # mart 2: tabela fato com as vendas detalhadas
    base.write.format("delta").mode("overwrite").save(f"s3a://{BUCKET}/gold/ecommerce/fato_vendas/")

    print("Camada Gold concluída!")
    spark.stop()

if __name__ == "__main__":
    executar()