#!/bin/bash

set -e

# Install yarn (for frontend dependencies and dev start)
apt-get update
apt-get install -y curl
curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/yarnkey.gpg
echo "deb [signed-by=/usr/share/keyrings/yarnkey.gpg] https://dl.yarnpkg.com/debian stable main" | tee /etc/apt/sources.list.d/yarn.list
apt-get update && apt-get install yarn -y

# Install frontend dependencies
cd frontend
npm install
cd ..

# Make sure scripts/with_server.py is executable
chmod +x scripts/with_server.py
