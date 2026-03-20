# Install required Python packages
pip install lxml python-docx

# Make scripts executable if needed (placeholders if scripts exist)
chmod +x scripts/office/soffice.py
chmod +x scripts/office/unpack.py
chmod +x scripts/office/pack.py
chmod +x scripts/comment.py

# Note: The scripts directory is copied into /app in Dockerfile
