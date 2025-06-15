FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# System deps
RUN apt-get update \
 && apt-get install -y build-essential libpq-dev netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

# Project metadata & dependencies
COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
 && poetry install --without dev --no-interaction --no-ansi

# Application code
COPY . /app

EXPOSE 8000

# At container start, collectstatic then run Gunicorn
CMD ["sh", "-c", "python src/workload_migrator/manage.py collectstatic --no-input && gunicorn --chdir src/workload_migrator workload_migrator.wsgi:application --bind 0.0.0.0:8000"]