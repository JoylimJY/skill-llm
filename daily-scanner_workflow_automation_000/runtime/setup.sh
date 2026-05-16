#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/Desktop

echo "Sandbox ready. Get笔记 directory contents:"
find /workspace/Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记/ -type f | sort

echo ""
echo "File modification times (to verify 24h window):"
find /workspace/Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记/ -type f -printf "%T@ %Tc %f\n" | sort