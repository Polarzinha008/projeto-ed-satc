import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import os

from sqlalchemy import create_engine

# Inicializa o Faker configurado para o Brasil
fake = Faker(['pt_BR'])

# Conexão com o banco de origem (postgres)
PG_USER = os.getenv("DB_USER", "airflow")
PG_PASSWORD = os.getenv("DB_PASSWORD", "airflow")
PG_HOST = os.getenv("PG_ORIGEM_HOST", "localhost")
PG_PORT = os.getenv("PG_ORIGEM_PORT", "5433")
PG_DB = os.getenv("PG_ORIGEM_DB", "ecommerce")

# Definição dos volumes exatos para somar 100.000 registros
VOLUMES = {
    "categorias": 50,
    "cupons": 150,
    "fornecedores": 800,
    "produtos": 5000,
    "clientes": 12000,
    "enderecos": 12000,
    "pedidos": 15000,
    "pagamentos": 15000,
    "avaliacoes": 15000,
    "itens_pedido": 25000
}

total_geral = sum(VOLUMES.values())
print(
    f"Configurado para gerar {total_geral} registros no total das 10 tabelas."
)

DATA_INICIO = datetime(2023, 6, 1)
DATA_FIM = datetime(2026, 6, 1)


def gerar_data_aleatoria(inicio, fim):
    """Gera uma data aleatoria dentro do intervalo informado."""
    delta = fim - inicio
    dias_aleatorios = random.randint(0, delta.days)
    return (inicio + timedelta(days=dias_aleatorios)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )


print("Iniciando a geração da massa de dados...")

# 1. CATEGORIAS (50)
categorias = []
for idx in range(1, VOLUMES["categorias"] + 1):
    categorias.append({
        "id_categoria": idx,
        "nome_categoria": f"Subcategoria {fake.word().capitalize()}-{idx}"
    })
df_categorias = pd.DataFrame(categorias)
print(f"1/10 - Categorias: {len(df_categorias)} linhas")

# 2. CUPONS (150)
cupons = []
for idx in range(1, VOLUMES["cupons"] + 1):
    cupons.append({
        "id_cupom": idx,
        "codigo": f"PROMO{idx:03d}",
        "percentual_desconto": random.choice([5, 10, 15, 20])
    })
df_cupons = pd.DataFrame(cupons)
print(f"2/10 - Cupons: {len(df_cupons)} lines")

# 3. FORNECEDORES (800)
fornecedores = []
for idx in tqdm(
    range(1, VOLUMES["fornecedores"] + 1),
    desc="3/10 - Fornecedores"
):
    fornecedores.append({
        "id_fornecedor": idx,
        "nome_fornecedor": fake.company(),
        "cnpj": fake.cnpj(),
        "contato_email": fake.company_email()
    })
df_fornecedores = pd.DataFrame(fornecedores)

# 4. PRODUTOS (5.000)
produtos = []
for idx in tqdm(range(1, VOLUMES["produtos"] + 1), desc="4/10 - Produtos"):
    produtos.append({
        "id_produto": idx,
        "id_categoria": random.randint(1, VOLUMES["categorias"]),
        "id_fornecedor": random.randint(1, VOLUMES["fornecedores"]),
        "nome_produto": f"Item Tech {fake.word().upper()}-{idx}",
        "preco_unitario": round(random.uniform(50.0, 5000.0), 2)
    })
df_produtos = pd.DataFrame(produtos)

# 5. CLIENTES (12.000)
clientes = []
for idx in tqdm(range(1, VOLUMES["clientes"] + 1), desc="5/10 - Clientes"):
    clientes.append({
        "id_cliente": idx,
        "nome": fake.name(),
        "email": fake.unique.email(),
        "cpf": fake.unique.cpf(),
        "data_cadastro": gerar_data_aleatoria(DATA_INICIO, DATA_FIM)
    })
df_clientes = pd.DataFrame(clientes)

# 6. ENDEREÇOS (12.000)
enderecos = []
for idx in tqdm(range(1, VOLUMES["enderecos"] + 1), desc="6/10 - Endereços"):
    enderecos.append({
        "id_endereco": idx,
        "id_cliente": idx,
        "rua": fake.street_name(),
        "numero": fake.building_number(),
        "cidade": fake.city(),
        "estado": fake.state_abbr(),
        "cep": fake.postcode()
    })
df_enderecos = pd.DataFrame(enderecos)

