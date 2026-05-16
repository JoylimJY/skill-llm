#!/bin/bash
set -e

# ── Mock server script ──────────────────────────────────────────────────────
cat > /mock_server.py << 'PYEOF'
from flask import Flask, jsonify, abort
import json, os

app = Flask(__name__)

SEARCH_DATA = [
    {
        "name_en": "Confucius",
        "name_zh": "孔子",
        "url": "/real_world/confucius/",
        "category_en": "Real World",
        "category_zh": "真实世界",
        "tags": ["philosopher", "wisdom", "china", "ancient"],
        "tags_en": ["philosopher", "wisdom", "china", "ancient"],
        "tags_zh": ["哲学家", "智慧", "中国", "古代"]
    },
    {
        "name_en": "Sun Wukong",
        "name_zh": "孙悟空",
        "url": "/virtual_world/sun_wukong/",
        "category_en": "Virtual World",
        "category_zh": "虚拟世界",
        "tags": ["monkey king", "journey to the west", "mythical", "trickster"],
        "tags_en": ["monkey king", "journey to the west", "mythical", "trickster"],
        "tags_zh": ["猴王", "西游记", "神话", "恶作剧者"]
    },
    {
        "name_en": "Sherlock Holmes",
        "name_zh": "夏洛克·福尔摩斯",
        "url": "/virtual_world/sherlock_holmes/",
        "category_en": "Virtual World",
        "category_zh": "虚拟世界",
        "tags": ["detective", "deduction", "mystery", "london"],
        "tags_en": ["detective", "deduction", "mystery", "london"],
        "tags_zh": ["侦探", "演绎", "谜团", "伦敦"]
    }
]

CONFUCIUS_SOUL = """# Confucius Persona

You are Confucius (孔子), the great Chinese philosopher and teacher from the Spring and Autumn period.

## Core Philosophy
- Emphasize ren (benevolence) and li (ritual propriety)
- Teach through analogy and reflection
- Value education, family, and social harmony

## Speaking Style
Speak with measured wisdom. Use classical maxims. Reference virtue, learning, and moral cultivation.

## Sample Responses
- "Is it not pleasant to learn with a constant perseverance and application?"
- "The man who moves a mountain begins by carrying away small stones."
"""

SUN_WUKONG_SOUL = """# Sun Wukong Persona

You are Sun Wukong (孙悟空), the Monkey King from Journey to the West, born from stone and master of 72 transformations.

## Core Traits
- Irreverent, boastful, and fiercely loyal once tamed
- Possesses immense magical power and cunning
- Carries the magical staff Ruyi Jingu Bang

## Speaking Style
Bold, energetic, slightly arrogant. Refer to yourself in the third person occasionally. Brag about your abilities but show wisdom when it matters.

## Sample Responses
- "Ha! Old Sun has defeated dragons and demons — this problem is nothing!"
- "Seventy-two transformations and not one of them has ever failed me."
"""

@app.route('/search.json')
def search():
    return jsonify(SEARCH_DATA)

@app.route('/real_world/confucius/SOUL.en.md')
def confucius_en():
    return CONFUCIUS_SOUL, 200, {'Content-Type': 'text/plain'}

@app.route('/real_world/confucius/SOUL.md')
def confucius_zh():
    return CONFUCIUS_SOUL, 200, {'Content-Type': 'text/plain'}

@app.route('/virtual_world/sun_wukong/SOUL.en.md')
def sun_wukong_en():
    return SUN_WUKONG_SOUL, 200, {'Content-Type': 'text/plain'}

@app.route('/virtual_world/sun_wukong/SOUL.md')
def sun_wukong_zh():
    return SUN_WUKONG_SOUL, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8899, debug=False)
PYEOF

# Start the mock server in the background
python /mock_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID on port 8899"

# Wait for the server to be ready
for i in $(seq 1 15); do
    if curl -sf http://localhost:8899/search.json > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 1
done

# Redirect agent-souls.com to localhost via /etc/hosts
echo "127.0.0.1 agent-souls.com" >> /etc/hosts
echo "Host override added: agent-souls.com -> 127.0.0.1"

# Verify the redirect works
curl -sf http://agent-souls.com:8899/search.json | head -c 200 || echo "Warning: host redirect check failed"

# The mock server listens on 8899, but the skill uses WebFetch to https://agent-souls.com
# We need to redirect port 80 to 8899 so http requests work
# Use iptables or socat to forward port 80 -> 8899
if command -v socat &>/dev/null; then
    socat TCP-LISTEN:80,fork TCP:127.0.0.1:8899 &
    echo "socat forwarding port 80 -> 8899"
else
    # fallback: use iptables
    iptables -t nat -A OUTPUT -p tcp --dport 80 -d 127.0.0.1 -j REDIRECT --to-port 8899 2>/dev/null || true
    echo "Attempted iptables redirect 80->8899"
fi

# Also handle port 443 (https) — redirect to 80 via iptables if possible
iptables -t nat -A OUTPUT -p tcp --dport 443 -d 127.0.0.1 -j REDIRECT --to-port 8899 2>/dev/null || true

sleep 1
echo "Setup complete."