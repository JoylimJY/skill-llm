#!/bin/bash
# Configure ImageMagick to allow PDF operations
if [ -f /etc/ImageMagick-6/policy.xml ]; then
    sed -i 's/policy domain="coder" rights="none" pattern="PDF"/policy domain="coder" rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml
fi