#!/usr/bin/env bash
set -e

cd /workspace

# Ensure node_modules has glin-profanity available
if [ ! -d "node_modules/glin-profanity" ]; then
    npm install glin-profanity
fi

# Ensure package.json has type:module or commonjs — default commonjs is fine
# Give agent write permissions across workspace
chmod -R 777 /workspace

echo "Setup complete."