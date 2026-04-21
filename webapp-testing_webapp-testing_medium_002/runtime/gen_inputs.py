import os
import json

# Create the todo web app
app_dir = 'todo-app'
os.makedirs(app_dir, exist_ok=True)

# Create package.json
package_json = {
    "name": "todo-app",
    "version": "1.0.0",
    "scripts": {
        "dev": "node server.js"
    },
    "dependencies": {}
}

with open(os.path.join(app_dir, 'package.json'), 'w') as f:
    json.dump(package_json, f, indent=2)

# Create the server
server_js = '''const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo List</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        #todo-input { width: 70%; padding: 8px; font-size: 16px; }
        #add-btn { padding: 8px 16px; font-size: 16px; cursor: pointer; background: #4CAF50; color: white; border: none; }
        #todo-list { list-style: none; padding: 0; margin-top: 20px; }
        #todo-list li { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        #todo-list li.completed span { text-decoration: line-through; color: #999; }
        #todo-list li input[type=checkbox] { margin-right: 10px; }
    </style>
</head>
<body>
    <h1>Todo List</h1>
    <div>
        <input type="text" id="todo-input" placeholder="Add a new todo..." />
        <button id="add-btn">Add</button>
    </div>
    <ul id="todo-list"></ul>
    <script>
        const input = document.getElementById(\'todo-input\');
        const addBtn = document.getElementById(\'add-btn\');
        const list = document.getElementById(\'todo-list\');

        function addTodo(text) {
            if (!text.trim()) return;
            const li = document.createElement(\'li\');
            const checkbox = document.createElement(\'input\');
            checkbox.type = \'checkbox\';
            checkbox.addEventListener(\'change\', () => {
                if (checkbox.checked) {
                    li.classList.add(\'completed\');
                } else {
                    li.classList.remove(\'completed\');
                }
            });
            const span = document.createElement(\'span\');
            span.textContent = text;
            li.appendChild(checkbox);
            li.appendChild(span);
            list.appendChild(li);
            input.value = \'\';
        }

        addBtn.addEventListener(\'click\', () => addTodo(input.value));
        input.addEventListener(\'keypress\', (e) => {
            if (e.key === \'Enter\') addTodo(input.value);
        });
    </script>
</body>
</html>`;

const server = http.createServer((req, res) => {
    res.writeHead(200, { \'Content-Type\': \'text/html\' });
    res.end(html);
});

server.listen(PORT, () => {
    console.log(`Todo app running at http://localhost:${PORT}`);
});
'''

with open(os.path.join(app_dir, 'server.js'), 'w') as f:
    f.write(server_js)

print('Todo app files created in ./todo-app/')
print('Start with: cd todo-app && npm run dev')
