FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pandas matplotlib seaborn numpy scipy scikit-learn plotly

WORKDIR /workspace
COPY . .

RUN chmod +x *.py *.sh