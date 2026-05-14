import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []
total_score = 0.0

def find_file(name):
    """Find a file by exact name anywhere in workspace."""
    results = list(Path(workspace).rglob(name))
    return results[0] if results else None

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return weight if condition else 0.0

# ============================================================
# CHECK GROUP 1: docker-compose.yml validation
# ============================================================
try:
    import yaml
    compose_path = find_file("docker-compose.yml")
    if compose_path is None:
        total_score += check("compose_file_exists", False, "docker-compose.yml not found anywhere in workspace", 2.0)
        compose = None
    else:
        with open(compose_path) as f:
            compose = yaml.safe_load(f)
        total_score += check("compose_file_exists", True, f"Found docker-compose.yml at {compose_path}", 2.0)
except Exception as e:
    compose = None
    total_score += check("compose_file_exists", False, f"Error loading docker-compose.yml: {e}", 2.0)

if compose:
    services = compose.get("services", {})

    # --- GRASS checks ---
    try:
        grass = services.get("grass", {})
        grass_image = grass.get("image", "")
        total_score += check(
            "grass_image_correct",
            grass_image == "mrcolorrain/grass:latest",
            f"Grass image: '{grass_image}' (expected 'mrcolorrain/grass:latest')",
            1.5
        )
        # Env vars: must use GRASS_USER and GRASS_PASS (not GRASS_EMAIL or GRASS_USERNAME)
        grass_env = grass.get("environment", [])
        if isinstance(grass_env, list):
            env_keys = [e.split("=")[0] for e in grass_env if "=" in e]
        elif isinstance(grass_env, dict):
            env_keys = list(grass_env.keys())
        else:
            env_keys = []
        total_score += check(
            "grass_env_GRASS_USER",
            "GRASS_USER" in env_keys,
            f"Grass env keys: {env_keys} — must contain GRASS_USER (not GRASS_EMAIL)",
            1.5
        )
        total_score += check(
            "grass_env_GRASS_PASS",
            "GRASS_PASS" in env_keys,
            f"Grass env keys: {env_keys} — must contain GRASS_PASS (not GRASS_PASSWORD)",
            1.5
        )
        grass_name = grass.get("container_name", "")
        total_score += check(
            "grass_container_name",
            grass_name == "grass-node",
            f"Grass container_name: '{grass_name}' (expected 'grass-node')",
            1.0
        )
    except Exception as e:
        total_score += check("grass_checks", False, f"Exception checking grass service: {e}", 5.5)

    # --- MYSTERIUM checks ---
    try:
        myst = services.get("mysterium", {})
        myst_image = myst.get("image", "")
        total_score += check(
            "mysterium_image_correct",
            myst_image == "mysteriumnetwork/myst:latest",
            f"Mysterium image: '{myst_image}' (expected 'mysteriumnetwork/myst:latest')",
            1.5
        )
        # cap_add must include NET_ADMIN
        cap_add = myst.get("cap_add", [])
        total_score += check(
            "mysterium_cap_add_NET_ADMIN",
            "NET_ADMIN" in cap_add,
            f"Mysterium cap_add: {cap_add} — must contain NET_ADMIN",
            2.0
        )
        # command must contain --agreed-terms-and-conditions
        myst_cmd = myst.get("command", "")
        cmd_str = " ".join(myst_cmd) if isinstance(myst_cmd, list) else str(myst_cmd)
        total_score += check(
            "mysterium_command_agreed_terms",
            "--agreed-terms-and-conditions" in cmd_str,
            f"Mysterium command: '{cmd_str}' — must contain '--agreed-terms-and-conditions'",
            2.0
        )
        # port 4449
        myst_ports = myst.get("ports", [])
        ports_str = " ".join(str(p) for p in myst_ports)
        total_score += check(
            "mysterium_port_4449",
            "4449" in ports_str,
            f"Mysterium ports: {myst_ports} — must include 4449:4449",
            1.0
        )
        # volume /root/.mysterium
        myst_vols = myst.get("volumes", [])
        vols_str = " ".join(str(v) for v in myst_vols)
        total_score += check(
            "mysterium_volume_path",
            "/root/.mysterium" in vols_str,
            f"Mysterium volumes: {myst_vols} — must mount to /root/.mysterium",
            1.5
        )
        myst_name = myst.get("container_name", "")
        total_score += check(
            "mysterium_container_name",
            myst_name == "mysterium-node",
            f"Mysterium container_name: '{myst_name}' (expected 'mysterium-node')",
            1.0
        )
    except Exception as e:
        total_score += check("mysterium_checks", False, f"Exception checking mysterium service: {e}", 9.0)

    # --- HONEYGAIN checks ---
    try:
        hg = services.get("honeygain", {})
        hg_image = hg.get("image", "")
        total_score += check(
            "honeygain_image_correct",
            hg_image == "honeygain/honeygain:latest",
            f"Honeygain image: '{hg_image}' (expected 'honeygain/honeygain:latest')",
            1.5
        )
        hg_env = hg.get("environment", [])
        if isinstance(hg_env, list):
            hg_env_keys = [e.split("=")[0] for e in hg_env if "=" in e]
            hg_env_vals = {e.split("=")[0]: e.split("=", 1)[1] for e in hg_env if "=" in e}
        elif isinstance(hg_env, dict):
            hg_env_keys = list(hg_env.keys())
            hg_env_vals = hg_env
        else:
            hg_env_keys = []
            hg_env_vals = {}
        total_score += check(
            "honeygain_env_EMAIL",
            "HONEYGAIN_EMAIL" in hg_env_keys,
            f"Honeygain env keys: {hg_env_keys} — must contain HONEYGAIN_EMAIL",
            1.0
        )
        total_score += check(
            "honeygain_env_PASS",
            "HONEYGAIN_PASS" in hg_env_keys,
            f"Honeygain env keys: {hg_env_keys} — must contain HONEYGAIN_PASS",
            1.0
        )
        # HONEYGAIN_DEVICE is a proprietary trap — easily missed
        total_score += check(
            "honeygain_env_DEVICE",
            "HONEYGAIN_DEVICE" in hg_env_keys,
            f"Honeygain env keys: {hg_env_keys} — must contain HONEYGAIN_DEVICE (proprietary field)",
            2.0
        )
        hg_name = hg.get("container_name", "")
        total_score += check(
            "honeygain_container_name",
            hg_name == "honeygain-node",
            f"Honeygain container_name: '{hg_name}' (expected 'honeygain-node')",
            1.0
        )
    except Exception as e:
        total_score += check("honeygain_checks", False, f"Exception checking honeygain service: {e}", 6.5)

    # --- Top-level compose checks ---
    try:
        vols_top = compose.get("volumes", {})
        total_score += check(
            "compose_mysterium_volume_declared",
            "mysterium_data" in vols_top,
            f"Top-level volumes: {list(vols_top.keys())} — must declare 'mysterium_data'",
            1.5
        )
    except Exception as e:
        total_score += check("compose_top_level_volumes", False, f"Exception: {e}", 1.5)

