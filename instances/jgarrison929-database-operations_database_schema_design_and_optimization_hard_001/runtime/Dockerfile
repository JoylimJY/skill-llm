FROM postgres:15-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-psycopg2 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install psycopg2-binary -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV POSTGRES_DB=healthdb
ENV POSTGRES_USER=healthadmin
ENV POSTGRES_PASSWORD=health_secret_2024
ENV PGPASSWORD=health_secret_2024

RUN mkdir -p /workspace/skill_context /workspace/schema /workspace/reports /workspace/archive /workspace/legacy /workspace/docs /workspace/migrations /workspace/monitoring /workspace/config /workspace/tests

RUN touch /workspace/.keep && chown postgres:postgres /workspace/.keep