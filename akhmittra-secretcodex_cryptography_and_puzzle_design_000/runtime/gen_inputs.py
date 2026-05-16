#!/usr/bin/env python3
"""
Generate the sandbox workspace for the SecretCodex cipher challenge.
All cryptographic values are computed deterministically from scratch.
"""

import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ─────────────────────────────────────────────
# Pure-Python cipher implementations (reference)
# ─────────────────────────────────────────────

POLYBIUS_GRID = {
    'A': (1,1), 'B': (1,2), 'C': (1,3), 'D': (1,4), 'E': (1,5),
    'F': (2,1), 'G': (2,2), 'H': (2,3), 'I': (2,4), 'J': (2,4),
    'K': (2,5), 'L': (3,1), 'M': (3,2), 'N': (3,3), 'O': (3,4),
    'P': (3,5), 'Q': (4,1), 'R': (4,2), 'S': (4,3), 'T': (4,4),
    'U': (4,5), 'V': (5,1), 'W': (5,2), 'X': (5,3), 'Y': (5,4),
    'Z': (5,5)
}

POLYBIUS_REVERSE = {}
for letter, (r, c) in POLYBIUS_GRID.items():
    key = r * 10 + c
    if key not in POLYBIUS_REVERSE:
        POLYBIUS_REVERSE[key] = letter

def vigenere_encode(plaintext, keyword):
    """Encode using Vigenère cipher. Only processes A-Z."""
    keyword = keyword.upper()
    result = []
    ki = 0
    for ch in plaintext.upper():
        if ch.isalpha():
            shift = ord(keyword[ki % len(keyword)]) - ord('A')
            enc = chr((ord(ch) - ord('A') + shift) % 26 + ord('A'))
            result.append(enc)
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)

def vigenere_decode(ciphertext, keyword):
    """Decode using Vigenère cipher. Only processes A-Z."""
    keyword = keyword.upper()
    result = []
    ki = 0
    for ch in ciphertext.upper():
        if ch.isalpha():
            shift = ord(keyword[ki % len(keyword)]) - ord('A')
            dec = chr((ord(ch) - ord('A') - shift) % 26 + ord('A'))
            result.append(dec)
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)

def rail_fence_encode(text, rails):
    """Encode using Rail Fence cipher."""
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1
    for ch in text:
        fence[rail].append(ch)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    return ''.join(''.join(r) for r in fence)

def rail_fence_decode(ciphertext, rails):
    """Decode using Rail Fence cipher."""
    n = len(ciphertext)
    pattern = []
    rail = 0
    direction = 1
    for i in range(n):
        pattern.append(rail)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction

    indices = list(range(n))
    sorted_indices = sorted(indices, key=lambda i: (pattern[i], i))
    result = [''] * n
    for pos, idx in enumerate(sorted_indices):
        result[idx] = ciphertext[pos]
    return ''.join(result)

def polybius_encode(text):
    """Encode text to Polybius coordinate pairs (space-separated)."""
    pairs = []
    for ch in text.upper():
        if ch.isalpha():
            r, c = POLYBIUS_GRID[ch]
            pairs.append(f"{r}{c}")
    return ' '.join(pairs)

def polybius_decode(coords_str):
    """Decode Polybius coordinate pairs back to text."""
    tokens = coords_str.strip().split()
    result = []
    for token in tokens:
        key = int(token)
        result.append(POLYBIUS_REVERSE[key])
    return ''.join(result)

# ─────────────────────────────────────────────
# Pipeline: Vigenère → Rail Fence → Polybius
# ─────────────────────────────────────────────

KEYWORD = "PHANTOM"
RAILS = 3

# Message to be DECODED by the agent
DECODE_PLAINTEXT = "ESCAPETHROUGHTHESHADOWS"
step1 = vigenere_encode(DECODE_PLAINTEXT, KEYWORD)
step2 = rail_fence_encode(step1, RAILS)
ENCODED_CHALLENGE = polybius_encode(step2)

# Message to be ENCODED by the agent
ENCODE_PLAINTEXT = "THEPHANTOMKNOWS"
enc_step1 = vigenere_encode(ENCODE_PLAINTEXT, KEYWORD)
enc_step2 = rail_fence_encode(enc_step1, RAILS)
EXPECTED_ENCODED_OUTPUT = polybius_encode(enc_step2)

# Sanity checks
assert polybius_decode(ENCODED_CHALLENGE) == step2
assert rail_fence_decode(polybius_decode(ENCODED_CHALLENGE), RAILS) == step1
assert vigenere_decode(rail_fence_decode(polybius_decode(ENCODED_CHALLENGE), RAILS), KEYWORD) == DECODE_PLAINTEXT