# ============================================================
# CHECK GROUP 2: bandwidth-monitor.sh validation
# ============================================================
try:
    monitor_path = find_file("bandwidth-monitor.sh")
    if monitor_path is None:
        total_score += check("monitor_script_exists", False, "bandwidth-monitor.sh not found", 2.0)
        monitor_content = None
    else:
        with open(monitor_path) as f:
            monitor_content = f.read()
        total_score += check("monitor_script_exists", True, f"Found bandwidth-monitor.sh at {monitor_path}", 2.0)
except Exception as e:
    monitor_content = None
    total_score += check("monitor_script_exists", False, f"Error reading monitor script: {e}", 2.0)

if monitor_content:
    try:
        # Must check all 4 exact container names
        for cname in ["grass-node", "mysterium-node", "storj-node", "honeygain-node"]:
            total_score += check(
                f"monitor_checks_{cname}",
                cname in monitor_content,
                f"bandwidth-monitor.sh {'contains' if cname in monitor_content else 'MISSING'} '{cname}'",
                1.0
            )
        # Must use docker inspect pattern (from SKILL.md template)
        uses_docker_inspect = "docker inspect" in monitor_content
        total_score += check(
            "monitor_uses_docker_inspect",
            uses_docker_inspect,
            f"bandwidth-monitor.sh {'uses' if uses_docker_inspect else 'does NOT use'} 'docker inspect'",
            1.5
        )
        # Must have restart logic
        has_restart = "docker start" in monitor_content or "docker restart" in monitor_content
        total_score += check(
            "monitor_has_restart_logic",
            has_restart,
            f"bandwidth-monitor.sh {'has' if has_restart else 'MISSING'} docker restart/start logic",
            1.0
        )
    except Exception as e:
        total_score += check("monitor_content_checks", False, f"Exception: {e}", 5.5)

