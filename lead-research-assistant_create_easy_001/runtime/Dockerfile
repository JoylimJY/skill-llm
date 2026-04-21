FROM python:3.11-slim

RUN pip install --no-cache-dir requests beautifulsoup4
# The evaluation does not require additional tools but includes common scraping libs for demo

WORKDIR /app

# No scripts copied in the image since mounted dynamically