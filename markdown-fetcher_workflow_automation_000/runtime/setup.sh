#!/bin/bash
set -e

# Write the mock server that simulates markdown.new, defuddle.md, r.jina.ai behavior
cat > /workspace/mock_server.py << 'MOCK_SERVER_EOF'
#!/usr/bin/env python3
"""
Mock server that simulates the markdown conversion services with realistic fallback behavior.
- markdown.new endpoint: ALWAYS returns 503 (unavailable for these non-Cloudflare URLs)
- defuddle.md endpoint: Returns 404 for URL1, 503 for URL2, 200 for URL3
- r.jina.ai endpoint: Returns 200 with valid Markdown for URL1, URL2 (those defuddle failed)
- Logs all access attempts to /workspace/logs/mock_access.log
"""

from flask import Flask, request, Response
import re
import datetime
import json

app = Flask(__name__)
LOG_FILE = "/workspace/logs/mock_access.log"

MARKDOWN_CONTENT = {
    "neural-plasticity-2024": """# Neural Plasticity in the Adult Brain: 2024 Research Review

**Source:** example-research.org  
**Date:** 2024-03-15

## Abstract

Recent advances in neuroscience have revealed remarkable plasticity in adult neural circuits. This review synthesizes findings from over 200 studies conducted between 2020-2024.

## Key Findings

- Synaptic remodeling occurs continuously throughout adult life
- Environmental enrichment promotes dendritic arborization
- BDNF signaling is critical for experience-dependent plasticity

## Methods

Studies employed a combination of two-photon microscopy, electrophysiology, and behavioral assays.

## Conclusion

Adult neural plasticity is far more extensive than previously thought, with significant implications for treating neurological disorders.
""",
    "quantum-entanglement-review": """# Quantum Entanglement: A Comprehensive Review

**Source:** scijournal.net  
**Date:** 2024-01-20

## Introduction

Quantum entanglement remains one of the most fascinating phenomena in modern physics. This review covers theoretical foundations and experimental demonstrations.

## Historical Context

- Einstein-Podolsky-Rosen paradox (1935)
- Bell's theorem (1964)
- Aspect experiments (1982)

## Recent Advances

Long-distance entanglement distribution over 1000km fiber links has been demonstrated in 2023-2024.

## Applications

- Quantum cryptography
- Quantum teleportation
- Quantum computing

## References

1. Aspect et al., Physical Review Letters, 1982
2. Pan et al., Nature, 2023
""",
    "crispr-advances-2024": """# CRISPR Technology Advances in 2024

**Source:** biotech-weekly.com  
**Date:** 2024-05-10

## Overview

CRISPR-Cas9 and next-generation base editing technologies have reached new milestones in 2024.

## Clinical Breakthroughs

- First approved CRISPR therapy for sickle cell disease
- Successful in vivo base editing in liver cells
- Prime editing reduces off-target effects by 90%

## Agricultural Applications

- Disease-resistant crops with improved yield
- Precision breeding without foreign DNA insertion

## Ethical Considerations

Regulatory frameworks are evolving globally to address germline editing concerns.

## Future Outlook

2025 is expected to see 10+ CRISPR-based therapies in Phase III clinical trials.
"""
}

URL_TO_KEY = {
    "https://example-research.org/articles/neural-plasticity-2024": "neural-plasticity-2024",
    "https://scijournal.net/papers/quantum-entanglement-review": "quantum-entanglement-review",
    "https://biotech-weekly.com/crispr-advances-2024": "crispr-advances-2024",
}

def log_access(service, url, status_code):
    timestamp = datetime.datetime.now().isoformat()
    entry = {"timestamp": timestamp, "service": service, "url": url, "status": status_code}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def extract_target_url(path):
    """Extract the target URL from the path, handling both /https://... and /https://... patterns"""
    # path comes in as /https://example.com/... 
    if path.startswith("/"):
        path = path[1:]
    # Reconstruct full URL - path may have had double slash collapsed
    if path.startswith("https:/") and not path.startswith("https://"):
        path = "https://" + path[7:]
    elif path.startswith("http:/") and not path.startswith("http://"):
        path = "http://" + path[6:]
    return path

@app.route("/markdown_new/<path:target_url>")
def markdown_new(target_url):
    full_url = "https://" + target_url
    log_access("markdown.new", full_url, 503)
    return Response("Service Unavailable - This site is not Cloudflare-hosted", status=503, 
                   content_type="text/plain")

