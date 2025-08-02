FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /workspace
COPY . /workspace

RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e ".[dev, preprocess, server]" && \
    .venv/bin/pre-commit install

ENTRYPOINT [ "/bin/bash" ]
