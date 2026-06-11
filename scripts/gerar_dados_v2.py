import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import os

# Inicializa o Faker configurado para o Brasil
fake = Faker(['pt_BR'])

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
print(f"📊 Configurado para gerar {total_geral} registros no total das 10 tabelas.")

DATA_INICIO = datetime(2023, 6, 1)
DATA_FIM = datetime(2026, 6, 1)

def gerar_data_aleatoria(inicio, fim):
    delta = fim - inicio
    dias_aleatorios = random.randint(0, delta.days)
    return (inicio + timedelta(days=dias_aleatorios)).strftime('%Y-%m-%d %H:%M:%S')

print("⏳ Iniciando a geração da massa de dados...")

# 1. CATEGORIAS (50)
categorias = []
for idx in range(1, VOLUMES["categorias"] + 1):
    categorias.append({"id_categoria": idx, "nome_categoria": f"Subcategoria {fake.word().capitalize()}-{idx}"})
df_categorias = pd.DataFrame(categorias)
print(f"✅ 1/10 - Categorias: {len(df_categorias)} linhas")

# 2. CUPONS (150)
cupons = []
for idx in range(1, VOLUMES["cupons"] + 1):
    cupons.append({"id_cupom": idx, "codigo": f"PROMO{idx:03d}", "percentual_desconto": random.choice([5, 10, 15, 20])})
df_cupons = pd.DataFrame(cupons)
print(f"✅ 2/10 - Cupons: {len(df_cupons)} lines")

# 3. FORNECEDORES (800)
fornecedores = []
for idx in tqdm(range(1, VOLUMES["fornecedores"] + 1), desc="3/10 - Fornecedores"):
    fornecedores.append({"id_fornecedor": idx, "nome_fornecedor": fake.company(), "cnpj": fake.cnpj(), "contato_email": fake.company_email()})
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
    data_cadastro_cliente = df_clientes.loc[id_cliente_sorteado - 1, 'data_cadastro']
    dt_cadastro = datetime.strptime(data_cadastro_cliente, '%Y-%m-%d %H:%M:%S')
    data_pedido = gerar_data_aleatoria(dt_cadastro, DATA_FIM)
    
    pedidos.append({
        "id_pedido": idx,
        "id_cliente": id_cliente_sorteado,
        "id_cupom": random.choice([None, random.randint(1, VOLUMES["cupons"])]),
        "data_pedido": data_pedido,
        "status_pedido": random.choice(['Entregue', 'Entregue', 'Entregue', 'Cancelado', 'Processando'])
    })
df_pedidos = pd.DataFrame(pedidos)

# 8. PAGAMENTOS (15.000)
pagamentos = []
for idx in tqdm(range(1, VOLUMES["pagamentos"] + 1), desc="8/10 - Pagamentos"):
    # Cada pagamento é atrelado a um pedido existente (relação 1:1 para bater os 15k)
    id_pedido = idx
    data_ped = datetime.strptime(df_pedidos.loc[id_pedido - 1, 'data_pedido'], '%Y-%m-%d %H:%M:%S')
    data_pagamento = (data_ped + timedelta(minutes=random.randint(5, 1440))).strftime('%Y-%m-%d %H:%M:%S')
    
    pagamentos.append({
        "id_pagamento": idx,
        "id_pedido": id_pedido,
        "metodo_pagamento": random.choice(['Cartão de Crédito', 'Pix', 'Boleto Bancário']),
        "data_pagamento": data_pagamento,
        "status_pagamento": 'Aprovado' if df_pedidos.loc[id_pedido - 1, 'status_pedido'] != 'Cancelado' else 'Estornado'
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
        "comentario": random.choice(["Excelente produto!", "Gostei bastante.", "Entrega rápida.", "O produto quebrou rápido.", "Pelo preço, vale a pena."])
    })
df_avaliacoes = pd.DataFrame(avaliacoes)

# 10. ITENS DO PEDIDO (25.000)
itens_pedido = []
for idx in tqdm(range(1, VOLUMES["itens_pedido"] + 1), desc="10/10 - Itens do Pedido"):
    itens_pedido.append({
        "id_item": idx,
        "id_pedido": random.randint(1, VOLUMES["pedidos"]), # Pedidos podem ter múltiplos itens para somar 25k
        "id_produto": random.randint(1, VOLUMES["produtos"]),
        "quantidade": random.randint(1, 5)
    })
df_itens_pedido = pd.DataFrame(itens_pedido)

# --- SALVANDO NA PASTA DE ORIGEM ---
os.makedirs("dados_origem", exist_ok=True)
df_clientes.to_csv("dados_origem/clientes.csv", index=False)
df_enderecos.to_csv("dados_origem/enderecos.csv", index=False)
df_categorias.to_csv("dados_origem/categorias.csv", index=False)
df_fornecedores.to_csv("dados_origem/fornecedores.csv", index=False)
df_produtos.to_csv("dados_origem/produtos.csv", index=False)
df_cupons.to_csv("dados_origem/cupons.csv", index=False)
df_pedidos.to_csv("dados_origem/pedidos.csv", index=False)
df_itens_pedido.to_csv("dados_origem/itens_pedido.csv", index=False)
df_pagamentos.to_csv("dados_origem/pagamentos.csv", index=False)
df_avaliacoes.to_csv("dados_origem/avaliacoes.csv", index=False)

print(f"\n🚀 Sucesso! {total_geral} registros criados e distribuídos nas 10 tabelas em '/dados_origem'.")