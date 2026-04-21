import os
import json
import textwrap

def make_backend():
    os.makedirs('backend', exist_ok=True)
    backend_code = textwrap.dedent('''
        from http.server import BaseHTTPRequestHandler, HTTPServer
        import json

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/items':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    data = {"items": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]}
                    self.wfile.write(json.dumps(data).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        if __name__ == '__main__':
            server = HTTPServer(('localhost', 3000), Handler)
            print('Backend server running on http://localhost:3000')
            server.serve_forever()
    ''')
    with open('backend/server.py', 'w') as f:
        f.write(backend_code)


def make_frontend():
    os.makedirs('frontend', exist_ok=True)

    # package.json with vite and react
    package_json = {
        "name": "frontend",
        "version": "1.0.0",
        "scripts": {"dev": "vite"},
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        },
        "devDependencies": {
            "vite": "^4.0.0",
            "@vitejs/plugin-react": "^3.0.0"
        }
    }
    with open('frontend/package.json', 'w') as f:
        json.dump(package_json, f, indent=2)

    # vite.config.js
    vite_config = textwrap.dedent('''
        import { defineConfig } from 'vite'
        import react from '@vitejs/plugin-react'

        export default defineConfig({
          plugins: [react()]
        })
    ''')
    with open('frontend/vite.config.js', 'w') as f:
        f.write(vite_config)

    # index.html
    index_html = textwrap.dedent('''
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Test Web App</title>
      </head>
      <body>
        <div id="root"></div>
        <script type="module" src="main.jsx"></script>
      </body>
    </html>
    ''')
    with open('frontend/index.html', 'w') as f:
        f.write(index_html)

    # main.jsx React app
    main_jsx = textwrap.dedent('''
    import React, {useState} from 'react';
    import ReactDOM from 'react-dom/client';

    function App() {
      const [items, setItems] = useState([]);

      function loadItems() {
        fetch('http://localhost:3000/items')
        .then(res => res.json())
        .then(data => setItems(data.items));
      }

      return (
        <div>
          <button onClick={loadItems}>Load Items</button>
          {items.length > 0 && (
            <ul id="items-list">
              {items.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          )}
        </div>
      )
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
    ''')
    with open('frontend/main.jsx', 'w') as f:
        f.write(main_jsx)


if __name__ == '__main__':
    make_backend()
    make_frontend()
