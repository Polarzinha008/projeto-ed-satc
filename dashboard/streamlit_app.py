"""Exibe os indicadores e graficos do e-commerce a partir da camada Gold."""

import os

import altair as alt
import pandas as pd
import s3fs
import streamlit as st


BUCKET = os.getenv("DATALAKE_BUCKET", "datalake")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_USER = os.getenv("MINIO_USER", "admin")
MINIO_PASSWORD = os.getenv("MINIO_PASSWORD", "admin123")
PUBLISHED_PREFIX = os.getenv("DASHBOARD_PREFIX", "published/dashboard")


st.set_page_config(
    page_title="Dashboard E-commerce",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)


REQUIRED_COLUMNS = {
    "fato_vendas": {
        "id_pedido",
        "quantidade",
        "receita",
        "ano_mes",
        "nome_produto",
        "nome_categoria",
        "data_pedido",
    },
    "faturamento_mensal": {"ano_mes", "receita_total", "qtd_pedidos"},
    "faturamento_por_categoria": {"nome_categoria", "receita_total", "qtd_vendida"},
    "top_produtos": {"nome_produto", "receita_total", "qtd_vendida", "nota_media"},
}


def format_currency(value: float) -> str:
    """Formata um valor numerico como moeda brasileira."""
    formatted = f"R$ {value:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value: float) -> str:
    """Formata um valor numerico com separador de milhares."""
    formatted = f"{value:,.0f}"
    return formatted.replace(",", ".")


@st.cache_resource(show_spinner=False)
def get_filesystem() -> s3fs.S3FileSystem:
    """Cria o cliente de acesso ao armazenamento MinIO."""
    return s3fs.S3FileSystem(
        key=MINIO_USER,
        secret=MINIO_PASSWORD,
        client_kwargs={"endpoint_url": MINIO_ENDPOINT},
        config_kwargs={"s3": {"addressing_style": "path"}},
    )


@st.cache_data(show_spinner=False)
def load_mart(nome_mart: str) -> pd.DataFrame:
    """Carrega e valida um mart publicado para o dashboard."""
    fs = get_filesystem()
    path = f"{BUCKET}/{PUBLISHED_PREFIX}/{nome_mart}"

    if not fs.exists(path):
        raise FileNotFoundError(path)

    df = pd.read_parquet(path, filesystem=fs)
    missing_columns = REQUIRED_COLUMNS[nome_mart] - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{nome_mart}: colunas ausentes: {missing}")

    return df


def show_missing_data_message(error: Exception) -> None:
    """Exibe instrucoes quando os dados publicados nao estao disponiveis."""
    st.title("Dashboard E-commerce")
    st.info(
        "Os dados publicados da camada Gold ainda nao foram encontrados. "
        "Gere os CSVs, suba o ambiente e execute as DAGs ate `dag_04_gold` no Airflow."
    )
    st.code(
        "python scripts/gerar_dados_v2.py\n"
        "cd docker\n"
        "docker compose --env-file ../.env up --build\n\n"
        "No Airflow, execute em ordem:\n"
        "dag_01_landing -> dag_02_bronze -> dag_03_silver -> dag_04_gold",
        language="bash",
    )
    st.caption(f"Detalhe tecnico: {error}")


def build_line_chart(faturamento_mensal: pd.DataFrame) -> alt.Chart:
    """Cria o grafico de linha do faturamento mensal."""
    chart_data = faturamento_mensal.sort_values("ano_mes").copy()

    return (
        alt.Chart(chart_data)
        .mark_line(point=True)
        .encode(
            x=alt.X("ano_mes:N", title="Mes"),
            y=alt.Y("receita_total:Q", title="Receita total"),
            tooltip=[
                alt.Tooltip("ano_mes:N", title="Mes"),
                alt.Tooltip("receita_total:Q", title="Receita", format=",.2f"),
                alt.Tooltip("qtd_pedidos:Q", title="Pedidos"),
            ],
        )
        .properties(height=320)
    )


def build_category_chart(faturamento_por_categoria: pd.DataFrame) -> alt.Chart:
    """Cria o grafico de barras do faturamento por categoria."""
    chart_data = faturamento_por_categoria.nlargest(12, "receita_total").sort_values(
        "receita_total"
    )

    return (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("receita_total:Q", title="Receita total"),
            y=alt.Y("nome_categoria:N", title="Categoria", sort="-x"),
            tooltip=[
                alt.Tooltip("nome_categoria:N", title="Categoria"),
                alt.Tooltip("receita_total:Q", title="Receita", format=",.2f"),
                alt.Tooltip("qtd_vendida:Q", title="Itens vendidos"),
            ],
        )
        .properties(height=320)
    )


def main() -> None:
    """Renderiza o dashboard e seus indicadores."""
    try:
        fato_vendas = load_mart("fato_vendas")
        faturamento_mensal = load_mart("faturamento_mensal")
        faturamento_por_categoria = load_mart("faturamento_por_categoria")
        top_produtos = load_mart("top_produtos")
    except Exception as exc:
        show_missing_data_message(exc)
        return

    receita_total = float(fato_vendas["receita"].sum())
    qtd_pedidos = int(fato_vendas["id_pedido"].nunique())
    ticket_medio = receita_total / qtd_pedidos if qtd_pedidos else 0
    qtd_itens = int(fato_vendas["quantidade"].sum())

    st.title("Dashboard E-commerce")
    st.caption("Fonte: camada Gold publicada em `published/dashboard` no bucket MinIO.")

    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.metric("Receita total", format_currency(receita_total))
    kpi_2.metric("Quantidade de pedidos", format_number(qtd_pedidos))
    kpi_3.metric("Ticket médio", format_currency(ticket_medio))
    kpi_4.metric("Quantidade de itens vendidos", format_number(qtd_itens))

    st.divider()

    chart_1, chart_2 = st.columns(2)
    with chart_1:
        st.subheader("Evolução do faturamento mensal")
        st.altair_chart(build_line_chart(faturamento_mensal), use_container_width=True)

    with chart_2:
        st.subheader("Faturamento por categoria")
        st.altair_chart(
            build_category_chart(faturamento_por_categoria), use_container_width=True
        )

    st.divider()

if __name__ == "__main__":
    main()
