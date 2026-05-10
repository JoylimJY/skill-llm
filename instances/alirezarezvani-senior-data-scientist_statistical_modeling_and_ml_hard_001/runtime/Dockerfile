FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2 \
    scipy==1.13.1 \
    scikit-learn==1.5.1 \
    xgboost==2.1.1 \
    statsmodels==0.14.2 \
    mlflow==2.14.3 \
    shap==0.45.1 \
    pyarrow==15.0.2 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN mkdir -p /workspace/skill_context