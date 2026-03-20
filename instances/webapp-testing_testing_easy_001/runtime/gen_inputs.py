#!/usr/bin/env python3
import os

# Create a simple HTML login form
html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Form Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .form-container { max-width: 400px; margin: 0 auto; }
        input, button { display: block; width: 100%; margin: 10px 0; padding: 10px; }
        button { background-color: #007bff; color: white; border: none; cursor: pointer; }
        .success-message { color: green; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="form-container">
        <h1>Login Form</h1>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit" id="submitBtn">Login</button>
        </form>
        <div id="result"></div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (username === 'testuser' && password === 'testpass123') {
                document.getElementById('result').innerHTML = 
                    '<div class="success-message">LOGIN_SUCCESS_MARKER - Welcome testuser!</div>';
            } else {
                document.getElementById('result').innerHTML = 
                    '<div style="color: red;">Invalid credentials</div>';
            }
        });
    </script>
</body>
</html>'''

with open('index.html', 'w') as f:
    f.write(html_content)

print("Created index.html with login form")