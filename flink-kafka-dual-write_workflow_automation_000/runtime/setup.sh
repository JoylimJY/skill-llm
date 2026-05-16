#!/bin/bash
set -e

echo "=== Setting up bethune workspace ==="

# Make scripts executable
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

# Pre-download Maven dependencies to speed up any compile attempts
cd /workspace
# Set Maven to use Aliyun mirror for faster dependency resolution in China
mkdir -p ~/.m2
cat > ~/.m2/settings.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<settings>
  <mirrors>
    <mirror>
      <id>aliyun</id>
      <mirrorOf>central</mirrorOf>
      <name>Aliyun Maven Mirror</name>
      <url>https://maven.aliyun.com/repository/central</url>
    </mirror>
  </mirrors>
</settings>
EOF

echo "=== Workspace setup complete ==="
echo "Directory structure:"
find /workspace/src -name "*.java" | head -30
echo "Config files:"
ls /workspace/src/main/resources/