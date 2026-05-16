FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-index jsonschema python-dateutil 2>/dev/null || \
    pip install \
        --retries 3 \
        --timeout 60 \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        jsonschema python-dateutil || \
    pip install \
        --retries 3 \
        --timeout 60 \
        --trusted-host pypi.org \
        --trusted-host files.pythonhosted.org \
        jsonschema python-dateutil || \
    (pip download \
        --no-deps \
        --dest /tmp/pkgs \
        --trusted-host pypi.org \
        jsonschema python-dateutil && \
     pip install --no-index --find-links /tmp/pkgs jsonschema python-dateutil)

WORKDIR /workspace