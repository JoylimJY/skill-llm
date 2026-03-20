FROM python:3.11-slim
RUN pip install anthropic python-dotenv
WORKDIR /workspace
COPY . .
RUN echo 'ANTHROPIC_API_KEY=test-key-12345' > .env