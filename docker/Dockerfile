FROM apache/airflow:2.9.1-python3.11

# Muda temporariamente para o usuário administrador (root) para instalar programas
USER root

# Atualiza os pacotes e instala o Java
RUN apt-get update && \
    apt-get install -y default-jre-headless && \
    apt-get clean

# Volta para o usuário padrão do Airflow por segurança
USER airflow