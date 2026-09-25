# syntax=docker/dockerfile:1.7
# Networks with TLS inspection can pass their CA bundle for the download steps only (it is
# never copied into the image):  docker build --secret id=ca,src="$SSL_CERT_FILE" .
# ---- 1. build the crash-cart UI -------------------------------------------------------
FROM node:22-slim AS ui
WORKDIR /ui
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; \
    npm install -g pnpm@11
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; \
    pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ---- 2. the server ----------------------------------------------------------------------
FROM python:3.13-slim AS app
ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    DATABASE_PATH=/data/codeloop.db \
    REPLAY_DIR=/app/demo/scenarios \
    FRONTEND_DIST=/app/frontend/dist \
    HOST=0.0.0.0 \
    PORT=8000
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version backend/
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi; \
    cd backend && uv sync --frozen --no-dev --no-install-project
COPY backend/ backend/
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca; fi; \
    cd backend && uv sync --frozen --no-dev
COPY demo/ demo/
COPY --from=ui /ui/dist frontend/dist
RUN useradd --create-home --uid 10001 codeloop && mkdir -p /data && chown codeloop /data
USER codeloop
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health', timeout=4)"
CMD ["/app/backend/.venv/bin/python", "-m", "codeloop"]
