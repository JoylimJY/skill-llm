FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    mlflow==2.13.0 \
    scikit-learn==1.4.2 \
    pandas==2.2.2 \
    numpy==1.26.4 \
    torch==2.2.2 \
    gitpython==3.1.43 \
    evidently==0.4.30 \
    shap==0.45.1 \
    plyer==2.1.0 \
    scipy==1.13.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace