#!/bin/bash
set -e

echo "[setup] Verifying workspace structure..."
ls /workspace/
echo "[setup] Main report present:"
ls /workspace/Q1_Q2_2024_sales_report.md
echo "[setup] Raw data available:"
ls /workspace/raw_data/sales/
echo "[setup] Setup complete."