#!/bin/bash

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..

# Pre-build frontend (optional but speeds startup)
cd frontend
npm run build
cd ..

# The servers will be run automatically by the test harness using with_server.py
