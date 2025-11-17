# === Stage 0: base ===
FROM python:3.12-slim-bookworm AS base

ENV POETRY_VERSION=2.1.3
RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION" && poetry self add "poetry-plugin-export==1.9.0"

# === Stage 1: Generate lock file ===
FROM base as locker

WORKDIR /lock
COPY pyproject.toml ./
RUN poetry config virtualenvs.create false \
 && poetry lock

# === Stage 2: Build actual application ===
FROM base as builder
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libpq-dev gcc g++ python3-dev make \
    git curl libpq-dev gcc g++ python3-dev make \
 && rm -rf /var/lib/apt/lists/* && apt-get clean

ENV POETRY_VERSION=2.1.3
RUN pip install --upgrade pip
RUN pip install "poetry==$POETRY_VERSION" && poetry self add "poetry-plugin-export==1.9.0"

WORKDIR /app
COPY pyproject.toml ./
COPY --from=locker /lock/poetry.lock ./

# Export requirements from the lock and install with pip (avoids Poetry install bug)
RUN poetry export --without dev -f requirements.txt -o requirements.txt \
 && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app

EXPOSE 8000
RUN chmod +x /app/scripts/init_server.sh
ENTRYPOINT ["/app/scripts/init_server.sh"]