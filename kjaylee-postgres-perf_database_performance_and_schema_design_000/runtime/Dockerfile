FROM postgres:15-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-psycopg2 \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install psycopg2-binary sqlparse -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV POSTGRES_PASSWORD=testpass
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=ecommerce

RUN mkdir -p /workspace
WORKDIR /workspace