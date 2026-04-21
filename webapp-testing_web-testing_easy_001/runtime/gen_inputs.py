import os

os.makedirs('app', exist_ok=True)

html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Test App</title>
</head>
<body>
    <h1>Welcome to My Test App</h1>
    <button id="clickBtn">Click Me</button>
    <p id="status">Waiting...</p>
    <script>
        document.getElementById('clickBtn').addEventListener('click', function() {
            document.getElementById('status').textContent = 'Button was clicked!';
        });
    </script>
</body>
</html>
'''

with open('app/index.html', 'w') as f:
    f.write(html_content)

print('Generated app/index.html')
