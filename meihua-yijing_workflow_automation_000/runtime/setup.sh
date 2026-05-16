#!/bin/bash
set -e

# Make meihua.py executable
chmod +x /workspace/meihua.py

# Verify the script is functional
echo "Verifying meihua.py..."
python3 /workspace/meihua.py numbers 6 7 3 > /tmp/meihua_test.txt 2>&1
if [ $? -eq 0 ]; then
    echo "meihua.py verification OK"
    cat /tmp/meihua_test.txt
else
    echo "meihua.py verification FAILED"
    cat /tmp/meihua_test.txt
    exit 1
fi

echo "Setup complete."