@app.route("/defuddle_md/<path:target_url>")
def defuddle_md(target_url):
    full_url = "https://" + target_url
    # Find the key
    content_key = None
    for url_key, key in URL_TO_KEY.items():
        if url_key == full_url or url_key.rstrip("/") == full_url.rstrip("/"):
            content_key = key
            break
    
    if content_key == "neural-plasticity-2024":
        log_access("defuddle.md", full_url, 404)
        return Response("Not Found", status=404, content_type="text/plain")
    elif content_key == "quantum-entanglement-review":
        log_access("defuddle.md", full_url, 503)
        return Response("Service temporarily unavailable", status=503, content_type="text/plain")
    elif content_key == "crispr-advances-2024":
        log_access("defuddle.md", full_url, 200)
        return Response(MARKDOWN_CONTENT[content_key], status=200, content_type="text/markdown")
    
    log_access("defuddle.md", full_url, 404)
    return Response("Not Found", status=404, content_type="text/plain")

@app.route("/r_jina/<path:target_url>")
def r_jina(target_url):
    full_url = "https://" + target_url
    content_key = None
    for url_key, key in URL_TO_KEY.items():
        if url_key == full_url or url_key.rstrip("/") == full_url.rstrip("/"):
            content_key = key
            break
    
    if content_key:
        log_access("r.jina.ai", full_url, 200)
        return Response(MARKDOWN_CONTENT[content_key], status=200, content_type="text/markdown")
    
    log_access("r.jina.ai", full_url, 404)
    return Response("Not Found", status=404, content_type="text/plain")

if __name__ == "__main__":
    import os
    os.makedirs("/workspace/logs", exist_ok=True)
    # Clear old log
    open(LOG_FILE, "w").close()
    app.run(host="0.0.0.0", port=18765, debug=False)
MOCK_SERVER_EOF

chmod +x /workspace/mock_server.py

# Write a hosts-style redirect config so the agent can use the mock server
# We'll use a proxy configuration approach - write a helper script that rewrites URLs
cat > /workspace/url_rewriter.py << 'REWRITER_EOF'
#!/usr/bin/env python3
"""
URL rewriting helper. 
Maps the real markdown service URLs to the local mock server.
The mock server runs on localhost:18765 with these endpoints:
  - /markdown_new/{url_without_prefix} -> simulates markdown.new/{url}
  - /defuddle_md/{url_without_prefix}  -> simulates defuddle.md/{url}
  - /r_jina/{url_without_prefix}       -> simulates r.jina.ai/{url}
"""

SERVICE_MAP = {
    "markdown.new": "http://localhost:18765/markdown_new",
    "defuddle.md": "http://localhost:18765/defuddle_md", 
    "r.jina.ai": "http://localhost:18765/r_jina",
}

def rewrite(service_url):
    """Given a full service URL like https://r.jina.ai/https://example.com, return mock URL"""
    for service, mock_base in SERVICE_MAP.items():
        prefix = f"https://{service}/"
        if service_url.startswith(prefix):
            target = service_url[len(prefix):]
            # Strip https:// from target for path routing
            if target.startswith("https://"):
                target = target[8:]
            elif target.startswith("http://"):
                target = target[7:]
            return f"{mock_base}/{target}"
    return service_url

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(rewrite(sys.argv[1]))
REWRITER_EOF

chmod +x /workspace/url_rewriter.py

# Start mock server in background
python3 /workspace/mock_server.py &
MOCK_PID=$!
echo $MOCK_PID > /workspace/mock_server.pid
echo "Mock server started with PID $MOCK_PID"

# Wait for server to be ready
sleep 2

# Verify server is running
for i in {1..10}; do
    if curl -s http://localhost:18765/markdown_new/example.com > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

# Write agent instructions file that describes the mock server mapping
cat > /workspace/SERVICE_ENDPOINTS.txt << 'ENDPOINTS_EOF'
LOCAL MOCK SERVER CONFIGURATION
================================
The following markdown conversion services are available via local mock server at localhost:18765.
When using these services, route through the mock server using the mappings below:

  markdown.new/{url}  ->  http://localhost:18765/markdown_new/{url_without_https_prefix}
  defuddle.md/{url}   ->  http://localhost:18765/defuddle_md/{url_without_https_prefix}  
  r.jina.ai/{url}     ->  http://localhost:18765/r_jina/{url_without_https_prefix}

The url_rewriter.py script in /workspace can help translate full service URLs to mock endpoints.

Example:
  Service URL:  https://r.jina.ai/https://example.com/article
  Mock URL:     http://localhost:18765/r_jina/example.com/article
ENDPOINTS_EOF

echo "Setup complete. Mock server running on port 18765."
echo "Task file: /workspace/fetch_tasks.json"
echo "Service endpoints guide: /workspace/SERVICE_ENDPOINTS.txt"