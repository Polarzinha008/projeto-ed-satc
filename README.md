# projeto-ed-satc

Projeto final de Engenharia de Dados com pipeline em camadas para dados de
e-commerce e dashboard analitico em Streamlit.

## Apresentação do Projeto

Os slides e a explicação técnica detalhada da arquitetura deste projeto podem ser acessados em:
👉 **[Apresentação no Gamma](https://gamma.app/docs/Arquitetura-Medalhao-com-Apache-Airflow-PySpark-e-Delta-Lake-r545f5owwozmh7a)**

## Stack

- Python
- Apache Airflow
- PySpark
- Delta Lake
- MinIO
- PostgreSQL
- Streamlit
- Docker Compose

## Camadas de dados

O pipeline processa dados sinteticos de e-commerce nas seguintes camadas:

- Landing: CSVs enviados para `s3://datalake/landing/ecommerce`
- Bronze: dados convertidos para Delta em `s3://datalake/bronze/ecommerce`
- Silver: dados limpos e deduplicados em `s3://datalake/silver/ecommerce`
- Gold: marts analiticos em `s3://datalake/gold/ecommerce`
- Publicacao do dashboard: Parquets derivados da Gold em `s3://datalake/published/dashboard`

O dashboard consome somente os dados publicados a partir da camada Gold.

## Como executar

### 1. Configurar variaveis de ambiente

Crie um arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Valores padrao usados no projeto:

```env
MINIO_USER=admin
MINIO_PASSWORD=admin123
DB_USER=airflow
DB_PASSWORD=airflow
```

### 2. Gerar os dados de origem

Instale as dependencias locais do gerador de dados:

```bash
pip install -r requirements.txt
```

Na raiz do projeto, execute:

```bash
python scripts/gerar_dados_v2.py
```

Esse comando cria os CSVs em `dados_origem/`.

### 3. Subir o ambiente

Entre na pasta `docker` e suba os servicos:

```bash
cd docker
docker compose --env-file ../.env up --build
```

Servicos principais:

- Airflow: `http://localhost:8080`
- MinIO Console: `http://localhost:9001`
- Dashboard Streamlit: `http://localhost:8501`

Usuario do Airflow:

- Login: `admin`
- Senha: valor de `DB_PASSWORD` no `.env`

### 4. Executar as DAGs

No Airflow, execute as DAGs nesta ordem:

1. `dag_01_landing`
2. `dag_02_bronze`
3. `dag_03_silver`
4. `dag_04_gold`

A DAG `dag_04_gold` gera os marts Delta da camada Gold e tambem publica copias
em Parquet para consumo do dashboard.

## Dashboard

Acesse:

```text
http://localhost:8501
```

Se os dados ainda nao existirem, o dashboard exibira uma mensagem orientando
executar as DAGs ate a camada Gold.

## KPIs principais

O dashboard One Page View apresenta exatamente 4 KPIs principais:

1. Receita total
2. Quantidade de pedidos
3. Ticket medio
4. Quantidade de itens vendidos

Fonte dos KPIs:

- `published/dashboard/fato_vendas`
- Derivado de `gold/ecommerce/fato_vendas`

## Metricas e graficos

Graficos obrigatorios:

1. Evolucao do faturamento mensal
   - Fonte: `published/dashboard/faturamento_mensal`
   - Derivado de `gold/ecommerce/faturamento_mensal`

2. Faturamento por categoria
   - Fonte: `published/dashboard/faturamento_por_categoria`
   - Derivado de `gold/ecommerce/faturamento_por_categoria`

Extras incluidos:

- Ranking de top produtos por receita
  - Fonte: `published/dashboard/top_produtos`
- Tabela resumida de vendas por mes e categoria
  - Fonte: `published/dashboard/fato_vendas`

## Marts Gold utilizados

- `gold/ecommerce/fato_vendas`
- `gold/ecommerce/faturamento_mensal`
- `gold/ecommerce/faturamento_por_categoria`
- `gold/ecommerce/top_produtos`
