# WorkloadMigrator

A production-quality Django (5.2+) & Celery (5.x) application to model VM workload migrations:

- **Domain models**: `Workload`, `Credentials`, `MountPoint`, `MigrationTarget`, `Migration`  
- **Business rules**: immutable IPs, required fields, allowed cloud types, prohibition of `C:\` migrations  
- **Persistence**: PostgreSQL via Django ORM  
- **Async orchestration**: Celery tasks (eager mode for tests; Redis broker in production)  
- **REST API**: CRUD + custom `POST /api/migrations/{id}/run/` via Django REST Framework  
- **OpenAPI & Swagger UI**: drf-spectacular integration  
- **Containerized**: Docker & Docker Compose  
- **End-to-end harness**: `scripts/test_api_flow.py` using `requests`  
- **Quality checks**: Black, isort, pytest  

---

## Table of Contents

1. [Prerequisites](#prerequisites)  
2. [Environment Variables](#environment-variables)  
3. [Local Setup](#local-setup)  
4. [Database Migrations](#database-migrations)  
5. [Running Locally](#running-locally)  
6. [API Documentation](#api-documentation)  
7. [Test Harness](#test-harness)  
8. [Docker & Compose](#docker--compose)  
9. [Lint & Tests](#lint--tests)  
10. [Project Structure](#project-structure)  
11. [Contributing](#contributing)  
12. [License](#license)  

---

## Prerequisites

- **Python** ≥ 3.11, < 3.14  
- **Poetry** for dependency management  
- **PostgreSQL** (locally or via Docker)  
- **Redis** (locally or via Docker)  
- **Docker & Docker Compose** (for containerized workflows)  

---

## Environment Variables

Create these at the **repo root** (next to `pyproject.toml`):

### `.env` (Local Development)

```dotenv
# .env — Local Development Configuration

# Database settings
DB_NAME=NameOfYourLocalDatabase
DB_USER=YourLocalDatabaseUser
DB_PASSWORD=YourLocalDatabasePassword
DB_HOST=localhost
DB_PORT=5432

# Celery / Redis settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### `.env.docker` (Docker Compose)

```dotenv
# .env.docker — Docker Environment Configuration

# Database settings
DB_NAME=NameOfYourDockerDatabase
DB_USER=YourDockerDatabaseUser
DB_PASSWORD=YourDockerDatabasePassword
DB_HOST=db
DB_PORT=5432

# Celery / Redis settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Local Setup

```bash
# Clone the repository and enter it:
git clone https://github.com/Mir-Yuchi/WorkloadMigrator.git
cd WorkloadMigrator

# Create & activate a virtual environment:
python -m venv venv
source venv/bin/activate

# Install dependencies:
pip install poetry
poetry config virtualenvs.create false
poetry install

# Populate your .env (copy from the template above).
```

---

## Database Migrations

Make sure your local Postgres is running and `.env` is set:

```bash
python src/workload_migrator/manage.py migrate
```

---

## Running Locally

```bash
# Start Redis:
redis-server

# Start Celery worker:
celery -A workload_migrator worker --loglevel=info

# Launch Django:
python src/workload_migrator/manage.py runserver
```

Your API is now live at http://localhost:8000/api/.

---

## API Documentation

- **OpenAPI schema**: GET `/api/schema/`  
- **Swagger UI**: GET `/api/docs/`  

Use the Swagger interface to explore all endpoints, payloads, and responses.

---

## Test Harness

A simple script to exercise the full API flow locally:

```bash
chmod +x scripts/test_api_flow.py
python scripts/test_api_flow.py
```

It will:

1. Create a Workload  
2. Create two MountPoints  
3. Create a MigrationTarget  
4. Create a Migration  
5. Trigger and report the migration result  

---

## Docker & Compose

To run everything in containers:

1. Ensure `.env.docker` is populated.  
2. Build & start all services:

   ```bash
   docker-compose up --build
   ```

   - `db` → PostgreSQL  
   - `redis` → Redis broker  
   - `web` → Django + Gunicorn  
   - `worker` → Celery  

3. Access the API at http://localhost:8000/api/.

---

## Lint & Tests

- **Black (formatting)**:

  ```bash
  poetry run black --check .
  ```

- **isort (imports)**:

  ```bash
  poetry run isort --check-only .
  ```

- **Pytest**:

  ```bash
  poetry run pytest --maxfail=1 --disable-warnings -q
  ```

---

## Project Structure

```
WorkloadMigrator/
├── .env
├── .env.docker
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── poetry.lock
├── pytest.ini
├── README.md
├── scripts/
│   └── test_api_flow.py
└── src/
    └── workload_migrator/
        ├── manage.py
        ├── core/
        │   ├── models.py
        │   ├── serializers.py
        │   ├── views.py
        │   ├── tasks.py
        │   ├── apps.py
        │   └── admin.py
        │   └── tests/
        └── workload_migrator/
            ├── __init__.py
            ├── settings.py
            ├── urls.py
            ├── wsgi.py
            └── celery.py
```

---


