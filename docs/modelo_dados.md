# Modelo de Dados

## Fonte de Dados

A fonte primária de dados simulada para este ambiente baseia-se em dados fictícios criados em nosso gerador Python para reproduzir o comportamento de um E-commerce.

Os arquivos crus (`.csv`) são ingeridos e processados pelo **Apache Airflow e PySpark**, transformados em um modelo otimizado e salvos nos formatos colunares avançados (Delta Lake) na camada *Gold* da nossa arquitetura.

## Modelo Entidade-Relacionamento (ER)

Abaixo apresentamos o modelo Entidade-Relacionamento (ER) completo das 10 tabelas geradas na origem que alimentam nosso Data Lakehouse e posteriormente o modelo dimensional.

<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>

<div class="mermaid">
erDiagram
    clientes ||--o{ enderecos : "possui"
    clientes ||--o{ pedidos : "realiza"
    clientes ||--o{ avaliacoes : "escreve"
    
    pedidos ||--|{ itens_pedido : "contém"
    pedidos ||--o| pagamentos : "gera"
    cupons |o--o{ pedidos : "aplicado em"
    
    produtos ||--o{ itens_pedido : "faz parte"
    produtos ||--o{ avaliacoes : "recebe"
    
    categorias ||--o{ produtos : "classifica"
    fornecedores ||--o{ produtos : "fornece"
    
    clientes {
        int id_cliente PK
        varchar nome
        varchar email
        varchar cpf
        datetime data_cadastro
    }
    
    enderecos {
        int id_endereco PK
        int id_cliente FK
        varchar rua
        varchar numero
        varchar cidade
        varchar estado
        varchar cep
    }
    
    categorias {
        int id_categoria PK
        varchar nome_categoria
    }
    
    cupons {
        int id_cupom PK
        varchar codigo
        int percentual_desconto
    }
    
    fornecedores {
        int id_fornecedor PK
        varchar nome_fornecedor
        varchar cnpj
        varchar contato_email
    }
    
    produtos {
        int id_produto PK
        int id_categoria FK
        int id_fornecedor FK
        varchar nome_produto
        float preco_unitario
    }
    
    pedidos {
        int id_pedido PK
        int id_cliente FK
        int id_cupom FK
        datetime data_pedido
        varchar status_pedido
    }
    
    pagamentos {
        int id_pagamento PK
        int id_pedido FK
        varchar metodo_pagamento
        datetime data_pagamento
        varchar status_pagamento
    }
    
    avaliacoes {
        int id_avaliacao PK
        int id_produto FK
        int id_cliente FK
        int nota
        varchar comentario
    }
    
    itens_pedido {
        int id_item PK
        int id_pedido FK
        int id_produto FK
        int quantidade
    }
</div>
