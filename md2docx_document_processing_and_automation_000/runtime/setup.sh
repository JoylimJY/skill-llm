#!/bin/bash
set -e

# Ensure deploy.sh exists before making it executable
if [ ! -f /workspace/scripts/deploy.sh ]; then
    mkdir -p /workspace/scripts
    echo '#!/bin/bash' > /workspace/scripts/deploy.sh
    echo "echo 'Deploying application...'" >> /workspace/scripts/deploy.sh
fi

# Make scripts executable
chmod +x /workspace/scripts/deploy.sh

# Verify pandoc is available
pandoc --version | head -1

# Verify python-docx is available
python3 -c "import docx; print('python-docx OK:', docx.__version__)"

echo "Setup complete."