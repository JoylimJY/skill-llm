#!/usr/bin/env python3
import os
import json

# Create a minimal todo app
html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Todo App</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        input { padding: 8px; width: 300px; }
        button { padding: 8px 16px; cursor: pointer; }
        .todo-list { margin-top: 20px; }
        .todo-item { padding: 10px; border: 1px solid #ccc; margin: 5px 0; display: flex; align-items: center; }
        .todo-item.completed { text-decoration: line-through; color: #999; }
        .todo-item input[type="checkbox"] { margin-right: 10px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Todo App</h1>
    <div>
        <input type="text" id="todoInput" placeholder="Enter a todo item">
        <button id="addBtn">Add Todo</button>
    </div>
    <div class="todo-list" id="todoList"></div>
    <script>
        let todos = [];
        const input = document.getElementById('todoInput');
        const addBtn = document.getElementById('addBtn');
        const todoList = document.getElementById('todoList');
        
        function renderTodos() {
            todoList.innerHTML = '';
            todos.forEach((todo, index) => {
                const div = document.createElement('div');
                div.className = 'todo-item' + (todo.completed ? ' completed' : '');
                div.innerHTML = `
                    <input type="checkbox" ${todo.completed ? 'checked' : ''} onchange="toggleTodo(${index})">
                    <span>${todo.text}</span>
                `;
                todoList.appendChild(div);
            });
        }
        
        window.toggleTodo = function(index) {
            todos[index].completed = !todos[index].completed;
            renderTodos();
        };
        
        addBtn.addEventListener('click', () => {
            if (input.value.trim()) {
                todos.push({ text: input.value, completed: false });
                input.value = '';
                renderTodos();
            }
        });
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addBtn.click();
        });
    </script>
</body>
</html>'''

with open('index.html', 'w') as f:
    f.write(html_content)

# Create package.json for serving
pkg_json = {
    "name": "todo-app",
    "version": "1.0.0",
    "scripts": {
        "dev": "npx http-server -p 5173 -c-1"
    }
}

with open('package.json', 'w') as f:
    json.dump(pkg_json, f)

print('Generated todo app files')
