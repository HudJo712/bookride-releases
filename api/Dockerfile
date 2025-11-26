FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml RELEASE_NOTES.md ./
COPY api ./api

ENV PYTHONPATH="/app/api/src:${PYTHONPATH}"

RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "bookandride_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
