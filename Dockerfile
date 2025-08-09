FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:/root/.local/bin:/root/.cargo/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl git build-essential ca-certificates \
    && update-ca-certificates \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash","-lc"]
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && (command -v uv && uv --version)

WORKDIR /workspace

COPY pyproject.toml uv.lock* README.md /workspace/

RUN uv pip install --system -e "/workspace[dev,preprocess,server]"

COPY . /workspace

RUN uv pip install --system pytest pytest-cov

CMD ["bash"]