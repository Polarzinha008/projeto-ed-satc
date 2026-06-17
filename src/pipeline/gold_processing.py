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

    # junta itens + produtos + categorias
    df = itens.join(produtos, itens.id_produto == produtos.id_produto)
    df = df.join(categorias, produtos.id_categoria == categorias.id_categoria)

    # receita de cada item
    df = df.withColumn("receita", col("preco_unitario"))

    # faturamento por categoria
    resultado = df.groupBy("id_categoria", "nome_categoria").agg(sum("receita"))

    resultado.write.format("delta").mode("overwrite").save(f"s3a://{BUCKET}/gold/ecommerce/faturamento_por_categoria/")

    print("Camada Gold concluída!")
    spark.stop()

if __name__ == "__main__":
    executar()