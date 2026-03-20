#!/usr/bin/env python3
import os
import json

# Create backend Flask application
os.makedirs('backend', exist_ok=True)

backend_code = '''from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

# Initial users with marker content for verification
users = [
    {"id": 1, "name": "Alice Smith", "email": "alice@test-marker-2024.com"},
    {"id": 2, "name": "Bob Jones", "email": "bob@test-marker-2024.com"}
]
next_id = 3

@app.route('/api/users', methods=['GET'])
def get_users():
    # Simulate API delay
    time.sleep(2)
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def add_user():
    global next_id
    data = request.json
    new_user = {
        "id": next_id,
        "name": data.get('name'),
        "email": data.get('email')
    }
    users.append(new_user)
    next_id += 1
    time.sleep(1)  # Simulate processing time
    return jsonify(new_user), 201

@app.route('/health')
def health():
    return jsonify({"status": "ok", "marker": "test-backend-2024"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
'''

with open('backend/app.py', 'w') as f:
    f.write(backend_code)

# Create frontend React application structure
os.makedirs('frontend/src', exist_ok=True)
os.makedirs('frontend/public', exist_ok=True)

package_json = {
    "name": "user-dashboard",
    "version": "0.1.0",
    "private": True,
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-scripts": "5.0.1"
    },
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "dev": "BROWSER=none PORT=3000 react-scripts start"
    },
    "browserslist": {
        "production": [">0.2%", "not dead", "not op_mini all"],
        "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
    }
}

with open('frontend/package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>User Dashboard - Test Marker 2024</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
'''

with open('frontend/public/index.html', 'w') as f:
    f.write(index_html)

app_js = '''import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      console.log('MARKER: Fetching users from API');
      const response = await fetch('http://localhost:8080/api/users');
      const data = await response.json();
      setUsers(data);
      setLoading(false);
      console.log('MARKER: Users loaded successfully', data.length);
    } catch (error) {
      console.error('MARKER: Error fetching users:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      console.log('MARKER: Submitting new user', formData);
      const response = await fetch('http://localhost:8080/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        const newUser = await response.json();
        setUsers([...users, newUser]);
        setFormData({ name: '', email: '' });
        setShowForm(false);
        console.log('MARKER: User added successfully', newUser);
      }
    } catch (error) {
      console.error('MARKER: Error adding user:', error);
    }
    
    setSubmitting(false);
  };

  return (
    <div className="App">
      <h1 data-testid="page-title">User Dashboard</h1>
      <div className="marker-info">Test Environment 2024</div>
      
      {loading ? (
        <div data-testid="loading">Loading users...</div>
      ) : (
        <>
          <button 
            data-testid="add-user-btn"
            onClick={() => setShowForm(!showForm)}
            className="add-user-button"
          >
            Add User
          </button>
          
          {showForm && (
            <form onSubmit={handleSubmit} data-testid="user-form" className="user-form">
              <div>
                <input
                  type="text"
                  placeholder="Name"
                  data-testid="name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <input
                  type="email"
                  placeholder="Email"
                  data-testid="email-input"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>
              <button type="submit" data-testid="submit-btn" disabled={submitting}>
                {submitting ? 'Adding...' : 'Add User'}
              </button>
            </form>
          )}
          
          <div data-testid="user-list" className="user-list">
            <h2>Users ({users.length})</h2>
            {users.map((user) => (
              <div key={user.id} data-testid={`user-${user.id}`} className="user-item">
                <strong>{user.name}</strong> - {user.email}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default App;
'''

with open('frontend/src/App.js', 'w') as f:
    f.write(app_js)

app_css = '''.App {
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.marker-info {
  background: #f0f0f0;
  padding: 5px;
  font-size: 12px;
  color: #666;
}

.add-user-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  margin: 20px;
  cursor: pointer;
  border-radius: 4px;
}

.user-form {
  background: #f9f9f9;
  padding: 20px;
  margin: 20px;
  border-radius: 8px;
}

.user-form input {
  width: 200px;
  padding: 8px;
  margin: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.user-form button {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  margin: 10px;
  cursor: pointer;
  border-radius: 4px;
}

.user-list {
  margin: 20px;
}

.user-item {
  background: white;
  border: 1px solid #ddd;
  padding: 10px;
  margin: 5px 0;
  border-radius: 4px;
  text-align: left;
}
'''

with open('frontend/src/App.css', 'w') as f:
    f.write(app_css)

index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
'''

with open('frontend/src/index.js', 'w') as f:
    f.write(index_js)

print('Generated full-stack application with marker content for testing')