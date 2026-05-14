#!/usr/bin/env python3
"""
Evaluation script for the SecretCodex triple-lock cipher challenge.
Independently re-computes all expected values and validates agent output.
"""

import sys
import json
import os
from pathlib import Path

def vigenere_encode(plaintext, keyword):
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
    n = len(ciphertext)
    if n == 0:
        return ''
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

def polybius_encode(text):
    pairs = []
    for ch in text.upper():
        if ch.isalpha():
            r, c = POLYBIUS_GRID[ch]
            pairs.append(f"{r}{c}")
    return ' '.join(pairs)

def polybius_decode(coords_str):
    tokens = coords_str.strip().split()
    result = []
    for token in tokens:
        key = int(token)
        if key not in POLYBIUS_REVERSE:
            raise ValueError(f"Unknown Polybius code: {token}")
        result.append(POLYBIUS_REVERSE[key])
    return ''.join(result)

def normalize_polybius(s):
    """Normalize a Polybius string: strip, collapse whitespace."""
    return ' '.join(s.strip().split())

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    checks = []
    score_parts = []

    # ── Compute expected values independently ──────────────────────────────
    KEYWORD = "PHANTOM"
    RAILS = 3
    DECODE_PLAINTEXT = "ESCAPETHROUGHTHESHADOWS"
    ENCODE_PLAINTEXT = "THEPHANTOMKNOWS"

    # Encoding pipeline for DECODE_PLAINTEXT (to reproduce the ciphertext)
    ref_v = vigenere_encode(DECODE_PLAINTEXT, KEYWORD)
    ref_r = rail_fence_encode(ref_v, RAILS)
    ref_ct = polybius_encode(ref_r)

    # Encoding pipeline for ENCODE_PLAINTEXT
    enc_v = vigenere_encode(ENCODE_PLAINTEXT, KEYWORD)
    enc_r = rail_fence_encode(enc_v, RAILS)
    EXPECTED_ENCODED = polybius_encode(enc_r)

    # ── Find agent output file ─────────────────────────────────────────────
    candidates = list(Path(workspace).rglob('decoded_solution.json'))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found decoded_solution.json at: {[str(c) for c in candidates]}" if file_found
                  else "No file named 'decoded_solution.json' found anywhere in workspace."
    })
    score_parts.append(0.1 if file_found else 0.0)

    if not file_found:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return

    # ── Parse JSON ─────────────────────────────────────────────────────────
    solution_path = candidates[0]
    parsed_ok = False
    data = {}
    try:
        with open(solution_path, 'r') as f:
            data = json.load(f)
        parsed_ok = True
    except Exception as e:
        checks.append({
            "name": "json_parseable",
            "passed": False,
            "detail": f"Could not parse JSON: {e}"
        })
        score_parts.append(0.0)
        print(json.dumps({"passed": False, "score": sum(score_parts)/5, "checks": checks}))
        return

    checks.append({
        "name": "json_parseable",
        "passed": True,
        "detail": "decoded_solution.json is valid JSON."
    })
    score_parts.append(0.1)

    # ── Check decoded_message ──────────────────────────────────────────────
    try:
        decoded_msg = str(data.get("decoded_message", "")).strip().upper()
        # Normalize: remove spaces (some agents may insert spaces)
        decoded_msg_clean = decoded_msg.replace(" ", "")
        expected_clean = DECODE_PLAINTEXT.upper().replace(" ", "")
        msg_correct = (decoded_msg_clean == expected_clean)
        checks.append({
            "name": "decoded_message_correct",
            "passed": msg_correct,
            "detail": (f"Got '{decoded_msg}', expected '{DECODE_PLAINTEXT}'. "
                       f"Decoding pipeline: Polybius⁻¹ → Rail Fence⁻¹({RAILS} rails) → Vigenère⁻¹(key={KEYWORD})")
        })
        score_parts.append(0.35 if msg_correct else 0.0)
    except Exception as e:
        checks.append({
            "name": "decoded_message_correct",
            "passed": False,
            "detail": f"Error checking decoded_message: {e}"
        })
        score_parts.append(0.0)

    # ── Check encoded_challenge ────────────────────────────────────────────
    try:
        encoded_challenge = str(data.get("encoded_challenge", "")).strip()
        enc_normalized = normalize_polybius(encoded_challenge)
        exp_normalized = normalize_polybius(EXPECTED_ENCODED)
        enc_correct = (enc_normalized == exp_normalized)

        # Also check intermediate steps to give partial credit info
        detail_parts = [
            f"Got: '{enc_normalized}'",
            f"Expected: '{exp_normalized}'",
            f"Pipeline: Vigenère({KEYWORD}) → Rail Fence({RAILS} rails) → Polybius",
            f"  Step1 Vigenère result: {enc_v}",
            f"  Step2 Rail Fence result: {enc_r}",
            f"  Step3 Polybius result: {EXPECTED_ENCODED}",
        ]
        checks.append({
            "name": "encoded_challenge_correct",
            "passed": enc_correct,
            "detail": " | ".join(detail_parts)
        })
        score_parts.append(0.35 if enc_correct else 0.0)
    except Exception as e:
        checks.append({
            "name": "encoded_challenge_correct",
            "passed": False,
            "detail": f"Error checking encoded_challenge: {e}"
        })
        score_parts.append(0.0)

    # ── Check cipher_layers field ──────────────────────────────────────────
    try:
        cipher_layers = data.get("cipher_layers", None)
        layers_ok = False
        layers_detail = ""

        if not isinstance(cipher_layers, list):
            layers_detail = f"cipher_layers must be a list, got: {type(cipher_layers).__name__}"
        elif len(cipher_layers) != 3:
            layers_detail = f"cipher_layers must have exactly 3 items, got {len(cipher_layers)}: {cipher_layers}"
        else:
            # Check that each layer description mentions the correct cipher names in order
            # Layer 0: Vigenère (innermost, applied first in encoding)
            # Layer 1: Rail Fence (middle)
            # Layer 2: Polybius (outermost, applied last in encoding)
            l0 = str(cipher_layers[0]).lower()
            l1 = str(cipher_layers[1]).lower()
            l2 = str(cipher_layers[2]).lower()

            vigenere_ok = any(kw in l0 for kw in ['vigenere', 'vigenère', 'keyword', 'phantom'])
            rail_ok = any(kw in l1 for kw in ['rail', 'fence', 'transposition', 'zigzag'])
            polybius_ok = any(kw in l2 for kw in ['polybius', 'square', 'grid', 'coordinate'])

            layers_ok = vigenere_ok and rail_ok and polybius_ok
            layers_detail = (
                f"Layer[0] (Vigenère): {'✓' if vigenere_ok else '✗'} '{cipher_layers[0]}' | "
                f"Layer[1] (Rail Fence): {'✓' if rail_ok else '✗'} '{cipher_layers[1]}' | "
                f"Layer[2] (Polybius): {'✓' if polybius_ok else '✗'} '{cipher_layers[2]}'"
            )

        checks.append({
            "name": "cipher_layers_correct_order",
            "passed": layers_ok,
            "detail": layers_detail
        })
        score_parts.append(0.10 if layers_ok else 0.0)
    except Exception as e:
        checks.append({
            "name": "cipher_layers_correct_order",
            "passed": False,
            "detail": f"Error checking cipher_layers: {e}"
        })
        score_parts.append(0.0)

    # ── Final score ────────────────────────────────────────────────────────
    total_score = sum(score_parts)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()