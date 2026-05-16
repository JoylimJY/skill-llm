import sys
import os
import subprocess
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    score = 0.0

    workspace = Path(workspace)

    # -----------------------------------------------------------------------
    # CHECK 1: gateway_main.c exists somewhere in the workspace
    # -----------------------------------------------------------------------
    found_files = list(workspace.rglob("gateway_main.c"))
    c1_passed = len(found_files) > 0
    checks.append({
        "name": "gateway_main.c exists",
        "passed": c1_passed,
        "detail": f"Found at: {found_files[0]}" if c1_passed else "File gateway_main.c not found in workspace."
    })

    if not c1_passed:
        return {"passed": False, "score": 0.0, "checks": checks}

    gateway_main_path = found_files[0]

    # -----------------------------------------------------------------------
    # CHECK 2: gateway_main.c includes "code.c" (not a header, the .c file)
    # -----------------------------------------------------------------------
    try:
        src = gateway_main_path.read_text()
        c2_passed = '#include "code.c"' in src
        checks.append({
            "name": "includes code.c correctly",
            "passed": c2_passed,
            "detail": '#include "code.c" found in source.' if c2_passed else 'Missing #include "code.c" — agent may have used a .h file or wrong include.'
        })
    except Exception as e:
        checks.append({"name": "includes code.c correctly", "passed": False, "detail": str(e)})
        c2_passed = False

    # -----------------------------------------------------------------------
    # CHECK 3: gateway_main.c uses config_load_file (loads config/gateway.cfg)
    # -----------------------------------------------------------------------
    try:
        src = gateway_main_path.read_text()
        c3_passed = "config_load_file" in src
        checks.append({
            "name": "uses config_load_file",
            "passed": c3_passed,
            "detail": "config_load_file found in source." if c3_passed else "config_load_file not used — agent did not implement file-based config loading."
        })
    except Exception as e:
        checks.append({"name": "uses config_load_file", "passed": False, "detail": str(e)})
        c3_passed = False

    # -----------------------------------------------------------------------
    # CHECK 4: gateway_main.c uses config_get_* with default fallbacks
    # -----------------------------------------------------------------------
    try:
        src = gateway_main_path.read_text()
        uses_get_string = "config_get_string" in src
        uses_get_int = "config_get_int" in src
        uses_get_bool = "config_get_bool" in src or "config_get_int" in src  # bool may use int getter
        c4_passed = uses_get_string and uses_get_int
        checks.append({
            "name": "uses config_get_string and config_get_int",
            "passed": c4_passed,
            "detail": f"get_string={uses_get_string}, get_int={uses_get_int}" 
        })
    except Exception as e:
        checks.append({"name": "uses config_get_string and config_get_int", "passed": False, "detail": str(e)})
        c4_passed = False

    # -----------------------------------------------------------------------
    # CHECK 5: Compiles successfully WITHOUT -DCONFIG_DEMO flag
    # -----------------------------------------------------------------------
    binary_path = "/tmp/gateway_eval_bin"
    compile_cmd = ["gcc", "-o", binary_path, str(gateway_main_path)]
    try:
        result = subprocess.run(
            compile_cmd,
            capture_output=True, text=True, timeout=30,
            cwd=str(workspace)
        )
        c5_passed = result.returncode == 0
        checks.append({
            "name": "compiles without -DCONFIG_DEMO",
            "passed": c5_passed,
            "detail": "Compiled successfully." if c5_passed else f"Compile error:\n{result.stderr[:600]}"
        })
    except Exception as e:
        checks.append({"name": "compiles without -DCONFIG_DEMO", "passed": False, "detail": str(e)})
        c5_passed = False

    # -----------------------------------------------------------------------
    # CHECK 6: Binary runs and prints correct values loaded from config file
    # -----------------------------------------------------------------------
    c6_passed = False
    output_text = ""
    if c5_passed:
        try:
            run_result = subprocess.run(
                [binary_path],
                capture_output=True, text=True, timeout=10,
                cwd=str(workspace)
            )
            output_text = run_result.stdout.strip()
            # Expected from config/gateway.cfg:
            #   mqtt.broker=10.42.0.1
            #   mqtt.port=8883
            #   mqtt.tls=true
            #   device.id=GW-PROD-042
            # Missing (must use defaults):
            #   poll.interval => default 60
            #   retry.max => default 3
            has_broker = "10.42.0.1" in output_text
            has_port   = "8883" in output_text
            has_tls    = ("true" in output_text.lower() or "1" in output_text)
            has_device = "GW-PROD-042" in output_text
            has_default_poll = "60" in output_text
            has_default_retry = "3" in output_text
            c6_passed = has_broker and has_port and has_device
            checks.append({
                "name": "output contains values from config file",
                "passed": c6_passed,
                "detail": (
                    f"Output: {output_text[:400]}\n"
                    f"broker(10.42.0.1)={has_broker}, port(8883)={has_port}, "
                    f"tls(true/1)={has_tls}, device(GW-PROD-042)={has_device}"
                )
            })
        except Exception as e:
            checks.append({"name": "output contains values from config file", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "output contains values from config file", "passed": False, "detail": "Skipped — binary did not compile."})

    # -----------------------------------------------------------------------
    # CHECK 7: Default fallbacks are printed for missing keys
    # -----------------------------------------------------------------------
    c7_passed = False
    if c5_passed and output_text:
        try:
            has_default_poll  = "60" in output_text
            has_default_retry = "3" in output_text
            # At least one default must appear (poll.interval=60 or retry.max=3)
            c7_passed = has_default_poll or has_default_retry
            checks.append({
                "name": "default fallback values used for missing keys",
                "passed": c7_passed,
                "detail": f"poll_default(60)={has_default_poll}, retry_default(3)={has_default_retry}. Output: {output_text[:300]}"
            })
        except Exception as e:
            checks.append({"name": "default fallback values used for missing keys", "passed": False, "detail": str(e)})
    else:
        checks.append({"name": "default fallback values used for missing keys", "passed": False, "detail": "Skipped — binary did not run or produced no output."})

    # -----------------------------------------------------------------------
    # CHECK 8: config_destroy is called (no memory leak, good API practice)
    # -----------------------------------------------------------------------
    try:
        src = gateway_main_path.read_text()
        c8_passed = "config_destroy" in src
        checks.append({
            "name": "config_destroy called",
            "passed": c8_passed,
            "detail": "config_destroy found." if c8_passed else "config_destroy not called — resource leak detected."
        })
    except Exception as e:
        checks.append({"name": "config_destroy called", "passed": False, "detail": str(e)})
        c8_passed = False

    # -----------------------------------------------------------------------
    # Score computation
    # -----------------------------------------------------------------------
    weights = {
        "gateway_main.c exists": 0.10,
        "includes code.c correctly": 0.15,
        "uses config_load_file": 0.15,
        "uses config_get_string and config_get_int": 0.10,
        "compiles without -DCONFIG_DEMO": 0.15,
        "output contains values from config file": 0.20,
        "default fallback values used for missing keys": 0.10,
        "config_destroy called": 0.05,
    }
    total = 0.0
    for chk in checks:
        w = weights.get(chk["name"], 0.0)
        if chk["passed"]:
            total += w
    score = round(total, 4)

    # overall pass: must compile, run with correct output, and use file loading
    overall = (
        c1_passed and c2_passed and c3_passed and
        c5_passed and c6_passed
    )

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))