# ============================================================
# CHECK GROUP 3: earnings_report.json validation
# ============================================================
try:
    earnings_path = find_file("earnings_report.json")
    if earnings_path is None:
        total_score += check("earnings_report_exists", False, "earnings_report.json not found", 2.0)
        earnings = None
    else:
        with open(earnings_path) as f:
            earnings = json.load(f)
        total_score += check("earnings_report_exists", True, f"Found earnings_report.json at {earnings_path}", 2.0)
except Exception as e:
    earnings = None
    total_score += check("earnings_report_exists", False, f"Error reading earnings_report.json: {e}", 2.0)

if earnings:
    try:
        # Must have bandwidth_mbps field showing 50 Mbps scenario
        bw = earnings.get("bandwidth_mbps", None)
        total_score += check(
            "earnings_bandwidth_50mbps",
            bw == 50 or bw == "50",
            f"earnings_report.json bandwidth_mbps: {bw} (expected 50 for the 50Mbps scenario)",
            1.0
        )

        platforms = earnings.get("platforms", {})

        # Grass at 50Mbps: $80-200/mo
        grass_e = platforms.get("grass", {})
        g_min = grass_e.get("min_monthly_usd", None)
        g_max = grass_e.get("max_monthly_usd", None)
        total_score += check(
            "earnings_grass_50mbps_min",
            g_min == 80,
            f"Grass min at 50Mbps: {g_min} (expected 80)",
            1.0
        )
        total_score += check(
            "earnings_grass_50mbps_max",
            g_max == 200,
            f"Grass max at 50Mbps: {g_max} (expected 200)",
            1.0
        )

        # Mysterium at 50Mbps: $15-50/mo
        myst_e = platforms.get("mysterium", {})
        m_min = myst_e.get("min_monthly_usd", None)
        m_max = myst_e.get("max_monthly_usd", None)
        total_score += check(
            "earnings_mysterium_50mbps_min",
            m_min == 15,
            f"Mysterium min at 50Mbps: {m_min} (expected 15)",
            1.0
        )
        total_score += check(
            "earnings_mysterium_50mbps_max",
            m_max == 50,
            f"Mysterium max at 50Mbps: {m_max} (expected 50)",
            1.0
        )

        # Storj at 50Mbps: $10-50/mo
        storj_e = platforms.get("storj", {})
        s_min = storj_e.get("min_monthly_usd", None)
        s_max = storj_e.get("max_monthly_usd", None)
        total_score += check(
            "earnings_storj_50mbps_min",
            s_min == 10,
            f"Storj min at 50Mbps: {s_min} (expected 10)",
            1.0
        )
        total_score += check(
            "earnings_storj_50mbps_max",
            s_max == 50,
            f"Storj max at 50Mbps: {s_max} (expected 50)",
            1.0
        )

        # Honeygain at 50Mbps: $10-40/mo
        hg_e = platforms.get("honeygain", {})
        h_min = hg_e.get("min_monthly_usd", None)
        h_max = hg_e.get("max_monthly_usd", None)
        total_score += check(
            "earnings_honeygain_50mbps_min",
            h_min == 10,
            f"Honeygain min at 50Mbps: {h_min} (expected 10)",
            1.0
        )
        total_score += check(
            "earnings_honeygain_50mbps_max",
            h_max == 40,
            f"Honeygain max at 50Mbps: {h_max} (expected 40)",
            1.0
        )

        # Total: $115-340/mo
        total_e = earnings.get("total", {})
        t_min = total_e.get("min_monthly_usd", None)
        t_max = total_e.get("max_monthly_usd", None)
        total_score += check(
            "earnings_total_50mbps_min",
            t_min == 115,
            f"Total min at 50Mbps: {t_min} (expected 115)",
            1.5
        )
        total_score += check(
            "earnings_total_50mbps_max",
            t_max == 340,
            f"Total max at 50Mbps: {t_max} (expected 340)",
            1.5
        )
    except Exception as e:
        total_score += check("earnings_content_checks", False, f"Exception: {e}", 12.0)

# ============================================================
# Final scoring
# ============================================================
max_score = 62.5  # sum of all weights
normalized = round(total_score / max_score, 4)
passed = normalized >= 0.70

result = {
    "passed": passed,
    "score": normalized,
    "checks": checks
}
print(json.dumps(result, indent=2))