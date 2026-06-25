# projeto-ed-satc

Projeto final de Engenharia de Dados com pipeline em camadas para dados de
e-commerce e dashboard analitico em Streamlit.

## Documentação Oficial

A documentação completa do projeto, incluindo detalhes de arquitetura, execução e o modelo de dados gerado, está disponível no nosso site do MkDocs:
👉 **[Acessar Documentação do Projeto](https://Polarzinha008.github.io/projeto-ed-satc/)**

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

- Origem: banco relacional PostgreSQL (`ecommerce`) populado via Faker
- Landing: CSVs extraidos do Postgres para `s3://datalake/landing/ecommerce`
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
MINIO_PASSWORD=***
DB_USER=airflow
DB_PASSWORD=***
```

### 2. Subir o ambiente

Entre na pasta `docker` e suba os servicos:

```bash
cd docker
docker compose --env-file ../.env up --build -d
```

Servicos principais:

- Airflow: `http://localhost:8080`
- MinIO Console: `http://localhost:9001`
- Dashboard Streamlit: `http://localhost:8501`
- Postgres de origem: `localhost:5433` (banco `ecommerce`)

### 3. Gerar e carregar os dados de origem

Com o ambiente no ar, instale as dependencias locais do gerador e popule o
banco de origem:

```bash
pip install -r requirements.txt
python scripts/gerar_dados_v2.py
```

Esse comando gera a massa com Faker e carrega as 10 tabelas no Postgres de
origem (`ecommerce`), que sera lido pela camada Landing.

Usuario do Airflow:

- Login: `admin`
- Senha: valor de `DB_PASSWORD` no `.env`

### 4. Executar a DAG

No Airflow, execute a DAG `dag_pipeline_ecommerce`. Ela orquestra todas as
camadas em sequencia atraves de tasks encadeadas:

```text
ingestao_landing -> processamento_bronze -> processamento_silver -> processamento_gold
```

A task `processamento_gold` gera os marts Delta da camada Gold e tambem publica
cópias em Parquet para consumo do dashboard.

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
3. Ticket médio
4. Quantidade de itens vendidos

Fonte dos KPIs:

- `published/dashboard/fato_vendas`
- Derivado de `gold/ecommerce/fato_vendas`

## Métricas e gráficos

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
