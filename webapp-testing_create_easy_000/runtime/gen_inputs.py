import os

# Generate a minimal HTML + JS file simulating a local dynamic webapp on port 5173

HTML_CONTENT = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Test App</title>
  <script>
    function onButtonClick() {
      const result = document.createElement('div');
      result.id = 'result';
      result.textContent = 'Button clicked successfully!';
      document.body.appendChild(result);
    }
    window.onload = () => {
      const btn = document.getElementById('clickBtn');
      if(btn) btn.addEventListener('click', onButtonClick);
    };
  </script>
</head>
<body>
  <button id="clickBtn">Click Me</button>
</body>
</html>
'''

# Write the HTML file to ./frontend/index.html
os.makedirs('frontend', exist_ok=True)
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)

# Generate a simple server to serve this static HTML on port 5173
SERVER_SCRIPT = '''import http.server
import socketserver

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)

PORT = 5173
with socketserver.TCPServer(('localhost', PORT), Handler) as httpd:
    print(f'Serving HTTP on port {PORT}...')
    httpd.serve_forever()
'''

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(SERVER_SCRIPT)
