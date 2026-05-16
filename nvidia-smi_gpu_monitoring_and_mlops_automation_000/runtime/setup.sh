#!/bin/bash
set -e

WORKSPACE="/workspace"

# Install the mock nvidia-smi as a system command
cp "$WORKSPACE/scripts/mock_nvidia_smi.py" /usr/local/bin/nvidia-smi
chmod +x /usr/local/bin/nvidia-smi

# Override the installed pynvml with our mock version
# Find the real pynvml install location and replace it
PYNVML_SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
cp "$WORKSPACE/mock_libs/pynvml.py" "$PYNVML_SITE/pynvml.py"

# Verify the mock works
echo "=== Verifying mock nvidia-smi ==="
nvidia-smi -L
echo ""
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
echo ""
echo "=== Verifying mock pynvml ==="
python3 -c "
import pynvml
pynvml.nvmlInit()
count = pynvml.nvmlDeviceGetCount()
print(f'GPU count: {count}')
h = pynvml.nvmlDeviceGetHandleByIndex(0)
print(f'GPU 0 name: {pynvml.nvmlDeviceGetName(h).decode(\"utf-8\")}')
print(f'GPU 0 power (mW): {pynvml.nvmlDeviceGetPowerUsage(h)}')
pynvml.nvmlShutdown()
print('pynvml mock OK')
"
echo "=== Setup complete ==="