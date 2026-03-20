FROM python:3.11-slim
RUN pip install anthropic python-dotenv
WORKDIR /app
COPY . .
ENV ANTHROPIC_API_KEY=test-key-123