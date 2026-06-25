"""
Landing Zone – lê as tabelas do banco de origem (Postgres) e envia para o MinIO.
Origem SQL grava o formato bruto em CSV. Referência: Issue #3
"""

import os
import tempfile

import boto3
import psycopg2
from botocore.client import Config
from datetime import datetime

# Configurações do MinIO
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

# Banco de origem (Postgres do docker-compose)
PG_HOST = os.getenv("PG_ORIGEM_HOST", "postgres-origem")
PG_PORT = os.getenv("PG_ORIGEM_PORT", "5432")
PG_DB = os.getenv("PG_ORIGEM_DB", "ecommerce")
PG_USER = os.getenv("DB_USER", "airflow")
PG_PASSWORD = os.getenv("DB_PASSWORD", "airflow")

# Partição diária
DATA_PARTICAO = datetime.now().strftime("%Y-%m-%d")

# Lista das 10 tabelas
TABELAS = [
    "clientes", "enderecos", "categorias", "fornecedores",
    "produtos", "cupons", "pedidos", "itens_pedido",
    "pagamentos", "avaliacoes"
]


def get_client():
    """Cria um cliente boto3 conectado ao MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        use_ssl=False,
        config=Config(signature_version="s3v4"),
    )


def get_conexao():
    """Abre conexão com o banco de origem."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )


def criar_bucket_se_nao_existir(client):
    """Cria o bucket caso ainda não exista (idempotente)."""
    try:
        client.create_bucket(Bucket=BUCKET)
        print(f"Bucket '{BUCKET}' criado.")
    except (
        client.exceptions.BucketAlreadyOwnedByYou,
        client.exceptions.BucketAlreadyExists,
    ):
        print(f"Bucket '{BUCKET}' já existe.")


def upload_tabela(client, conn, tabela: str):
    """Exporta uma tabela do Postgres para CSV e envia para a Landing Zone."""
    destino = f"landing/ecommerce/{tabela}/{DATA_PARTICAO}/{tabela}.csv"

    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".csv", delete=False
    ) as tmp:
        caminho_tmp = tmp.name
        with conn.cursor() as cur:
            cur.copy_expert(
                f"COPY {tabela} TO STDOUT WITH CSV HEADER", tmp
            )

    try:
        client.upload_file(caminho_tmp, BUCKET, destino)
        print(f"{tabela} → s3://{BUCKET}/{destino}")
    finally:
        os.remove(caminho_tmp)


def executar():
    """Executa o pipeline da Landing Zone."""
    print("Iniciando ingestão para Landing Zone...\n")
    client = get_client()
    criar_bucket_se_nao_existir(client)

    conn = get_conexao()
    try:
        for tabela in TABELAS:
            upload_tabela(client, conn, tabela)
    finally:
        conn.close()

    print(f"\n Landing Zone concluída! {len(TABELAS)} tabelas processadas.")


if __name__ == "__main__":
    executar()
