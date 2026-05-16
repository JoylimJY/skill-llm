#!/bin/bash
# No mock servers needed; all operations are local file I/O.
# Ensure meal-planner directory permissions are correct.
chmod -R 755 ~/meal-planner/
echo "Setup complete. meal-planner workspace ready."
ls -la ~/meal-planner/