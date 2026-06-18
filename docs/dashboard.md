# Dashboard Analítico

O projeto conta com um dashboard interativo construído com **Streamlit**, seguindo o conceito de *One Page View*.

## Acesso
Para acessar o painel, certifique-se de ter executado todas as DAGs (conforme instruído na aba [Como Executar](execucao.md)) e acesse:

[http://localhost:8501](http://localhost:8501)

> **Aviso:** Se os dados ainda não tiverem sido processados até a camada Gold, o dashboard exibirá uma mensagem orientando a execução das DAGs.

## KPIs Principais

O painel apresenta 4 KPIs fundamentais do negócio de e-commerce logo na visão inicial:

1. **Receita total**
2. **Quantidade de pedidos**
3. **Ticket médio**
4. **Quantidade de itens vendidos**

**Origem dos dados (KPIs):**
- Arquivo consumido: `published/dashboard/fato_vendas`
- Derivado da tabela Delta: `gold/ecommerce/fato_vendas`

## Métricas e Gráficos

### Gráficos Obrigatórios
- **Evolução do faturamento mensal**
  - Consome: `published/dashboard/faturamento_mensal`
  - Derivado de: `gold/ecommerce/faturamento_mensal`
- **Faturamento por categoria**
  - Consome: `published/dashboard/faturamento_por_categoria`
  - Derivado de: `gold/ecommerce/faturamento_por_categoria`

### Extras Incluídos
- **Ranking de Top Produtos (por receita)**
  - Consome: `published/dashboard/top_produtos`
- **Tabela Resumida de Vendas (por mês e categoria)**
  - Consome: `published/dashboard/fato_vendas`

## Resumo dos Marts Gold Utilizados
A camada analítica Gold gerou os seguintes modelos que alimentam o visual do dashboard:
- `fato_vendas`
- `faturamento_mensal`
- `faturamento_por_categoria`
- `top_produtos`
