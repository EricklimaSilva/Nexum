# Nexum

Aplicação pessoal gamificada para acompanhamento de vida financeira, evolução física, treinos de calistenia e metas pessoais.

## Stack

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Flask-Migrate
- Flask-Login

## Estrutura inicial

- app/
  - auth/
  - dashboard/
  - common/
  - templates/
  - static/
- migrations/
- requirements.txt
- run.py
- .env.example

## Requisitos locais

- Python 3.11+
- PostgreSQL em execução
- virtualenv ou venv

## Configuração

1. Crie um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie um banco PostgreSQL local:

```sql
CREATE DATABASE nexum;
```

4. Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

5. Ajuste os valores no `.env` com suas credenciais locais.

## Variáveis de ambiente

```env
SECRET_KEY=change-this-secret-key
DATABASE_URL=postgresql+psycopg://localhost:5433/nexum
FLASK_ENV=development
FLASK_APP=run.py
```

## Inicialização do projeto

```bash
source .venv/bin/activate
flask db init
flask db migrate -m "initial migration"
flask db upgrade
python run.py
```

A aplicação ficará disponível em:

```text
http://localhost:5000
```

## Primeira fase implementada

- estrutura modular por domínio
- Application Factory
- configuração por ambiente
- autenticação com Flask-Login
- cadastro e login
- logout
- sessão protegida
- modelo User e UserProfile
- pagina inicial protegida como validação do fluxo

## Próximos passos

- dashboard completo
- finanças
- Safe Spend
- peso e IMC
- treinos
- goals e quests
- achievements
