import os
import json

# Create a mock team channel discussion file
team_discussion = '''
# Authentication Issues Discussion - #eng-platform

**Alice Chen** [2024-01-15 10:30]
We've had 3 production incidents this month related to JWT token expiration. Users getting logged out mid-session during critical workflows.

**Bob Rodriguez** [2024-01-15 10:45] 
The refresh token logic is brittle. Sometimes the client doesn't handle the 401 gracefully and just shows a white screen.

**Carol Kim** [2024-01-15 11:00]
Security audit flagged our JWT implementation too. Tokens are too long-lived (24h) and we're not rotating secrets properly.

**David Park** [2024-01-15 11:15]
Session-based auth might be simpler. Redis is already in our stack. Concerned about scaling though - we have 50k DAU.

**Eve Thompson** [2024-01-15 11:30]
Mobile apps will need changes if we switch. iOS and Android teams need 2-3 sprints notice minimum.

**MARKER_CONTENT_AUTH_DISCUSSION_2024**
'''

with open('team_auth_discussion.txt', 'w') as f:
    f.write(team_discussion)

# Create existing system architecture notes
arch_notes = '''
# Current Authentication Architecture

## Components
- JWT tokens (24h expiration)
- Refresh tokens (7d expiration) 
- Auth service (Node.js)
- PostgreSQL user store
- Redis for rate limiting

## Issues
1. Complex token refresh logic in frontend
2. Long-lived tokens security risk
3. No proper token revocation
4. Mobile apps crash on token expiry
5. Audit compliance gaps

## Traffic
- 50,000 daily active users
- 2M API calls/day requiring auth
- 99.9% uptime SLA

MARKER_CONTENT_CURRENT_ARCH_SYSTEM
'''

with open('current_architecture.md', 'w') as f:
    f.write(arch_notes)

# Create security requirements document
security_reqs = '''
# Security Requirements for Authentication

## Compliance
- SOC2 Type II certification required
- Session timeout max 8 hours
- Proper audit logging
- Secure session storage

## Threats to Address
- Token theft/replay attacks
- Session fixation
- CSRF attacks
- Privilege escalation

MARKER_CONTENT_SECURITY_REQUIREMENTS_DOC
'''

with open('security_requirements.txt', 'w') as f:
    f.write(security_reqs)

print('Generated input files with marker content for RFC authoring task')