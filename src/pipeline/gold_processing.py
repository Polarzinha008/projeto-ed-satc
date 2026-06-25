"""
Gold – camada de negócio (tabela fato + marts analíticos) a partir da Silver.
Gera uma tabela fato de vendas e agregações.
Referência: Issue #7
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
ACCESS_KEY = os.getenv("MINIO_USER", "admin")
SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

# Status de pedido que NÃO conta como venda concretizada (faturamento)
STATUS_INVALIDOS = ["Cancelado"]


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


def ler_silver(spark, tabela: str):
    """Lê uma tabela já limpa da camada Silver (formato Delta)."""
    return spark.read.format("delta").load(f"s3a://{BUCKET}/silver/ecommerce/{tabela}/")


def salvar_gold(df, nome_mart: str):
    """Grava uma tabela Gold em Delta e publica uma copia Parquet para o dashboard."""
    df = df.withColumn("dt_processamento_gold", F.current_timestamp())
    destino_gold = f"s3a://{BUCKET}/gold/ecommerce/{nome_mart}/"
    destino_dashboard = f"s3a://{BUCKET}/published/dashboard/{nome_mart}/"

    df.write.format("delta").mode("overwrite").save(destino_gold)
    df.write.format("parquet").mode("overwrite").save(destino_dashboard)

    print(f"Gold gravada: {nome_mart} ({df.count()} linhas)")
    print(f"Publicacao dashboard gravada: {nome_mart} -> {destino_dashboard}")


def construir_fato_vendas(spark):
    """Monta a tabela fato de vendas (grão = item de pedido), apenas com pedidos válidos.

    Selecionamos explicitamente as colunas de negócio de cada tabela para não arrastar
    colunas de controle homônimas (ex.: dt_processamento_silver), que ficariam duplicadas
    após os joins e quebrariam a escrita em Delta.
    """
    itens = ler_silver(spark, "itens_pedido").select("id_item", "id_pedido", "id_produto", "quantidade")
    pedidos = ler_silver(spark, "pedidos").select("id_pedido", "id_cliente", "data_pedido", "status_pedido")
    produtos = ler_silver(spark, "produtos").select("id_produto", "id_categoria", "nome_produto", "preco_unitario")
    categorias = ler_silver(spark, "categorias").select("id_categoria", "nome_categoria")

    # Mantém apenas pedidos que viraram venda (descarta cancelados)
    pedidos_validos = pedidos.filter(~F.col("status_pedido").isin(STATUS_INVALIDOS))

    fato = (
        itens
        .join(pedidos_validos, "id_pedido")   # join por nome coalesce a chave
        .join(produtos, "id_produto")
        .join(categorias, "id_categoria")
        .withColumn("receita", F.col("quantidade") * F.col("preco_unitario"))
        .withColumn("ano_mes", F.date_format(F.col("data_pedido").cast("timestamp"), "yyyy-MM"))
    )
    return fato


def executar():
    print("Iniciando processamento da Camada Gold...")
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")

    # Tabela fato é reutilizada por todos os marts -> cache para não reprocessar os joins
    fato = construir_fato_vendas(spark).cache()

    # 1) Fato de vendas detalhada (grão de item) – base para BI
    salvar_gold(
        fato.select(
            "id_item", "id_pedido", "id_cliente", "id_produto", "nome_produto",
            "id_categoria", "nome_categoria", "quantidade", "preco_unitario",
            "receita", "data_pedido", "ano_mes",
        ),
        "fato_vendas",
    )

    # 2) Faturamento por categoria
    salvar_gold(
        fato.groupBy("id_categoria", "nome_categoria")
            .agg(
                F.round(F.sum("receita"), 2).alias("receita_total"),
                F.sum("quantidade").alias("qtd_vendida"),
            )
            .orderBy(F.desc("receita_total")),
        "faturamento_por_categoria",
    )

    # 3) Faturamento mensal (série temporal ano-mês)
    salvar_gold(
        fato.groupBy("ano_mes")
            .agg(
                F.round(F.sum("receita"), 2).alias("receita_total"),
                F.countDistinct("id_pedido").alias("qtd_pedidos"),
            )
            .orderBy("ano_mes"),
        "faturamento_mensal",
    )

    # 4) Top produtos por receita, com nota média (left join p/ manter produtos sem avaliação)
    avaliacoes = ler_silver(spark, "avaliacoes").select("id_produto", "nota")
    nota_media = avaliacoes.groupBy("id_produto").agg(F.round(F.avg("nota"), 2).alias("nota_media"))
    salvar_gold(
        fato.groupBy("id_produto", "nome_produto")
            .agg(
                F.round(F.sum("receita"), 2).alias("receita_total"),
                F.sum("quantidade").alias("qtd_vendida"),
            )
            .join(nota_media, "id_produto", "left")
            .orderBy(F.desc("receita_total")),
        "top_produtos",
    )

    fato.unpersist()
    spark.stop()
    print("Camada Gold concluída!")


if __name__ == "__main__":
    executar()