print(f"[GEN] DECODE_PLAINTEXT    : {DECODE_PLAINTEXT}")
print(f"[GEN] Vigenère step1      : {step1}")
print(f"[GEN] Rail Fence step2    : {step2}")
print(f"[GEN] Polybius (final CT) : {ENCODED_CHALLENGE}")
print(f"[GEN] ENCODE_PLAINTEXT    : {ENCODE_PLAINTEXT}")
print(f"[GEN] Encoded output      : {EXPECTED_ENCODED_OUTPUT}")

# ─────────────────────────────────────────────
# Create workspace directory structure
# ─────────────────────────────────────────────

dirs = [
    "operations/active",
    "operations/archive",
    "operations/archive/q1",
    "operations/archive/q2",
    "team/agents",
    "team/logistics",
    "team/communications/drafts",
    "team/communications/sent",
    "puzzles/escape_rooms/series_a",
    "puzzles/escape_rooms/series_b",
    "puzzles/training",
    "keys/retired",
    "keys/active",
    "docs/internal",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ─────────────────────────────────────────────
# Distractor files (realistic but misleading)
# ─────────────────────────────────────────────

# 1. Old mission brief (wrong message, wrong format)
with open(os.path.join(WORKSPACE, "operations/archive/q1/mission_brief_v1.txt"), "w") as f:
    f.write("""OPERATION SILVER DAWN - Q1 BRIEF
================================
Status: ARCHIVED
Agent: Phoenix
Note: This brief uses outdated encoding. Replaced by new triple-lock system.
Old ciphertext: XLMW MW XLI SYX HEXIH QIWWEKI
""")

# 2. A fake key file with plausible-looking but wrong keyword
with open(os.path.join(WORKSPACE, "keys/retired/keyword_v1.txt"), "w") as f:
    f.write("""RETIRED KEY - DO NOT USE
========================
Keyword: SPECTER
Retired: 2024-01-15
Reason: Compromised during Operation Bronze Dusk
""")

# 3. A partial cipher reference (incomplete, misleading)
with open(os.path.join(WORKSPACE, "docs/internal/cipher_notes_draft.txt"), "w") as f:
    f.write("""DRAFT CIPHER NOTES - INCOMPLETE
================================
Caesar: shift n positions
ROT13: shift 13
Vigenère: keyword based - see full spec for details
Polybius: grid coords - WARNING: old notes used I≠J, new spec differs
Rail Fence: zigzag pattern - number of rails varies by operation

NOTE: These notes are outdated. Refer to SecretCodex documentation
for authoritative encoding procedures. This document should be
DELETED after review.
""")

# 4. Fake decoded message (wrong answer)
with open(os.path.join(WORKSPACE, "operations/archive/q2/decoded_attempt.txt"), "w") as f:
    f.write("""FAILED DECODE ATTEMPT - 2024-02-10
===================================
Tried: Caesar shift 7 on ciphertext
Result: XHVDBSQFKXLJQCFKXPZDLTPH
Status: WRONG - not readable
""")

# 5. Team roster with code names
with open(os.path.join(WORKSPACE, "team/agents/roster.txt"), "w") as f:
    f.write("""ACTIVE AGENTS - CODE NAME ROSTER
=================================
Phoenix    - Team Lead
Atlas      - Field Operations
Cipher     - Cryptography Specialist
Raven      - Intelligence
Echo       - Communications

Location Codes:
  Raven's Point  = North Library Entrance
  Glacier Station = Server Room B
  Meridian Hub    = Operations Center
""")

# 6. A wrong Polybius grid reference (trap: this uses I≠J which is WRONG per SKILL.md)
with open(os.path.join(WORKSPACE, "docs/internal/polybius_old_grid.txt"), "w") as f:
    f.write("""OLD POLYBIUS GRID (pre-2023, I≠J variant):
  1 2 3 4 5
1 A B C D E
2 F G H I J
3 L M N O P
4 Q R S T U
5 V W X Y Z

WARNING: This 6x5 grid is DEPRECATED. Current standard uses
5x5 with I/J combined. Do not use this for new encodings.
""")

# 7. Training puzzle with different rail count (distractor)
with open(os.path.join(WORKSPACE, "puzzles/training/beginner_rail_fence.txt"), "w") as f:
    f.write("""TRAINING PUZZLE - RAIL FENCE
============================
Practice puzzle using 4 rails (training only):
Plaintext:  PRACTICERUN
Ciphertext: PCIORATCEUN
Note: Production missions use 3 rails, not 4.
""")

# 8. Fake active key file with wrong keyword
with open(os.path.join(WORKSPACE, "keys/active/current_session.txt"), "w") as f:
    f.write("""CURRENT SESSION KEY PARAMETERS
================================
Session: 2024-Q3
Method: Triple-lock protocol
See: Active mission brief for full parameters.
""")

# 9. Log file with noise
with open(os.path.join(WORKSPACE, "logs/comms_log.txt"), "w") as f:
    f.write("""2024-03-01 09:14 - Phoenix sent encoded msg to Atlas
2024-03-01 09:22 - Atlas acknowledged receipt
2024-03-02 14:00 - Cipher performed routine key rotation
2024-03-03 08:30 - ALERT: Unrecognized decode attempt on archived Q1 msg
2024-03-05 11:45 - New mission brief issued for Operation Shadow Veil
""")

# 10. Series B puzzle (different cipher, not relevant)
with open(os.path.join(WORKSPACE, "puzzles/escape_rooms/series_b/room3_clue.txt"), "w") as f:
    f.write("""ESCAPE ROOM SERIES B - ROOM 3 CLUE
====================================
Cipher: Atbash
Ciphertext: OLLP FMWVI GSV GZYOV
Hint: Simple reversal cipher
""")

# 11. Draft communications
with open(os.path.join(WORKSPACE, "team/communications/drafts/msg_draft.txt"), "w") as f:
    f.write("""DRAFT - NOT SENT
To: Atlas
From: Phoenix
Subject: Meeting coordination

Need to transmit new coordinates using the triple-lock protocol.
Standing by for confirmation that shared key materials have been received.
""")

# 12. Active mission brief - THE KEY DOCUMENT the agent must work with
mission_brief = f"""OPERATION SHADOW VEIL - ACTIVE MISSION BRIEF
============================================
Classification: RESTRICTED
Issued by: Cipher (Cryptography Specialist)
Date: 2024-03-05

INTERCEPT ANALYSIS TASK
-----------------------
Our intelligence team has intercepted the following encoded transmission.
The transmission was encrypted using the standard triple-lock protocol:
  Layer 1 (innermost): Vigenère cipher, keyword: {KEYWORD}
  Layer 2 (middle):    Rail Fence transposition, rails: {RAILS}
  Layer 3 (outermost): Polybius Square coordinate encoding (I/J combined, standard 5x5)

INTERCEPTED CIPHERTEXT:
{ENCODED_CHALLENGE}

YOUR TASKS:
1. Decode the intercepted ciphertext above and recover the original plaintext.

2. Encode the following new message for secure transmission using the SAME
   triple-lock protocol (same keyword, same rail count, same Polybius grid):
   
   Plaintext to encode: {ENCODE_PLAINTEXT}

3. Save your results to a file named: decoded_solution.json
   The file must contain the following fields:
     - "decoded_message"   : the recovered plaintext from decoding
     - "encoded_challenge" : the Polybius-encoded ciphertext for the new message
     - "cipher_layers"     : a list of exactly 3 strings describing each layer used,
                             in the ORDER they were applied during ENCODING
                             (innermost first, outermost last)

NOTES:
- The triple-lock protocol always applies layers in the order: Vigenère → Rail Fence → Polybius
- Decoding reverses this: Polybius⁻¹ → Rail Fence⁻¹ → Vigenère⁻¹
- All Polybius coordinates are two-digit numbers (row then column), space-separated
- The Polybius grid treats I and J as the same cell (row 2, col 4)
"""

with open(os.path.join(WORKSPACE, "puzzles/escape_rooms/series_a/mission_brief.txt"), "w") as f:
    f.write(mission_brief)

# Save expected values for eval script reference (hidden from agent via naming)
expected = {
    "decode_plaintext": DECODE_PLAINTEXT,
    "encode_plaintext": ENCODE_PLAINTEXT,
    "vigenere_step": step1,
    "rail_fence_step": step2,
    "encoded_ciphertext": ENCODED_CHALLENGE,
    "expected_encoded_output": EXPECTED_ENCODED_OUTPUT,
    "keyword": KEYWORD,
    "rails": RAILS
}
with open(os.path.join(WORKSPACE, ".eval_reference.json"), "w") as f:
    json.dump(expected, f, indent=2)

print("\n[GEN] Workspace created successfully.")
print(f"[GEN] Mission brief written to: puzzles/escape_rooms/series_a/mission_brief.txt")
print(f"[GEN] Expected decoded message: {DECODE_PLAINTEXT}")
print(f"[GEN] Expected encoded output:  {EXPECTED_ENCODED_OUTPUT}")