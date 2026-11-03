FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SNAPSHOT_DIR=/app/data/snapshots \
    SNAPSHOT_SEED_DIR=/app/seed-snapshots

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY data/seed-snapshots ./seed-snapshots
RUN python -m pip install --no-cache-dir ".[server]"

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/snapshots \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8001
CMD ["uvicorn", "argentina_open_data.api:app", "--host", "0.0.0.0", "--port", "8000"]
