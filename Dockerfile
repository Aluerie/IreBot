ARG PYTHON_BASE=3.14-slim-bookworm
ARG UV_BASE=python3.14-bookworm-slim

FROM ghcr.io/astral-sh/uv:${UV_BASE} AS builder

ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /irebot

RUN apt-get update -y \
    && apt-get install --no-install-recommends --no-install-suggests -y git \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=/irebot/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/irebot/uv.lock \
    uv sync --no-dev

COPY . .

CMD [ "uv", "run", "src/main.py"]