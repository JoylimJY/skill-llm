#!/usr/bin/env bash
set -e

chmod +x /workspace/people_skill.py
chmod +x /workspace/database.py

cd /workspace
python -c "from database import PeopleDatabase; db = PeopleDatabase('people.db'); print('DB schema initialized OK')"

echo "Setup complete. Workspace contents:"
find /workspace -type f | sort