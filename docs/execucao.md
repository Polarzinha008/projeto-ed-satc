# Como Executar o Projeto

Para testar o pipeline e visualizar o dashboard, siga os passos abaixo para preparar o ambiente local.

## 1. Configurar variáveis de ambiente

Na raiz do projeto, crie um arquivo `.env` a partir do arquivo de exemplo fornecido:

```bash
cp .env.example .env
```

**Valores padrão usados no projeto:**
```env
MINIO_USER=admin
MINIO_PASSWORD=***
DB_USER=airflow
DB_PASSWORD=***
```

## 2. Gerar os dados de origem

Este projeto utiliza um gerador de dados sintéticos para simular o e-commerce. Instale as dependências locais primeiro:

```bash
pip install -r requirements.txt
```

Em seguida, na raiz do projeto, execute o script de geração:

```bash
python scripts/gerar_dados_v2.py
```

> **Nota:** Esse comando criará os arquivos CSVs brutos dentro da pasta `dados_origem/`.

## 3. Subir a Infraestrutura (Docker)

Entre na pasta `docker` e suba todos os serviços definidos no docker-compose:

```bash
cd docker
docker compose --env-file ../.env up --build -d
```

### Serviços e Acessos principais:

| Serviço | URL | Credenciais |
| :--- | :--- | :--- |
| **Apache Airflow** | [http://localhost:8080](http://localhost:8080) | `admin` / valor de `DB_PASSWORD` |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | valor de `MINIO_USER` / `MINIO_PASSWORD` |
| **Streamlit Dashboard** | [http://localhost:8501](http://localhost:8501) | N/A |

## 4. Executar as DAGs no Airflow

Acesse a interface do Airflow e ative as DAGs em sequência, esperando a anterior concluir antes de iniciar a próxima:

1. `dag_01_landing` - Move dados gerados para o storage (Landing Zone).
2. `dag_02_bronze` - Ingestão para o Delta Lake (Camada Bronze).
3. `dag_03_silver` - Limpeza e deduplicação (Camada Silver).
4. `dag_04_gold` - Criação dos Marts analíticos e exportação para o Dashboard.

> **Importante:** A `dag_04_gold` não só cria os marts em Delta, mas também publica as cópias finais em formato Parquet para o Streamlit consumir. Após o término com sucesso da camada Gold, o dashboard estará com os dados prontos.
