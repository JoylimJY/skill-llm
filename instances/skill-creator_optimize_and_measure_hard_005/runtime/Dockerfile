FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask==2.3.3 \
    pandas==2.1.1 \
    numpy==1.24.3 \
    psutil==5.9.5 \
    requests==2.31.0 \
    gunicorn==21.2.0 \
    memory_profiler==0.61.0 \
    line_profiler==4.1.1 \
    py-spy==0.3.14 \
    matplotlib==3.7.2 \
    seaborn==0.12.2 \
    yappi==1.4.0 \
    numba==0.58.1 \
    cython==3.0.2

WORKDIR /app