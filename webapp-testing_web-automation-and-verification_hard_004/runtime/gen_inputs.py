#!/usr/bin/env python3
import os
import json

os.makedirs('app', exist_ok=True)

# Create a minimal Vue.js app with login, dashboard, and modal
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Test Web App</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .login-form { max-width: 300px; }
        .login-form input { display: block; margin: 10px 0; padding: 8px; width: 100%; }
        .login-form button { padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        .dashboard { display: none; }
        .dashboard.active { display: block; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        table th, table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        table tr:hover { background: #f5f5f5; cursor: pointer; }
        .modal { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; border: 2px solid #333; padding: 20px; z-index: 1000; min-width: 400px; }
        .modal.active { display: block; }
        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999; }
        .modal-overlay.active { display: block; }
        .modal input { display: block; margin: 10px 0; padding: 8px; width: 100%; }
        .modal button { padding: 10px; margin-right: 10px; cursor: pointer; }
        .close-btn { background: #dc3545; color: white; border: none; }
    </style>
</head>
<body>
    <div id="app">
        <div class="login-form" id="loginForm">
            <h2>Login</h2>
            <input type="text" id="username" placeholder="Username" value="testuser">
            <input type="password" id="password" placeholder="Password" value="testpass">
            <button onclick="handleLogin()">Login</button>
        </div>
        
        <div class="dashboard" id="dashboard">
            <h2>Dashboard</h2>
            <table id="dataTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
        
        <div class="modal-overlay" id="modalOverlay" onclick="closeModal()"></div>
        <div class="modal" id="editModal">
            <h3>Edit Record</h3>
            <input type="hidden" id="recordId">
            <label>Name:</label>
            <input type="text" id="recordName" readonly>
            <label>Email:</label>
            <input type="text" id="recordEmail" readonly>
            <label>Status:</label>
            <input type="text" id="recordStatus" readonly>
            <button onclick="closeModal()" class="close-btn">Close</button>
        </div>
    </div>
    
    <script>
        const mockData = [
            { id: 1, name: "Alice Johnson", email: "alice@example.com", status: "Active" },
            { id: 2, name: "Bob Smith", email: "bob@example.com", status: "Inactive" },
            { id: 3, name: "Charlie Brown", email: "charlie@example.com", status: "Active" }
        ];
        
        function handleLogin() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            if (username === 'testuser' && password === 'testpass') {
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('dashboard').classList.add('active');
                loadTableData();
            }
        }
        
        function loadTableData() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            mockData.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${record.id}</td><td>${record.name}</td><td>${record.email}</td><td>${record.status}</td>`;
                row.onclick = () => openModal(record);
                tbody.appendChild(row);
            });
        }
        
        function openModal(record) {
            document.getElementById('recordId').value = record.id;
            document.getElementById('recordName').value = record.name;
            document.getElementById('recordEmail').value = record.email;
            document.getElementById('recordStatus').value = record.status;
            document.getElementById('modalOverlay').classList.add('active');
            document.getElementById('editModal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('modalOverlay').classList.remove('active');
            document.getElementById('editModal').classList.remove('active');
        }
    </script>
</body>
</html>'''

with open('app/index.html', 'w') as f:
    f.write(html_content)

# Create package.json for serving
package_json = {
    "name": "test-app",
    "version": "1.0.0",
    "scripts": {
        "dev": "npx http-server -p 5173 -c-1"
    },
    "devDependencies": {
        "http-server": "^14.1.1"
    }
}

with open('app/package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

print('Generated test app files')
