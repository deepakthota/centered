FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim
RUN useradd --create-home centered
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=centered:centered centered ./centered
COPY --chown=centered:centered migrations ./migrations
COPY --chown=centered:centered alembic.ini ./
USER centered
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "centered.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
