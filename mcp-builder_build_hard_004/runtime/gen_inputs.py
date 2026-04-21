import json
import os
from datetime import datetime, timedelta

# Fixed seed for deterministic outputs
PROJECTS_FILE = 'projects.json'
TASKS_FILE = 'tasks.json'
USERS_FILE = 'users.json'


def generate_projects():
    # Create 3 projects with clear marker content
    base_date = datetime(2023, 1, 1)
    projects = []
    markers = ['[PROJECT_MARKER_ALPHA]', '[PROJECT_MARKER_BETA]', '[PROJECT_MARKER_GAMMA]']
    for i in range(3):
        projects.append({
            'id': f'proj-{i+1}',
            'name': f'Project {chr(65+i)}',  # A, B, C
            'description': f'This is {markers[i]} description for project {chr(65+i)}.',
            'created_at': (base_date + timedelta(days=30*i)).isoformat(),
            'completed': i % 2 == 0,
            'completion_date': (base_date + timedelta(days=30*i + 60)).isoformat() if i % 2 == 0 else None
        })
    return projects


def generate_users():
    # Create 3 users with distinct marker content
    users = []
    markers = ['[USER_MARKER_EVE]', '[USER_MARKER_DAN]', '[USER_MARKER_KIM]']
    emails = ['eve@example.com', 'dan@example.com', 'kim@example.com']
    for i in range(3):
        users.append({
            'id': f'user-{i+1}',
            'username': f'user{i+1}',
            'full_name': f'User {markers[i]} Fullname',
            'email': emails[i],
            'active': True,
            'role': 'developer' if i != 2 else 'manager'
        })
    return users


def generate_tasks(projects, users):
    # Create 10 tasks distributed among projects and users
    tasks = []
    statuses = ['open', 'in_progress', 'closed']
    markers = ['[TASK_MARKER_ONE]', '[TASK_MARKER_TWO]', '[TASK_MARKER_THREE]', '[TASK_MARKER_FOUR]']
    for i in range(10):
        proj = projects[i % len(projects)]['id']
        user = users[i % len(users)]['id']
        status = statuses[i % len(statuses)]
        due_date = datetime(2023, 3, 1) + timedelta(days=7 * i)
        tasks.append({
            'id': f'task-{i+1}',
            'title': f'Task {i+1} {markers[i % len(markers)]}',
            'project_id': proj,
            'assignee_id': user,
            'status': status,
            'created_at': (due_date - timedelta(days=10)).isoformat(),
            'due_date': due_date.isoformat(),
            'description': f'Description for task {i+1} under project {proj} assigned to {user}.',
            'priority': ['low', 'medium', 'high'][i % 3]
        })
    return tasks


def main():
    projects = generate_projects()
    users = generate_users()
    tasks = generate_tasks(projects, users)

    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'projects': projects}, f, indent=2)

    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'users': users}, f, indent=2)

    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'tasks': tasks}, f, indent=2)

    print(f'Generated {PROJECTS_FILE}, {USERS_FILE}, and {TASKS_FILE}')


if __name__ == '__main__':
    main()
