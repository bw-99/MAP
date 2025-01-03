FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt /workspace/

RUN pip3 install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "/bin/bash" ]
