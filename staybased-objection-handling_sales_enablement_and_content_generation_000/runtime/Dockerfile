FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    pytest \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN mkdir -p /workspace/artifacts \
    /workspace/sales_team/call_notes \
    /workspace/sales_team/lost_deals \
    /workspace/sales_team/templates \
    /workspace/marketing/landing_pages \
    /workspace/marketing/email_sequences \
    /workspace/product/feature_requests \
    /workspace/ops/onboarding \
    /workspace/ops/contracts \
    /workspace/finance/pricing_history

WORKDIR /workspace