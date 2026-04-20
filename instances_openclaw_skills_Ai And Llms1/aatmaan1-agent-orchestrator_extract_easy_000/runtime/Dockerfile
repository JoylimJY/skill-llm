FROM python:3.11-slim

# Basic setup
ENV PYTHONUNBUFFERED=1
WORKDIR /workspace

# Install any runtime dependencies (none required for this task)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

# Ensure python is available
RUN python -V

# Expose a default command (the grader will override as needed). Do not run any scripts here.
CMD ["bash"]
