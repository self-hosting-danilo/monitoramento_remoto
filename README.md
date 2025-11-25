# Projeto Monitoramento Remoto

Este projeto utiliza **Django**, **Redis**, **PostgresSQL** e um **client MQTT**.  
Abaixo estão as instruções para configurar e rodar o sistema localmente.

---

## Pré-requisitos

- Python 3.11+  
- Redis (rodando em container local)  
- Postgres (rodando em um container local)
- Pip  

---

## 1. Preparar o ambiente

1. Criar e Ativar o ambiente virtual:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

Instalar as dependências do projeto:

```bash
pip install -r requirements.txt
```

2. Rodar o Redis

Certifique-se de que o Redis e o Postgres estão rodando em um container local.
Exemplo usando Docker:

```bash
docker run -d \
  --name meu_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=123456 \
  -e POSTGRES_DB=meubanco \
  -p 5432:5432 \
  postgres

docker run -d -p 6379:6379 --name redis redis
```

3. Rodar o client MQTT

O client MQTT precisa estar rodando para enviar/receber dados:

```bash
python backend/client/run_client.py
```

4. Inicializar o Django

Criar as migrações:

```bash
python backend/manage.py makemigrations
python backend/manage.py migrate
```
Criar um superusuário para acessar o admin:

```bash
python backend/manage.py createsuperuser
```

Rodar o servidor de desenvolvimento:

```bash
python backend/manage.py runserver
```
O Django estará disponível em: http://127.0.0.1:8000
