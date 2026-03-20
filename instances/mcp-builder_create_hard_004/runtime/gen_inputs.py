#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta
import random

# Set deterministic seed
random.seed(42)

# Generate mock Reddit API responses for testing
def generate_mock_data():
    # Create mock subreddit data
    subreddits = [
        {
            'id': 'sr_001',
            'name': 'technology',
            'display_name': 'r/technology',
            'subscribers': 15234567,
            'description': 'Subreddit for technology discussions and news',
            'created_utc': 1234567890,
            'public_description': 'Latest tech news and discussions'
        },
        {
            'id': 'sr_002', 
            'name': 'programming',
            'display_name': 'r/programming',
            'subscribers': 8901234,
            'description': 'Computer programming discussions',
            'created_utc': 1234567800,
            'public_description': 'Programming help and discussions'
        }
    ]
    
    # Create mock post data with marker content for verification
    posts = [
        {
            'id': 'post_ai_breakthrough',
            'title': 'Major AI breakthrough announced by tech company MARKER_TECH_2024',
            'author': 'tech_reporter_001',
            'subreddit': 'technology',
            'score': 4567,
            'num_comments': 234,
            'created_utc': int((datetime.now() - timedelta(days=1)).timestamp()),
            'selftext': 'This is a groundbreaking development in artificial intelligence that will change everything. VERIFICATION_MARKER_AI_CONTENT',
            'url': 'https://reddit.com/r/technology/comments/abc123/major_ai_breakthrough',
            'permalink': '/r/technology/comments/abc123/major_ai_breakthrough',
            'domain': 'self.technology'
        },
        {
            'id': 'post_python_tutorial',
            'title': 'Comprehensive Python tutorial for beginners MARKER_PYTHON_GUIDE',
            'author': 'python_guru_42',
            'subreddit': 'programming',
            'score': 1234,
            'num_comments': 89,
            'created_utc': int((datetime.now() - timedelta(days=2)).timestamp()),
            'selftext': 'Learn Python from scratch with this detailed guide. VERIFICATION_MARKER_PYTHON_TUTORIAL',
            'url': 'https://reddit.com/r/programming/comments/def456/python_tutorial',
            'permalink': '/r/programming/comments/def456/python_tutorial',
            'domain': 'self.programming'
        },
        {
            'id': 'post_security_alert',
            'title': 'Critical security vulnerability discovered in popular framework MARKER_SECURITY_2024',
            'author': 'security_expert_99',
            'subreddit': 'programming', 
            'score': 2890,
            'num_comments': 156,
            'created_utc': int((datetime.now() - timedelta(hours=6)).timestamp()),
            'selftext': 'Developers should update immediately to patch this critical issue. VERIFICATION_MARKER_SECURITY_ALERT',
            'url': 'https://reddit.com/r/programming/comments/ghi789/security_vulnerability',
            'permalink': '/r/programming/comments/ghi789/security_vulnerability',
            'domain': 'self.programming'
        }
    ]
    
    # Create mock comment data
    comments = [
        {
            'id': 'comment_001',
            'author': 'commenter_alpha',
            'body': 'This is really exciting! Thanks for sharing. VERIFICATION_MARKER_COMMENT_001',
            'score': 45,
            'created_utc': int((datetime.now() - timedelta(hours=12)).timestamp()),
            'parent_id': 'post_ai_breakthrough',
            'permalink': '/r/technology/comments/abc123/major_ai_breakthrough/comment_001'
        },
        {
            'id': 'comment_002', 
            'author': 'dev_student_123',
            'body': 'Great tutorial! Really helped me understand the concepts. VERIFICATION_MARKER_COMMENT_002',
            'score': 23,
            'created_utc': int((datetime.now() - timedelta(hours=18)).timestamp()),
            'parent_id': 'post_python_tutorial',
            'permalink': '/r/programming/comments/def456/python_tutorial/comment_002'
        }
    ]
    
    return subreddits, posts, comments

# Generate test data
subreddits, posts, comments = generate_mock_data()

# Save mock data for server to use
with open('mock_reddit_data.json', 'w') as f:
    json.dump({
        'subreddits': subreddits,
        'posts': posts, 
        'comments': comments
    }, f, indent=2)

# Create a sample requirements.txt that the user might reference
with open('requirements.txt', 'w') as f:
    f.write('''mcp>=1.6.0
pydantic>=2.0.0
httpx>=0.25.0
typing-extensions>=4.8.0
''')

# Create a README template
with open('README.md', 'w') as f:
    f.write('''# Reddit MCP Server

A Model Context Protocol server for Reddit integration providing read-only access to Reddit data.

## Features

- Search posts across subreddits
- Get subreddit information and statistics  
- Retrieve comment threads
- Support for both JSON and Markdown output formats
- Comprehensive pagination support
- Robust error handling

## Tools

- `reddit_search_posts` - Search for posts matching criteria
- `reddit_get_subreddit` - Get information about a specific subreddit
- `reddit_get_comments` - Retrieve comments for a post

## Usage

Run the server with:
```bash
python reddit_mcp.py
```
''')

print('Generated mock Reddit data and project files successfully.')