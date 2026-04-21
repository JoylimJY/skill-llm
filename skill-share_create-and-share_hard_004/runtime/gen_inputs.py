import os
import json
import yaml

# Create mock Slack API configuration
slack_config = {
    'workspace_id': 'T1234567890',
    'bot_token': 'xoxb-mock-token-12345',
    'channels': {
        'dev-tools': 'C1234567890',
        'general': 'C0987654321'
    }
}

with open('slack_config.json', 'w') as f:
    json.dump(slack_config, f, indent=2)

# Create sample database schemas for references
schemas = {
    'mysql_schema.sql': '''-- MySQL Schema Example
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total DECIMAL(10,2),
    status ENUM('pending', 'completed', 'cancelled'),
    FOREIGN KEY (user_id) REFERENCES users(id)
);''',
    
    'postgres_schema.sql': '''-- PostgreSQL Schema Example
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total NUMERIC(10,2),
    status VARCHAR(20) CHECK (status IN ('pending', 'completed', 'cancelled'))
);'''
}

for filename, content in schemas.items():
    with open(filename, 'w') as f:
        f.write(content)

# Create sample configuration templates
config_templates = {
    'migration_config.yaml': {
        'source_database': {
            'type': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'source_db',
            'username': '${SOURCE_USER}',
            'password': '${SOURCE_PASS}'
        },
        'target_database': {
            'type': 'postgresql',
            'host': 'localhost', 
            'port': 5432,
            'database': 'target_db',
            'username': '${TARGET_USER}',
            'password': '${TARGET_PASS}'
        },
        'migration_settings': {
            'batch_size': 1000,
            'parallel_workers': 4,
            'retry_attempts': 3,
            'verify_data': True
        }
    },
    
    'docker-compose.yml': '''version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: source_db
    ports:
      - "3306:3306"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: target_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
'''
}

for filename, content in config_templates.items():
    if filename.endswith('.yaml'):
        with open(filename, 'w') as f:
            yaml.dump(content, f, default_flow_style=False)
    else:
        with open(filename, 'w') as f:
            f.write(content)

print('Generated input files for skill-share task')