FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libcairo2-dev \
    gdal-bin \
    libgdal-dev \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_VERSION=3.4.1

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv --version

ENV PATH="/root/.local/bin:$PATH"
ENV UV_HTTP_TIMEOUT=300

COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/scripts ./scripts
COPY backend/ ./backend/

RUN uv pip install -e ./backend --system

RUN mkdir -p logs static/maps

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
