# Create a simple static HTML file with known marker content
with open('index.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f8ff; margin: 40px; }
        h1 { color: #2c3e50; }
        p { color: #555; }
        .marker-box { background: #e8f5e9; border: 2px solid #4caf50; padding: 20px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Hello Playwright World</h1>
    <p>This is a test page for screenshot automation.</p>
    <div class="marker-box">
        <strong>MARKER-SCREENSHOT-TEST-2024</strong>
        <p>If you can see this, the screenshot worked!</p>
    </div>
</body>
</html>''')
print('index.html created successfully')
