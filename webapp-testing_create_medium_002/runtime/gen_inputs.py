import os

# Create backend server files
os.makedirs('backend', exist_ok=True)

backend_server_py = '''
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

items = []

class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/items':
            self._set_headers()
            self.wfile.write(json.dumps({'items': items}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/items':
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length)
            # Add a new item with a fixed marker text
            items.append('MarkerItem-12345')
            self._set_headers()
            self.wfile.write(json.dumps({'result': 'ok'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('', 4000)
    httpd = HTTPServer(server_address, SimpleHandler)
    print('Backend server running on port 4000')
    httpd.serve_forever()
'''

with open('backend/server.py', 'w') as f:
    f.write(backend_server_py)

# Create frontend React app files
eos.makedirs('frontend', exist_ok=True)

package_json = '''{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "dev": "react-scripts start",
    "build": "react-scripts build"
  }
}
'''

with open('frontend/package.json', 'w') as f:
    f.write(package_json)

app_js = '''import React, { useEffect, useState } from 'react';

function App() {
  const [items, setItems] = useState([]);

  // fetch items from backend
  useEffect(() => {
    fetch('http://localhost:4000/items')
      .then(res => res.json())
      .then(data => setItems(data.items))
  }, []);

  // Add item by POST to backend
  function addItem() {
    fetch('http://localhost:4000/items', { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        // After POST, fetch again
        fetch('http://localhost:4000/items')
          .then(res => res.json())
          .then(data => setItems(data.items))
      })
  }

  return (
    <div>
      <h1>Item List</h1>
      <button onClick={addItem}>Add Item</button>
      <ul>
        {items.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    </div>
  );
}

export default App;
'''

os.makedirs('frontend/src', exist_ok=True)
with open('frontend/src/App.js', 'w') as f:
    f.write(app_js)

# Minimal index.js and index.html
index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
'''
with open('frontend/src/index.js', 'w') as f:
    f.write(index_js)

index_html = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>React App</title></head><body><div id="root"></div></body></html>'''
public_dir = os.path.join('frontend', 'public')
os.makedirs(public_dir, exist_ok=True)
with open(os.path.join(public_dir, 'index.html'), 'w') as f:
    f.write(index_html)

# Create .gitignore for node_modules
with open('frontend/.gitignore', 'w') as f:
    f.write('node_modules\nbuild\n')

# Create empty package-lock.json placeholder
with open('frontend/package-lock.json', 'w') as f:
    f.write('{}')
