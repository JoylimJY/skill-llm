FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install anthropic python-docx pypdf markdown beautifulsoup4 requests