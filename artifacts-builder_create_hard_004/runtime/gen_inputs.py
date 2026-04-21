import os
import json

# Create minimal input files expected for initialization and build
# This task relies on invoking the scripts/init-artifact.sh and bundle script
# Provide a dummy 'shadcn-components.tar.gz' with minimal contents to allow extraction

# Create dummy minimal tarball of shadcn/ui components folder
import tarfile

COMPONENTS_DIR = 'shadcn_components_dummy'

if not os.path.exists(COMPONENTS_DIR):
    os.makedirs(os.path.join(COMPONENTS_DIR, 'ui'), exist_ok=True)
    # Create a minimal component file
    with open(os.path.join(COMPONENTS_DIR, 'ui', 'button.tsx'), 'w') as f:
        f.write('// Dummy shadcn/ui Button component placeholder\n')


# Create tar.gz
with tarfile.open('scripts/shadcn-components.tar.gz', 'w:gz') as tar:
    tar.add(COMPONENTS_DIR, arcname='')

# Create scripts directory if missing
os.makedirs('scripts', exist_ok=True)

# Write dummy init-artifact.sh and bundle-artifact.sh that will be replaced by mounted scripts at runtime
# Provide minimal index.html file post-init (the actual init script creates it)

with open('index.html', 'w') as f:
    f.write('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Test Artifact</title></head><body><div id="root"></div></body></html>')

# Known marker content: Dummy component tarball with // Dummy shadcn/ui Button component placeholder comment
