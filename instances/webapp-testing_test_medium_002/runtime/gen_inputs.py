import os
import json

# Create package.json for React todo app
package_json = {
    "name": "todo-app",
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
        "test": "react-scripts test",
        "eject": "react-scripts eject"
    },
    "browserslist": {
        "production": [
            ">0.2%",
            "not dead",
            "not op_mini all"
        ],
        "development": [
            "last 1 chrome version",
            "last 1 firefox version",
            "last 1 safari version"
        ]
    }
}

with open('package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

# Create package-lock.json (minimal)
package_lock = {
    "name": "todo-app",
    "version": "0.1.0",
    "lockfileVersion": 2,
    "requires": True,
    "packages": {}
}

with open('package-lock.json', 'w') as f:
    json.dump(package_lock, f, indent=2)

# Create public directory
os.makedirs('public', exist_ok=True)

# Create index.html
index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Todo App - Test Marker: WEBAPP_TESTING_TODO_v1.0</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''

with open('public/index.html', 'w') as f:
    f.write(index_html)

# Create src directory
os.makedirs('src', exist_ok=True)

# Create App.js with todo functionality
app_js = '''import React, { useState } from 'react';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [inputValue, setInputValue] = useState('');

  const addTodo = () => {
    if (inputValue.trim() !== '') {
      setTodos([...todos, { 
        id: Date.now(), 
        text: inputValue, 
        completed: false 
      }]);
      setInputValue('');
    }
  };

  const toggleTodo = (id) => {
    setTodos(todos.map(todo => 
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  return (
    <div className="App">
      <h1 data-testid="app-title">Todo App - MARKER_WEBAPP_TEST_2024</h1>
      <div className="todo-input">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          placeholder="Enter a todo..."
          data-testid="todo-input"
        />
        <button onClick={addTodo} data-testid="add-button">Add Todo</button>
      </div>
      <div className="todo-list">
        {todos.map(todo => (
          <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`} data-testid="todo-item">
            <input 
              type="checkbox" 
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
              data-testid="todo-checkbox"
            />
            <span className="todo-text">{todo.text}</span>
            <button 
              onClick={() => deleteTodo(todo.id)} 
              className="delete-button"
              data-testid="delete-button"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
      <div className="todo-count" data-testid="todo-count">
        Total: {todos.length} | Completed: {todos.filter(t => t.completed).length}
      </div>
    </div>
  );
}

export default App;
'''

with open('src/App.js', 'w') as f:
    f.write(app_js)

# Create App.css
app_css = '''.App {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.todo-input {
  display: flex;
  margin-bottom: 20px;
  gap: 10px;
}

.todo-input input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.todo-input button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #eee;
  margin-bottom: 5px;
  gap: 10px;
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: #666;
}

.todo-text {
  flex: 1;
}

.delete-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.todo-count {
  margin-top: 20px;
  font-weight: bold;
  color: #666;
}
'''

with open('src/App.css', 'w') as f:
    f.write(app_css)

# Create index.js
index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''

with open('src/index.js', 'w') as f:
    f.write(index_js)

# Create index.css
index_css = '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
'''

with open('src/index.css', 'w') as f:
    f.write(index_css)

# Create scripts directory for testing tools
os.makedirs('scripts', exist_ok=True)

print("Generated React todo app with test markers")