# 7. PEDIDOS (15.000)
pedidos = []
for idx in tqdm(range(1, VOLUMES["pedidos"] + 1), desc="7/10 - Pedidos"):
    id_cliente_sorteado = random.randint(1, VOLUMES["clientes"])
    data_cadastro_cliente = df_clientes.loc[
        id_cliente_sorteado - 1, 'data_cadastro'
    ]
    dt_cadastro = datetime.strptime(data_cadastro_cliente, '%Y-%m-%d %H:%M:%S')
    data_pedido = gerar_data_aleatoria(dt_cadastro, DATA_FIM)

    pedidos.append({
        "id_pedido": idx,
        "id_cliente": id_cliente_sorteado,
        "id_cupom": random.choice([
            None,
            random.randint(1, VOLUMES["cupons"])
        ]),
        "data_pedido": data_pedido,
        "status_pedido": random.choice([
            'Entregue',
            'Entregue',
            'Entregue',
            'Cancelado',
            'Processando'
        ])
    })
df_pedidos = pd.DataFrame(pedidos)

# 8. PAGAMENTOS (15.000)
pagamentos = []
for idx in tqdm(range(1, VOLUMES["pagamentos"] + 1), desc="8/10 - Pagamentos"):
    # Cada pagamento é atrelado a um pedido existente
    # (relação 1:1 para bater os 15k)
    id_pedido = idx
    data_ped = datetime.strptime(
        df_pedidos.loc[id_pedido - 1, 'data_pedido'],
        '%Y-%m-%d %H:%M:%S'
    )
    data_pagamento = (
        data_ped + timedelta(minutes=random.randint(5, 1440))
    ).strftime('%Y-%m-%d %H:%M:%S')

    pagamentos.append({
        "id_pagamento": idx,
        "id_pedido": id_pedido,
        "metodo_pagamento": random.choice([
            'Cartão de Crédito',
            'Pix',
            'Boleto Bancário'
        ]),
        "data_pagamento": data_pagamento,
        "status_pagamento": (
            'Aprovado'
            if df_pedidos.loc[id_pedido - 1, 'status_pedido'] != 'Cancelado'
            else 'Estornado'
        )
    })
df_pagamentos = pd.DataFrame(pagamentos)

# 9. AVALIAÇÕES (15.000)
avaliacoes = []
for idx in tqdm(range(1, VOLUMES["avaliacoes"] + 1), desc="9/10 - Avaliações"):
    avaliacoes.append({
        "id_avaliacao": idx,
        "id_produto": random.randint(1, VOLUMES["produtos"]),
        "id_cliente": random.randint(1, VOLUMES["clientes"]),
        "nota": random.randint(1, 5),
        "comentario": random.choice([
            "Excelente produto!",
            "Gostei bastante.",
            "Entrega rápida.",
            "O produto quebrou rápido.",
            "Pelo preço, vale a pena."
        ])
    })
df_avaliacoes = pd.DataFrame(avaliacoes)

# 10. ITENS DO PEDIDO (25.000)
itens_pedido = []
for idx in tqdm(
    range(1, VOLUMES["itens_pedido"] + 1),
    desc="10/10 - Itens do Pedido"
):
    itens_pedido.append({
        "id_item": idx,
        # Pedidos podem ter múltiplos itens para somar 25k
        "id_pedido": random.randint(1, VOLUMES["pedidos"]),
        "id_produto": random.randint(1, VOLUMES["produtos"]),
        "quantidade": random.randint(1, 5)
    })
df_itens_pedido = pd.DataFrame(itens_pedido)

# --- CARGA NO BANCO DE ORIGEM ---
# O Faker gera a massa e popula o ambiente relacional (Postgres), que é a
# origem lida pela camada Landing.
tabelas = {
    "clientes": df_clientes,
    "enderecos": df_enderecos,
    "categorias": df_categorias,
    "fornecedores": df_fornecedores,
    "produtos": df_produtos,
    "cupons": df_cupons,
    "pedidos": df_pedidos,
    "itens_pedido": df_itens_pedido,
    "pagamentos": df_pagamentos,
    "avaliacoes": df_avaliacoes,
}

engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

for nome, df in tabelas.items():
    df.to_sql(nome, engine, if_exists="replace", index=False)
    print(f"Carregada no banco: {nome} ({len(df)} linhas)")

print(
    f"\n Sucesso! {total_geral} registros criados e carregados "
    f"nas 10 tabelas do banco de origem '{PG_DB}'."
)
