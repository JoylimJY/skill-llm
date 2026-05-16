#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying scenario files are in place..."
test -f /workspace/ops/scenarios/pending/order_request.json && echo "OK: order_request.json"
test -f /workspace/ops/config/addresses/priya_address_book.json && echo "OK: priya_address_book.json"
test -f /workspace/ops/connectors/swiggy/search_results.json && echo "OK: swiggy_search_results.json"
test -f /workspace/ops/connectors/zomato/search_results.json && echo "OK: zomato_search_results.json"

echo "Setup complete. Agent workspace ready."