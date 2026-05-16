#!/bin/bash
set -e

# Ensure home directory exists and is writable
mkdir -p /home/user
chmod 755 /home/user

echo "Sandbox ready. Raw friend notes are in /home/user/raw_friend_notes/"
echo "Agent should create the friends system under /home/user/friends/"