#!/bin/bash
set -e

# Create the mock bracketsbot CLI
cat > /usr/local/bin/bracketsbot << 'BRACKETSBOT_EOF'
#!/usr/bin/env python3
"""
Mock bracketsbot CLI for testing.
Implements: walk-run-policy, validate, share-link, walk-next, walk-apply, semantic-run, prepare-submit-tx
"""
import sys
import json
import os
import hashlib
import re

WORKSPACE = os.environ.get("BRACKETSBOT_WORKSPACE", os.getcwd())
OUT_DIR = os.path.join(WORKSPACE, "out")
WALK_PICKS_FILE = os.path.join(OUT_DIR, "model-walk-picks.json")
BRACKET_OUTPUT_FILE = os.path.join(OUT_DIR, "model-bracket-output.json")

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)

def error_json(msg, code=1):
    print(json.dumps({"error": msg, "success": False}))
    sys.exit(code)

def generate_deterministic_bracket():
    """Generate 63 picks deterministically. Seeds 1..64. Higher seed (lower number) usually wins."""
    picks = []
    
    round1_matchups = []
    for region_start in [1, 17, 33, 49]:
        pairs = [(region_start, region_start+15), (region_start+1, region_start+14),
                 (region_start+2, region_start+13), (region_start+3, region_start+12),
                 (region_start+4, region_start+11), (region_start+5, region_start+10),
                 (region_start+6, region_start+9), (region_start+7, region_start+8)]
        round1_matchups.extend(pairs)
    
    upsets_r1 = {(5, 12): 12, (6, 11): 11, (7, 10): 10,
                  (21, 28): 28, (38, 43): 43, (53, 60): 60}
    
    r1_winners = []
    for (a, b) in round1_matchups:
        key = (min(a,b), max(a,b))
        if key in upsets_r1:
            winner = upsets_r1[key]
        else:
            winner = a if a < b else b
        picks.append(winner)
        r1_winners.append(winner)
    
    r2_winners = []
    for i in range(0, 32, 2):
        a, b = r1_winners[i], r1_winners[i+1]
        winner = a if a < b else b
        picks.append(winner)
        r2_winners.append(winner)
    
    r3_winners = []
    for i in range(0, 16, 2):
        a, b = r2_winners[i], r2_winners[i+1]
        winner = a if a < b else b
        picks.append(winner)
        r3_winners.append(winner)
    
    r4_winners = []
    for i in range(0, 8, 2):
        a, b = r3_winners[i], r3_winners[i+1]
        winner = a if a < b else b
        picks.append(winner)
        r4_winners.append(winner)
    
    r5_winners = []
    for i in range(0, 4, 2):
        a, b = r4_winners[i], r4_winners[i+1]
        winner = a if a < b else b
        picks.append(winner)
        r5_winners.append(winner)
    
    champion = r5_winners[0] if r5_winners[0] < r5_winners[1] else r5_winners[1]
    picks.append(champion)
    
    return picks

