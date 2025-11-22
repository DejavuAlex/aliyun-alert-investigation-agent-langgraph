FROM python:3.11-slim

ARG PIP_INDEX_URL
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOME=/app \
    LOG_LEVEL=INFO

WORKDIR $APP_HOME

# System deps (if needed for wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for cache
COPY pyproject.toml ./
COPY src ./src

# Install runtime deps
RUN pip install --upgrade pip \
    && if [ -n "$PIP_INDEX_URL" ]; then pip config set global.index-url "$PIP_INDEX_URL"; fi \
    && pip install ".[default]" || true \
    && pip install langgraph langserve fastapi uvicorn

# Optional: copy env/example files
COPY .env* ./

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD curl -sf http://127.0.0.1:8000/ || exit 1

CMD ["uvicorn", "src.langserve_app:app", "--host", "0.0.0.0", "--port", "8000"]

