FROM python:3.11-slim

RUN pip install requests beautifulsoup4 flask

RUN useradd -m -s /bin/bash agent
WORKDIR /home/agent