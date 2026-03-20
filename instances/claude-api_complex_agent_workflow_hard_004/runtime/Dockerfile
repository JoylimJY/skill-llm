FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN pip install --no-cache-dir \
    anthropic==0.40.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    pandas==2.1.4 \
    numpy==1.24.3 \
    matplotlib==3.7.2 \
    seaborn==0.12.2 \
    reportlab==4.0.7 \
    python-dateutil==2.8.2 \
    textblob==0.17.1 \
    yfinance==0.2.28 \
    scikit-learn==1.3.2 \
    nltk==3.8.1

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon'); nltk.download('stopwords')"

COPY . /workspace/
RUN chmod +x /workspace/*.py /workspace/*.sh