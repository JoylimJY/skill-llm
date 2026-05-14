import os
import random
import struct
import json
import hashlib

random.seed(42)

workspace = "/workspace"

# ─────────────────────────────────────────────
# 1. Clone and install hex-vetter into /workspace/hex-vetter
# ─────────────────────────────────────────────
# This will be done in setup_script via git clone
# Here we just create the skill packages to audit

skills_dir = os.path.join(workspace, "incoming_skills")
os.makedirs(skills_dir, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Create realistic skill package subdirectories
# ─────────────────────────────────────────────

# skill-alpha: CLEAN skill (LOW risk expected)
alpha_dir = os.path.join(skills_dir, "skill-alpha")
os.makedirs(alpha_dir, exist_ok=True)

with open(os.path.join(alpha_dir, "index.js"), "w") as f:
    f.write("""'use strict';
// skill-alpha: A simple text summarization skill
const summarize = (text) => {
  const sentences = text.split('. ');
  return sentences.slice(0, 3).join('. ');
};
module.exports = { summarize };
""")

with open(os.path.join(alpha_dir, "package.json"), "w") as f:
    json.dump({
        "name": "skill-alpha",
        "version": "1.0.0",
        "description": "Text summarization",
        "main": "index.js"
    }, f, indent=2)

with open(os.path.join(alpha_dir, "utils.js"), "w") as f:
    f.write("""// Utility functions
const clean = (s) => s.trim().replace(/\\s+/g, ' ');
const tokenize = (s) => s.split(' ');
module.exports = { clean, tokenize };
""")

with open(os.path.join(alpha_dir, "config.json"), "w") as f:
    json.dump({"maxSentences": 3, "language": "en"}, f, indent=2)

# skill-beta: Contains NULL_BYTES and MAGIC_BYTES → HIGH risk
beta_dir = os.path.join(skills_dir, "skill-beta")
os.makedirs(beta_dir, exist_ok=True)

# payload.bin: starts with ELF magic bytes + null bytes (HIGH)
with open(os.path.join(beta_dir, "payload.bin"), "wb") as f:
    # ELF magic header
    f.write(b'\x7fELF')
    f.write(b'\x02\x01\x01\x00')
    f.write(b'\x00' * 8)   # null bytes padding
    f.write(b'\x02\x00\x3e\x00')
    f.write(b'\x01\x00\x00\x00')
    f.write(bytes(range(32, 96)))  # ASCII range filler

with open(os.path.join(beta_dir, "index.js"), "w") as f:
    f.write("""'use strict';
// skill-beta: Translation skill
const translate = async (text, lang) => {
  return `[${lang}] ${text}`;
};
module.exports = { translate };
""")

with open(os.path.join(beta_dir, "package.json"), "w") as f:
    json.dump({
        "name": "skill-beta",
        "version": "2.1.0",
        "description": "Translation helper"
    }, f, indent=2)

with open(os.path.join(beta_dir, "loader.js"), "w") as f:
    f.write("""// Dynamic loader
const fs = require('fs');
const load = (p) => fs.readFileSync(p);
module.exports = { load };
""")

# skill-gamma: Contains UNICODE_OVERRIDE and CONTROL_CHARS → HIGH risk
gamma_dir = os.path.join(skills_dir, "skill-gamma")
os.makedirs(gamma_dir, exist_ok=True)

# trojan.js: contains RLO unicode override (U+202E) — classic trojan filename trick
with open(os.path.join(gamma_dir, "trojan.js"), "wb") as f:
    normal_code = b"'use strict';\n// Looks like a config file\n"
    # embed Unicode RLO override (U+202E = \xe2\x80\xae in UTF-8)
    hidden = b"const exec = require('child_process').execSync;\n"
    rlo = b'\xe2\x80\xae'  # U+202E RIGHT-TO-LEFT OVERRIDE
    lro = b'\xe2\x80\xad'  # U+202D LEFT-TO-RIGHT OVERRIDE
    f.write(normal_code)
    f.write(b"// Config: " + rlo + b"gniftfarc" + lro + b"\n")
    f.write(hidden)
    # Also add control chars (0x01, 0x02)
    f.write(b"var x = 1;\x01\x02\n")
    f.write(b"module.exports = {};\n")

with open(os.path.join(gamma_dir, "index.js"), "w") as f:
    f.write("""'use strict';
const gamma = () => 'gamma skill active';
module.exports = { gamma };
""")

with open(os.path.join(gamma_dir, "package.json"), "w") as f:
    json.dump({
        "name": "skill-gamma",
        "version": "0.9.1",
        "description": "Experimental NLP module"
    }, f, indent=2)

with open(os.path.join(gamma_dir, "constants.js"), "w") as f:
    f.write("module.exports = { VERSION: '0.9.1', MAX_TOKENS: 512 };\n")

# skill-delta: Contains HIGH_NON_ASCII → MEDIUM risk
delta_dir = os.path.join(skills_dir, "skill-delta")
os.makedirs(delta_dir, exist_ok=True)

# data.bin: high ratio of non-ASCII bytes (looks like encoded/base64 payload)
with open(os.path.join(delta_dir, "data.bin"), "wb") as f:
    # Write lots of high-byte content (0x80-0xFF range)
    rng = random.Random(99)
    payload = bytes([rng.randint(0x80, 0xFF) for _ in range(512)])
    f.write(payload)

with open(os.path.join(delta_dir, "index.js"), "w") as f:
    f.write("""'use strict';
// skill-delta: Image processing helper (stub)
const process = (buf) => buf;
module.exports = { process };
""")

with open(os.path.join(delta_dir, "package.json"), "w") as f:
    json.dump({
        "name": "skill-delta",
        "version": "1.2.0",
        "description": "Binary processing utilities"
    }, f, indent=2)

with open(os.path.join(delta_dir, "helpers.js"), "w") as f:
    f.write("const noop = () => {};\nmodule.exports = { noop };\n")

# skill-epsilon: Nested, clean distractor files + one SUSPICIOUS_PATTERN file → MEDIUM or HIGH
epsilon_dir = os.path.join(skills_dir, "skill-epsilon")
epsilon_sub = os.path.join(epsilon_dir, "lib", "core")
os.makedirs(epsilon_sub, exist_ok=True)

with open(os.path.join(epsilon_dir, "index.js"), "w") as f:
    f.write("'use strict';\nmodule.exports = require('./lib/core/main');\n")

with open(os.path.join(epsilon_sub, "main.js"), "w") as f:
    f.write("""'use strict';
const run = () => console.log('epsilon running');
module.exports = { run };
""")

# suspicious.js: contains a known attack pattern string (e.g., common shell injection fragment)
with open(os.path.join(epsilon_sub, "suspicious.js"), "wb") as f:
    # embed SUSPICIOUS_PATTERN: common signatures like /bin/sh, exec, etc.
    f.write(b"'use strict';\n")
    # embed recognizable attack pattern bytes — null byte + exec call pattern
    f.write(b"// internal loader\nvar _cmd = '/bin/sh\x00-c';\n")
    f.write(b"module.exports = {};\n")

with open(os.path.join(epsilon_dir, "package.json"), "w") as f:
    json.dump({
        "name": "skill-epsilon",
        "version": "3.0.0",
        "description": "Core runtime module"
    }, f, indent=2)

with open(os.path.join(epsilon_sub, "constants.js"), "w") as f:
    f.write("module.exports = { PI: 3.14159 };\n")

with open(os.path.join(epsilon_sub, "types.js"), "w") as f:
    f.write("module.exports = {};\n")

# Additional distractor files at top level of incoming_skills
with open(os.path.join(skills_dir, "MARKETPLACE_QUEUE.txt"), "w") as f:
    f.write("Pending review:\n- skill-alpha\n- skill-beta\n- skill-gamma\n- skill-delta\n- skill-epsilon\n")

with open(os.path.join(skills_dir, "submission_metadata.json"), "w") as f:
    json.dump({
        "batch_id": "BATCH-2024-0042",
        "submitted_by": "third-party-vendors",
        "submitted_at": "2024-06-15T09:00:00Z",
        "count": 5
    }, f, indent=2)

print("Workspace inputs generated successfully.")
print(f"Created skill packages in: {skills_dir}")
print("Skills: skill-alpha (clean), skill-beta (ELF+nulls), skill-gamma (unicode override+ctrl), skill-delta (high non-ascii), skill-epsilon (suspicious pattern)")