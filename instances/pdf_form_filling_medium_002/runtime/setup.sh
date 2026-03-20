#!/bin/bash
set -e

# Make sure poppler tools are available
which pdftotext || (echo "pdftotext not found" && exit 1)
which pdfimages || (echo "pdfimages not found" && exit 1)

# Verify Python packages
python3 -c "import pypdf, pdfplumber, reportlab, PIL, pdf2image, pytesseract, pypdfium2" || (echo "Required Python packages not installed" && exit 1)

echo "Setup complete - all dependencies verified"