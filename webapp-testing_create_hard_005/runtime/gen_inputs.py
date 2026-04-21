import os
import json

# Create backend minimal Flask API server
backend_code = '''
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/items')
def items():
    # Return a static list of items
    return jsonify(["Item-1", "Item-2", "Item-3"])

@app.route('/')
def root():
    return 'Backend API root'

if __name__ == '__main__':
    app.run(port=3000)
'''

# Create frontend React app (minimal)
# package.json
package_json = '''{
  "name": "frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "scripts": {
    "dev": "vite"
  },
  "devDependencies": {
    "vite": "^4.0.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
'''

# vite.config.js
vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 }
})
'''

# src/main.jsx
main_jsx = '''import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'

function App() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    setLoading(true);
    const res = await fetch('http://localhost:3000/api/items');
    const data = await res.json();
    setItems(data);
    setLoading(false);
  }

  return <div>
    <h1>Data Fetch Test App</h1>
    <button onClick={loadData}>Load Data</button>
    {loading && <p>Loading...</p>}
    <ul>
      {items.map((item, idx) => <li key={idx}>{item}</li>)}
    </ul>
  </div>
}

const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)
'''

# index.html
index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>React App</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
'''

# Write backend server
os.makedirs('backend', exist_ok=True)
with open('backend/server.py', 'w') as f:
    f.write(backend_code)

# Write frontend app
os.makedirs('frontend/src', exist_ok=True)

with open('frontend/package.json', 'w') as f:
    f.write(package_json)

with open('frontend/vite.config.js', 'w') as f:
    f.write(vite_config)

with open('frontend/src/main.jsx', 'w') as f:
    f.write(main_jsx)

with open('frontend/index.html', 'w') as f:
    f.write(index_html)

# Write the required with_server.py helper (identical to provided script)
with_server_py = '''#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py
"""

import subprocess
import socket
import time
import sys
import argparse

def is_server_ready(port, timeout=30):
    """Wait for server to be ready by polling the port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command (can be repeated)')
    parser.add_argument('--port', action='append', dest='ports', type=int, required=True, help='Port for each server (must match --server count)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds per server (default: 30)')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after server(s) ready')

    args = parser.parse_args()

    # Remove the '--' separator if present
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]

    if not args.command:
        print("Error: No command specified to run")
        sys.exit(1)

    # Parse server configurations
    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    server_processes = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Use shell=True to support commands with cd and &&
            process = subprocess.Popen(
                server['cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on port {server['port']}...")
            if not is_server_ready(server['port'], timeout=args.timeout):
                raise RuntimeError(f"Server failed to start on port {server['port']} within {args.timeout}s")

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

        # Run the command
        print(f"Running: {' '.join(args.command)}\n")
        result = subprocess.run(args.command)
        sys.exit(result.returncode)

    finally:
        # Clean up all servers
        print(f"\nStopping {len(server_processes)} server(s)...")
        for i, process in enumerate(server_processes):
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print(f"Server {i+1} stopped")
        print("All servers stopped")


if __name__ == '__main__':
    main()
'''

os.makedirs('scripts', exist_ok=True)
with open('scripts/with_server.py', 'w') as f:
    f.write(with_server_py)

# Make helper executable
os.chmod('scripts/with_server.py', 0o755)

# Write the test playwright script skeleton as a template for user
playwright_test = '''
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on('console', lambda msg: print(f'LOG: {msg.type}: {msg.text}'))
        
        page.goto('http://localhost:5173')
        page.wait_for_load_state('networkidle')

        # Take screenshot
        page.screenshot(path='screenshot_inspect.png', full_page=True)

        # Extract content
        content = page.content()
        print('Page content length:', len(content))

        # Discover buttons
        buttons = page.locator('button')
        texts = buttons.all_inner_texts()
        print('Buttons found:', texts)

        # Click 'Load Data' button
        try:
            load_button = page.locator('button', has_text='Load Data')
            load_button.click()
            page.wait_for_selector('ul li', timeout=5000)

            # Check if 'Item-1' is in list
            items = page.locator('ul li').all_inner_texts()
            if any('item-1' in it.lower() for it in items):
                print('Item-1 found in list')
            else:
                print('Item-1 NOT found in list')

        except Exception as e:
            print('Error during interaction:', e)

        browser.close()

if __name__ == '__main__':
    main()
'''

with open('test_playwright.py', 'w') as f:
    f.write(playwright_test)
