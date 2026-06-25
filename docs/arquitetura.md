# Arquitetura e Tecnologias

Nossa stack foi desenhada para criar um Data Lakehouse moderno, com base na arquitetura medalhão.

## Stack Tecnológica

- **Python**: Linguagem principal para scripts e geração de dados.
- **Apache Airflow**: Orquestração das tarefas (DAGs).
- **PySpark**: Motor principal de transformação de dados.
- **Delta Lake**: Formato de armazenamento que traz confiabilidade (ACID) ao Data Lake.
- **MinIO**: Object Storage compatível com S3 (simulando armazenamento em nuvem).
- **PostgreSQL**: Banco de dados relacional para metadados do Airflow.
- **Streamlit**: Framework Python para o dashboard analítico.
- **Docker Compose**: Containerização de toda a infraestrutura para facilitar execução local.

## Arquitetura Medalhão (Camadas de Dados)

O pipeline processa dados sintéticos de e-commerce seguindo as melhores práticas e dividindo o armazenamento nas seguintes camadas:

### Diagrama da Arquitetura

<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

<div class="mermaid">
graph LR
    style A fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    style B fill:#fde68a,stroke:#d97706,stroke-width:2px
    style C fill:#fed7aa,stroke:#c2410c,stroke-width:2px
    style D fill:#e5e7eb,stroke:#4b5563,stroke-width:2px
    style E fill:#fef08a,stroke:#a16207,stroke-width:2px
    style F fill:#bbf7d0,stroke:#15803d,stroke-width:2px

    A[Origem: CSV] -->|Airflow DAG 01| B[(Landing Zone)]
    B -->|PySpark / Delta<br>DAG 02| C[(Camada Bronze)]
    C -->|Limpeza<br>DAG 03| D[(Camada Silver)]
    D -->|Marts Analíticos<br>DAG 04| E[(Camada Gold)]
    E -->|Parquet| F[Dashboard Streamlit]
</div>

### Landing Zone
- Dados brutos, no formato original.
- Arquivos CSV enviados para o bucket `s3://datalake/landing/ecommerce`.

### Camada Bronze
- Dados crus persistidos no formato Delta Lake.
- Permite consultas rápidas aos dados históricos sem alteração estrutural.
- Local: `s3://datalake/bronze/ecommerce`.

### Camada Silver
- Dados limpos, deduplicados e tipados corretamente.
- Tabelas refinadas em formato Delta Lake.
- Local: `s3://datalake/silver/ecommerce`.

### Camada Gold
- Modelagem dimensional (Marts analíticos).
- Dados enriquecidos e agregados com foco em regras de negócio.
- Local: `s3://datalake/gold/ecommerce`.
- Inclui fatos e dimensões, como `fato_vendas`, `faturamento_mensal`, etc.

### Camada Published / Dashboard
- Cópia otimizada em formato Parquet para consumo rápido e leve pelo Streamlit.
- O dashboard consome *somente* os dados publicados a partir da camada Gold.
- Local: `s3://datalake/published/dashboard`.

## Fluxo de Processamento

A ingestão e o processamento de cada etapa são orquestrados por DAGs no Airflow. As cargas de dados são completas (full load), utilizando overwrite da Landing até a camada Gold.
