#!/bin/bash

# No additional tools needed beyond pip packages already installed

# Inform user of env var setup
if [ -z "$COMPOSIO_API_KEY" ]; then
  echo "Warning: COMPOSIO_API_KEY env var not set. Set it before running the task."
fi

