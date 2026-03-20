import os
import json

# Create context files that would be referenced during doc creation
with open('existing_rate_limiter.py', 'w') as f:
    f.write('''# Current rate limiting implementation
class SimpleRateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
        # MARKER_LEGACY_SIMPLE_IMPLEMENTATION
        
    def is_allowed(self, client_id):
        # Basic in-memory rate limiting
        return True
''')

with open('team_requirements.md', 'w') as f:
    f.write('''# Rate Limiting Requirements

## Performance Goals
- Handle 50k requests/second
- Sub-5ms latency overhead
- 99.9% availability

## Features Needed
- Per-user and per-IP limits
- Dynamic configuration
- Redis clustering support
- MARKER_TEAM_PERFORMANCE_REQUIREMENTS

## Migration Constraints
- Zero downtime deployment
- Backwards compatibility for 2 weeks
''')

with open('redis_config.yaml', 'w') as f:
    f.write('''redis:
  cluster:
    nodes:
      - redis-1.internal:6379
      - redis-2.internal:6379
      - redis-3.internal:6379
  # MARKER_REDIS_CLUSTER_CONFIG
  connection_pool:
    max_connections: 50
    timeout: 5s
''')

# Create a template structure hint
with open('doc_template_hint.md', 'w') as f:
    f.write('''# Typical Technical Design Doc Structure

1. Overview & Goals
2. Current State Analysis 
3. Proposed Architecture
4. Implementation Details
5. Configuration & Usage
6. Migration Plan
7. Testing Strategy
8. Monitoring & Observability

# MARKER_TEMPLATE_STRUCTURE_GUIDE
''')

print("Generated context files for rate limiting design doc")