def cmd_walk_run_policy(args):
    """Runs a policy module over the full bracket."""
    ensure_out_dir()
    
    policy_module = None
    use_json = False
    i = 0
    while i < len(args):
        if args[i] == "--policy-module" and i+1 < len(args):
            policy_module = args[i+1]
            i += 2
        elif args[i] == "--json":
            use_json = True
            i += 1
        else:
            i += 1
    
    if not policy_module:
        if use_json:
            error_json("--policy-module is required for walk-run-policy")
        else:
            print("Error: --policy-module is required")
            sys.exit(1)
    
    if not os.path.exists(policy_module):
        if use_json:
            error_json(f"Policy module not found: {policy_module}")
        else:
            print(f"Error: Policy module not found: {policy_module}")
            sys.exit(1)
    
    with open(policy_module, "r") as f:
        module_content = f.read()
    
    has_choose_winner = ("chooseWinner" in module_content)
    if not has_choose_winner:
        if use_json:
            error_json("Policy module must export 'chooseWinner' function. Found no such export.")
        else:
            print("Error: Policy module must export 'chooseWinner' function.")
            sys.exit(1)
    
    picks = generate_deterministic_bracket()
    
    output = {
        "predictions": picks,
        "totalPicks": len(picks),
        "policyModule": policy_module,
        "success": True,
        "complete": True
    }
    
    with open(BRACKET_OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    result = {
        "success": True,
        "complete": True,
        "outputFile": BRACKET_OUTPUT_FILE,
        "totalPicks": len(picks),
        "message": f"Policy module executed successfully. {len(picks)} picks generated.",
        "predictions": picks
    }
    
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Bracket complete. {len(picks)} picks written to {BRACKET_OUTPUT_FILE}")

def cmd_validate(args):
    """Validates the bracket predictions."""
    use_json = "--json" in args
    predictions_file = None
    
    i = 0
    while i < len(args):
        if args[i] == "--predictions-file" and i+1 < len(args):
            predictions_file = args[i+1]
            i += 2
        else:
            i += 1
    
    if not predictions_file:
        if os.path.exists(BRACKET_OUTPUT_FILE):
            predictions_file = BRACKET_OUTPUT_FILE
        elif os.path.exists(WALK_PICKS_FILE):
            predictions_file = WALK_PICKS_FILE
        else:
            if use_json:
                error_json("No predictions file found. Run walk-run-policy or semantic-run first.")
            else:
                print("Error: No predictions file found.")
                sys.exit(1)
    
    if not os.path.exists(predictions_file):
        if use_json:
            error_json(f"Predictions file not found: {predictions_file}")
        else:
            print(f"Error: Predictions file not found: {predictions_file}")
            sys.exit(1)
    
    try:
        with open(predictions_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        if use_json:
            error_json(f"Invalid JSON in predictions file: {e}")
        else:
            print(f"Error: Invalid JSON: {e}")
            sys.exit(1)
    
    picks = data.get("predictions", [])
    
    errors = []
    
    if len(picks) != 63:
        errors.append(f"Expected 63 picks, got {len(picks)}")
    
    for i, pick in enumerate(picks):
        if not isinstance(pick, int) or pick < 1 or pick > 64:
            errors.append(f"Pick {i} is invalid: {pick} (must be seed 1..64)")
    
    if errors:
        result = {
            "valid": False,
            "success": False,
            "errors": errors,
            "totalPicks": len(picks)
        }
    else:
        result = {
            "valid": True,
            "success": True,
            "errors": [],
            "totalPicks": len(picks),
            "message": "Bracket is valid. 63 picks verified, all seeds in range 1..64."
        }
    
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print("Bracket is valid.")
        else:
            print("Bracket validation failed:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)

def cmd_share_link(args):
    """Generates a share link for the bracket."""
    use_json = "--json" in args
    predictions_file = None
    
    i = 0
    while i < len(args):
        if args[i] == "--predictions-file" and i+1 < len(args):
            predictions_file = args[i+1]
            i += 2
        else:
            i += 1
    
    if not predictions_file:
        predictions_file = WALK_PICKS_FILE
    
    if not os.path.exists(predictions_file):
        if use_json:
            error_json(f"Predictions file not found: {predictions_file}. For Coded/Instructed workflows, use --predictions-file ./out/model-bracket-output.json")
        else:
            print(f"Error: Predictions file not found: {predictions_file}")
            sys.exit(1)
    
    try:
        with open(predictions_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        if use_json:
            error_json(f"Invalid predictions file: {e}")
        else:
            print(f"Error: {e}")
            sys.exit(1)
    
    picks = data.get("predictions", [])
    
    picks_hash = hashlib.md5(json.dumps(picks).encode()).hexdigest()[:12]
    share_url = f"https://bracketsbot.xyz/bracket?picks={picks_hash}&src=agent"
    
    result = {
        "success": True,
        "shareUrl": share_url,
        "picksCount": len(picks),
        "message": "Share URL generated. Open in browser to review and submit with your browser wallet."
    }
    
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Share URL: {share_url}")

def cmd_walk_next(args):
    """Returns the next game to pick."""
    use_json = "--json" in args
    result = {
        "gameId": 1,
        "round": 1,
        "teamA": {"seed": 1, "name": "Houston"},
        "teamB": {"seed": 16, "name": "Wagner"},
        "done": False
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Game 1: Houston (1) vs Wagner (16)")

def cmd_walk_apply(args):
    """Applies a winner pick."""
    use_json = "--json" in args
    winner_seed = None
    i = 0
    while i < len(args):
        if args[i] == "--winner-seed" and i+1 < len(args):
            winner_seed = int(args[i+1])
            i += 2
        else:
            i += 1
    result = {
        "success": True,
        "appliedSeed": winner_seed,
        "gamesRemaining": 62
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Applied winner seed: {winner_seed}")

def cmd_semantic_run(args):
    """Runs semantic policy over all games."""
    ensure_out_dir()
    use_json = "--json" in args
    picks = generate_deterministic_bracket()
    output = {
        "predictions": picks,
        "totalPicks": len(picks),
        "success": True,
        "complete": True
    }
    with open(BRACKET_OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    result = {
        "success": True,
        "complete": True,
        "outputFile": BRACKET_OUTPUT_FILE,
        "totalPicks": len(picks),
        "predictions": picks
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Semantic run complete. {len(picks)} picks.")

def cmd_prepare_submit_tx(args):
    """Prepares a transaction payload."""
    use_json = "--json" in args
    result = {
        "success": True,
        "tx": {
            "to": "0xBracketsBot1234567890abcdef",
            "data": "0xdeadbeef",
            "value": "0"
        }
    }
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print("Transaction prepared.")

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: bracketsbot <command> [options]")
        sys.exit(1)
    
    command = args[0]
    rest = args[1:]
    
    dispatch = {
        "walk-run-policy": cmd_walk_run_policy,
        "validate": cmd_validate,
        "share-link": cmd_share_link,
        "walk-next": cmd_walk_next,
        "walk-apply": cmd_walk_apply,
        "semantic-run": cmd_semantic_run,
        "prepare-submit-tx": cmd_prepare_submit_tx,
    }
    
    if command not in dispatch:
        print(json.dumps({"error": f"Unknown command: {command}", "available": list(dispatch.keys())}))
        sys.exit(1)
    
    dispatch[command](rest)

if __name__ == "__main__":
    main()
BRACKETSBOT_EOF

chmod +x /usr/local/bin/bracketsbot

# Verify it works
bracketsbot validate --json 2>/dev/null || true

echo "bracketsbot CLI mock installed successfully."
echo "Available commands: walk-run-policy, validate, share-link, walk-next, walk-apply, semantic-run, prepare-submit-tx"