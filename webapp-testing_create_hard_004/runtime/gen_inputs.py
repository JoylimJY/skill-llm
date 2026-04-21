import os
import json

def create_backend():
    os.makedirs('backend', exist_ok=True)
    flask_code = '''
from flask import Flask, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route('/message')
def message():
    return jsonify({"message": "Hello from Flask Backend! [MARKER-BACKEND]"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
'''.strip()
    with open('backend/server.py', 'w') as f:
        f.write(flask_code)

    requirements = 'flask\nflask-cors\n'
    with open('backend/requirements.txt', 'w') as f:
        f.write(requirements)


def create_frontend():
    os.makedirs('frontend', exist_ok=True)
    # Minimal React app with button to fetch message from backend
    package_json = '''{
  "name": "frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
'''.strip()
    with open('frontend/package.json', 'w') as f:
        f.write(package_json)

    app_js = '''import React, { useState } from 'react';

export default function App() {
  const [message, setMessage] = useState('');
  const [btnText, setBtnText] = useState('Fetch Message');

  async function fetchMessage() {
    const res = await fetch('http://localhost:3000/message');
    const data = await res.json();
    setMessage(data.message + ' [MARKER-FRONTEND]');
    setBtnText('Refetch');
  }

  return (
    <div style={{ padding: 20 }}>
      <button onClick={fetchMessage}>{btnText}</button>
      {message && <p>{message}</p>}
    </div>
  );
}
'''.strip()

    src_dir = 'frontend/src'
    os.makedirs(src_dir, exist_ok=True)
    with open(os.path.join(src_dir, 'App.js'), 'w') as f:
        f.write(app_js)

    index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
'''.strip()
    with open(os.path.join(src_dir, 'index.js'), 'w') as f:
        f.write(index_js)

    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Test Frontend</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>
'''.strip()
    public_dir = 'frontend/public'
    os.makedirs(public_dir, exist_ok=True)
    with open(os.path.join(public_dir, 'index.html'), 'w') as f:
        f.write(index_html)

    # Also create minimal .env to ensure React runs on port 5173
    with open(os.path.join('frontend', '.env'), 'w') as f:
        f.write('PORT=5173\n')

    # Write package-lock.json empty to avoid warnings
    with open(os.path.join('frontend', 'package-lock.json'), 'w') as f:
        f.write('{}')


def generate():
    create_backend()
    create_frontend()

if __name__ == '__main__':
    generate()
