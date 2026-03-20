#!/bin/bash
# Configure ImageMagick security policy to allow PDF processing
sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' /etc/ImageMagick-6/policy.xml 2>/dev/null || true
sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' /etc/ImageMagick-7/policy.xml 2>/dev/null || true

# Set proper permissions
chmod 644 /workspace/*.pdf /workspace/*.png /workspace/*.json 2>/dev/null || true