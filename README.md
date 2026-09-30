# Nexum

Nexum é uma aplicação de acompanhamento pessoal e produtividade, organizada em módulos de finanças, saúde, objetivo, treino e progressão. O projeto combina Flask, SQLAlchemy, Flask-Login, Flask-WTF e PostgreSQL para manter um fluxo de uso pessoal com segurança e rastreabilidade.

## Tecnologias

- Python 3.12+
- Flask 3.x
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Flask-Limiter
- PostgreSQL
- pytest + pytest-cov
- Alembic

## Módulos principais

- auth: autenticação, cadastro e sessão
- dashboard: resumo geral e indicadores
- finance: saldo, safe spend e compromissos
- body: altura, peso e histórico corporal
- workouts: treinos, exercícios e séries
- goals: metas e status de progresso
- quick_log: registro rápido de ações com XP
- progression: cálculo de nível, rank e ledger de XP
- common: utilitários e validadores

## Requisitos

- Python 3.12+
- PostgreSQL 15+ para desenvolvimento e integração
- macOS/Linux
- `venv` ou `virtualenv`
- `git`

## Setup no macOS/Linux

1. Clone o repositório e entre na pasta:

```bash
cd nexum
```

2. Crie o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Atualize o pip e instale dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

4. Copie o arquivo de ambiente:

```bash
cp .env.example .env
```

5. Ajuste as variáveis locais no `.env`.

## Configuração de ambiente

Arquivo de exemplo:

```env
SECRET_KEY=change-me-in-local-env
DATABASE_URL=postgresql+psycopg://erick@localhost:5433/nexum_recovered
FLASK_ENV=development
```

Observações:
- `SECRET_KEY` deve ser único e não trivial em produção
- `DATABASE_URL` precisa apontar para o banco local de desenvolvimento
- para testes normais, o app usa SQLite isolado
- para integração PostgreSQL, o banco alvo deve ser `nexum_test`

## PostgreSQL local

Crie e configure os bancos necessários:

```sql
CREATE DATABASE nexum_recovered;
CREATE DATABASE nexum_test;
```

Banco legado:
- `nexum`: banco legado não deve ser usado para desenvolvimento nem testes
- `nexum_recovered`: usado para desenvolvimento local
- `nexum_test`: usado para integração PostgreSQL em testes

## Migrations

A migração ativa atual é:

```text
f84b9a4d1e2a
```

Comandos básicos:

```bash
export DATABASE_URL="postgresql+psycopg://erick@localhost:5433/nexum_recovered"
flask db current
flask db heads
flask db upgrade
```

Para um cenário de teste PostgreSQL:

```bash
export DATABASE_URL="postgresql+psycopg://erick@localhost:5433/nexum_test"
flask db upgrade
```

## Execução local

```bash
source .venv/bin/activate
python run.py
```

A aplicação fica em:

```text
http://localhost:5000
```

## Testes

Teste principal:

```bash
pytest -v
```

Cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

Testes PostgreSQL:

```bash
pytest -m postgres -v
```

Compile check:

```bash
python3 -m compileall app tests
```

## Segurança implementada

- CSRF habilitado em ambiente normal
- `TestingConfig` usa SQLite isolado e desativa CSRF apenas em testes
- `ProductionConfig` exige `SECRET_KEY` não padrão e `DATABASE_URL`
- `login_required` em rotas protegidas
- isolamento por `user_id` em módulos críticos
- rate limiting em rotas sensíveis
- headers básicos aplicados em respostas: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- páginas de erro amigáveis: 403, 404, 429, 500

## XP Ledger

O sistema mantém um ledger de experiência com `XPEvent` e `UserProgress` para registrar eventos de progressão de forma auditável. Isso evita que XP seja creditado sem rastreio consistente.

## Quick Log

O módulo Quick Log permite registrar ações rápidas do dia com categoria e XP. Ele inclui:
- normalização do texto
- filtros por categoria
- deduplicação imediata
- controle de abuso por rate limit
- registro de progresso em `UserProgress`

## Estrutura de pastas

```text
nexum/
├── app/
│   ├── auth/
│   ├── body/
│   ├── common/
│   ├── dashboard/
│   ├── finance/
│   ├── goals/
│   ├── progression/
│   ├── quick_log/
│   ├── static/
│   ├── templates/
│   ├── workouts/
│   ├── __init__.py
│   ├── config.py
│   └── extensions.py
├── migrations/
├── tests/
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── run.py
├── pytest.ini
└── .github/
```

## Troubleshooting básico

### Erro de autenticação ou CSRF
- confirme que o `.env` está correto
- confirme que o formulário inclui `{{ csrf_token() }}`
- use o ambiente de teste isolado para validar fluxos sem risco

### PostgreSQL não conecta
- confirme se o serviço do PostgreSQL está ativo
- confirme o host, porta e banco
- use `nexum_test` para integração e `nexum_recovered` para desenvolvimento local

### Migrações fora do estado esperado
```bash
export DATABASE_URL="postgresql+psycopg://erick@localhost:5433/nexum_recovered"
flask db current
flask db heads
```

### Erro de secret key em produção
- configure `SECRET_KEY` com valor forte e não padrão
- nunca use `dev-secret-key-change-me` ou `test-secret-key-unsafe-only-for-tests` em produção

## Backup e restore PostgreSQL

Backup seguro:

```bash
pg_dump -d nexum_recovered -h localhost -p 5433 -U erick -f backup_nexum_recovered.sql
```

Restore:

```bash
createdb -h localhost -p 5433 -U erick nexum_recovered
psql -h localhost -p 5433 -U erick -d nexum_recovered -f backup_nexum_recovered.sql
```

Ou em dump em formato custom:

```bash
pg_dump -Fc -d nexum_recovered -h localhost -p 5433 -U erick -f backup_nexum_recovered.dump
pg_restore -h localhost -p 5433 -U erick -d nexum_recovered backup_nexum_recovered.dump
```

Aviso:
- nunca use `nexum` em desenvolvimento ou testes
- não rode restore automático em produção sem revisão do ambiente
- não inclua senha no comando; configure a autenticação local do cliente conforme seu ambiente

## CI / GitHub Actions

O workflow em [.github/workflows/tests.yml](.github/workflows/tests.yml) executa:
- pytest normal em SQLite
- cobertura
- compileall
- migrations PostgreSQL em `nexum_test`
- pytest de integração em PostgreSQL

## Comandos de desenvolvimento

O projeto inclui um [Makefile](Makefile) com comandos úteis:

```bash
make test
make coverage
make postgres-test
make run
make check
```

Esses comandos apenas agrupam passos já existentes do projeto.

## Banco de dados de desenvolvimento

- `nexum`: legado; não usar
- `nexum_recovered`: desenvolvimento local
- `nexum_test`: integração e testes PostgreSQL

## Sumário operacional

O projeto está pronto para:
- desenvolvimento local
- testes automatizados
- integração PostgreSQL em banco test-only
- preparação para CI e publicação futura
