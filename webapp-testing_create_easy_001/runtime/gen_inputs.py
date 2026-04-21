import os

def main():
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Test Page</title>
    <script>
      function onClick() {
        const btn = document.getElementById('mybtn');
        btn.innerText = 'Clicked!';
      }
    </script>
</head>
<body>
    <button id="mybtn" onclick="onClick()">Click Me</button>
</body>
</html>
'''

    with open('page.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    main()
