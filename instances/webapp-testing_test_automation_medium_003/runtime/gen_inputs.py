#!/usr/bin/env python3
import os
import json

# Create a simple React todo app
package_json = {
    "name": "todo-test-app",
    "version": "0.1.0",
    "private": True,
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-scripts": "5.0.1"
    },
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build"
    },
    "browserslist": {
        "production": [">0.2%", "not dead", "not op_mini all"],
        "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
    }
}

os.makedirs('todo-app', exist_ok=True)
os.makedirs('todo-app/src', exist_ok=True)
os.makedirs('todo-app/public', exist_ok=True)

with open('todo-app/package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

# Create the main App component with deterministic IDs and classes
app_js = '''import React, { useState } from 'react';
import './App.css';

function App() {
  const [todos, setTodos] = useState([
    { id: 1, text: 'MARKER_INITIAL_TODO_ITEM', completed: false }
  ]);
  const [inputValue, setInputValue] = useState('');

  const addTodo = () => {
    if (inputValue.trim()) {
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
      <h1 data-testid="app-title">MARKER_TODO_APP_TITLE</h1>
      <div className="todo-input">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Add a new todo..."
          data-testid="todo-input"
        />
        <button onClick={addTodo} data-testid="add-button">Add Todo</button>
      </div>
      <ul className="todo-list" data-testid="todo-list">
        {todos.map(todo => (
          <li key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
            <span 
              className="todo-text"
              style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}
            >
              {todo.text}
            </span>
            <button 
              onClick={() => toggleTodo(todo.id)}
              data-testid={`complete-${todo.id}`}
            >
              {todo.completed ? 'Undo' : 'Complete'}
            </button>
            <button 
              onClick={() => deleteTodo(todo.id)}
              data-testid={`delete-${todo.id}`}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
      <div data-testid="todo-count">Total todos: {todos.length}</div>
    </div>
  );
}

export default App;
'''

with open('todo-app/src/App.js', 'w') as f:
    f.write(app_js)

# Create basic CSS
app_css = '''.App {
  text-align: center;
  padding: 20px;
}

.todo-input {
  margin: 20px 0;
}

.todo-input input {
  padding: 8px;
  margin-right: 10px;
  width: 200px;
}

.todo-list {
  list-style: none;
  padding: 0;
  max-width: 400px;
  margin: 0 auto;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border: 1px solid #ddd;
  margin: 5px 0;
}

.todo-text {
  flex: 1;
  text-align: left;
  margin-right: 10px;
}

.completed .todo-text {
  opacity: 0.6;
}

button {
  margin-left: 5px;
  padding: 4px 8px;
  cursor: pointer;
}
'''

with open('todo-app/src/App.css', 'w') as f:
    f.write(app_css)

# Create index.js
index_js = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
'''

with open('todo-app/src/index.js', 'w') as f:
    f.write(index_js)

# Create public/index.html
index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Todo Test App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''

with open('todo-app/public/index.html', 'w') as f:
    f.write(index_html)

print("Generated React todo app with marker content for testing")
