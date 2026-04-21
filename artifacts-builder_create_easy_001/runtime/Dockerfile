FROM node:20-slim

WORKDIR /workspace

# Install bash, python3, git, tar
RUN apt-get update && apt-get install -y bash python3 git tar && rm -rf /var/lib/apt/lists/*

# Create required scripts and artifact tarball structure if they are not provided by the build context
RUN mkdir -p scripts && \
    cat > scripts/init-artifact.sh <<'EOF'
#!/usr/bin/env bash
set -e

project="$1"

if [ -z "$project" ]; then
  echo "Usage: $0 <project-name>"
  exit 1
fi

mkdir -p "$project"
if [ ! -f "$project/index.html" ]; then
  cat > "$project/index.html" <<'HTML'
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Artifact</title></head>
  <body><h1>Artifact</h1></body>
</html>
HTML
fi
EOF
RUN chmod +x scripts/init-artifact.sh && \
    cat > scripts/bundle-artifact.sh <<'EOF'
#!/usr/bin/env bash
set -e

cat > bundle.html <<'HTML'
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Bundle</title></head>
  <body><h1>Bundle</h1></body>
</html>
HTML
EOF
RUN chmod +x scripts/bundle-artifact.sh

# Install pnpm
RUN npm install -g pnpm

# Set environment variable to silence pnpm prompts
ENV PNPM_HOME=/workspace/.pnpm
ENV PATH="$PNPM_HOME:$PATH"

# Create a placeholder tarball at build time so initialization can succeed
RUN python3 - <<'PY'
import tarfile, os
with tarfile.open("shadcn-components.tar.gz", "w:gz") as tar:
    data = b"# SHADCN COMPONENTS DUMMY FILE - marker for test\n"
    info = tarfile.TarInfo("dummy_component.txt")
    info.size = len(data)
    tar.addfile(info, fileobj=__import__("io").BytesIO(data))
PY

# Default command: open a shell
CMD ["/bin/bash"]