"""
Landing Zone – lê CSVs locais e envia para o MinIO.
Referência: Issue #3 - Ingestão para Landing Zone
"""

import boto3
import os
from botocore.client import Config
from datetime import datetime

# Configurações do MinIO
MINIO_ENDPOINT = "https://minio:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_PASSWORD", "admin123")
BUCKET = "datalake"

# Pasta com os CSVs gerados pelo gerar_dados_v2.py
DATA_ORIGEM = "/opt/airflow/dados_origem"

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


def criar_bucket_se_nao_existir(client):
    """Cria o bucket caso ainda não exista."""
    buckets = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    if BUCKET not in buckets:
        client.create_bucket(Bucket=BUCKET)
        print(f"✅ Bucket '{BUCKET}' criado.")
    else:
        print(f"ℹ️  Bucket '{BUCKET}' já existe.")


def upload_tabela(client, tabela: str):
    """Faz upload de um CSV para a Landing Zone."""
    arquivo_local = os.path.join(DATA_ORIGEM, f"{tabela}.csv")
    destino = f"landing/ecommerce/{tabela}/{DATA_PARTICAO}/{tabela}.csv"

    if not os.path.exists(arquivo_local):
        print(f"⚠️  Arquivo não encontrado: {arquivo_local}")
        return

    client.upload_file(arquivo_local, BUCKET, destino)
    print(f"📤 {tabela}.csv → s3://{BUCKET}/{destino}")


def executar():
    """Executa o pipeline da Landing Zone."""
    print("🚀 Iniciando ingestão para Landing Zone...\n")
    client = get_client()
    criar_bucket_se_nao_existir(client)

    for tabela in TABELAS:
        upload_tabela(client, tabela)

    print(f"\n✅ Landing Zone concluída! {len(TABELAS)} tabelas processadas.")


if __name__ == "__main__":
    executar()
