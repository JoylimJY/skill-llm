FROM python:3.11-slim

# Install minimal runtime dependencies (none required for this task)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /task

# The actual solution script and inputs will be injected at runtime by the harness.
# This Dockerfile intentionally does not COPY any files here, to respect environment isolation.

CMD ["python3", "-m", "built_in_executor"]
