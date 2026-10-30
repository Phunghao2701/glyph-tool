# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend-build
WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ARG VITE_GOOGLE_CLIENT_ID=
ARG VITE_GOOGLE_API_KEY=
ARG VITE_GOOGLE_APP_ID=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_GOOGLE_CLIENT_ID=${VITE_GOOGLE_CLIENT_ID} \
    VITE_GOOGLE_API_KEY=${VITE_GOOGLE_API_KEY} \
    VITE_GOOGLE_APP_ID=${VITE_GOOGLE_APP_ID}
RUN npm run build

FROM python:3.12-slim-trixie AS backend-build
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /workspace/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
COPY backend/app ./app
COPY backend/vendor ./vendor

FROM python:3.12-slim-trixie AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/home/vietfont \
    XDG_DATA_HOME=/home/vietfont/.local/share \
    VFK_DATA_DIR=/data \
    MPLCONFIGDIR=/tmp/matplotlib

RUN apt-get update \
    && apt-get install --no-install-recommends -y dbus-daemon gnome-keyring \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system vietfont \
    && useradd --system --gid vietfont --home-dir /home/vietfont --create-home --shell /usr/sbin/nologin vietfont \
    && mkdir -p /data /home/vietfont/.local/share/keyrings /tmp/matplotlib \
    && chown -R vietfont:vietfont /data /home/vietfont /tmp/matplotlib

WORKDIR /workspace
COPY --from=backend-build /opt/venv /opt/venv
COPY --from=backend-build --chown=vietfont:vietfont /workspace/backend /workspace/backend
COPY --from=frontend-build --chown=vietfont:vietfont /workspace/frontend/dist /workspace/frontend/dist
COPY --chown=vietfont:vietfont docker-entrypoint.sh /usr/local/bin/docker-entrypoint
RUN chmod 755 /usr/local/bin/docker-entrypoint

WORKDIR /workspace/backend
USER vietfont
EXPOSE 8000 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).read()"]
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
