import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    workspace_path = Path(workspace)

    # =========================================================
    # CHECK 1: Config file exists with a valid supported name
    # =========================================================
    valid_config_names = [
        "snipgrapher.config.json",
        "snipgrapher.config.yaml",
        "snipgrapher.config.yml",
        "snipgrapher.config.toml",
    ]
    found_config = None
    for name in valid_config_names:
        candidate = workspace_path / name
        if candidate.exists():
            found_config = candidate
            break

    add_check(
        "config_file_exists_with_valid_name",
        found_config is not None,
        f"Found config: {found_config}" if found_config else f"No valid config found in workspace root. Expected one of: {valid_config_names}",
        weight=1.5,
    )

    # =========================================================
    # CHECK 2: Config has correct camelCase keys and required fields
    # =========================================================
    config_data = {}
    if found_config:
        try:
            suffix = found_config.suffix.lower()
            content = found_config.read_text()
            if suffix == ".json":
                config_data = json.loads(content)
            elif suffix in (".yaml", ".yml"):
                import yaml
                config_data = yaml.safe_load(content)
            elif suffix == ".toml":
                import toml
                config_data = toml.loads(content)
        except Exception as e:
            add_check("config_parseable", False, f"Config file could not be parsed: {e}", weight=1.5)
        else:
            add_check("config_parseable", True, "Config file parsed successfully.", weight=0.5)

    # Required camelCase fields
    required_camel_case_fields = ["fontFamily", "fontSize", "lineNumbers", "windowControls", "backgroundStyle", "shadow"]
    if config_data:
        missing = [f for f in required_camel_case_fields if f not in config_data]
        has_bad_case = any(
            k in config_data for k in ["font-family", "font_family", "font_size", "line_numbers", "window_controls"]
        )
        camel_ok = len(missing) == 0 and not has_bad_case
        add_check(
            "config_uses_camelCase_keys",
            camel_ok,
            f"Missing camelCase fields: {missing}. Bad-case keys present: {has_bad_case}" if not camel_ok else "All required camelCase fields present.",
            weight=2.0,
        )
    else:
        add_check("config_uses_camelCase_keys", False, "Config data is empty or unparseable.", weight=2.0)

    # =========================================================
    # CHECK 3: Config has a "profiles" block with both "default" and "social"
    # =========================================================
    if config_data:
        profiles = config_data.get("profiles", {})
        has_default_profile = "default" in profiles
        has_social_profile = "social" in profiles
        profiles_ok = has_default_profile and has_social_profile
        add_check(
            "config_has_default_and_social_profiles",
            profiles_ok,
            f"profiles block: {list(profiles.keys())}. Has 'default': {has_default_profile}, has 'social': {has_social_profile}",
            weight=2.0,
        )

        # Social profile must have at least padding, fontSize, and watermark overrides
        if has_social_profile:
            social = profiles["social"]
            social_has_padding = "padding" in social
            social_has_fontSize = "fontSize" in social
            social_has_watermark = "watermark" in social
            social_ok = social_has_padding and social_has_fontSize and social_has_watermark
            add_check(
                "social_profile_has_required_overrides",
                social_ok,
                f"Social profile keys: {list(social.keys())}. Needs padding, fontSize, watermark.",
                weight=1.5,
            )
        else:
            add_check("social_profile_has_required_overrides", False, "No 'social' profile found.", weight=1.5)
    else:
        add_check("config_has_default_and_social_profiles", False, "Config not parseable.", weight=2.0)
        add_check("social_profile_has_required_overrides", False, "Config not parseable.", weight=1.5)

    # =========================================================
    # CHECK 4: Batch render output directory exists and contains rendered files
    # =========================================================
    # The agent should have run batch rendering on snippets/**/*.ts
    # We look for any directory that contains rendered output files (svg/png/webp)
    rendered_dirs = []
    for d in workspace_path.rglob("*"):
        if d.is_dir():
            rendered_files = list(d.glob("*.svg")) + list(d.glob("*.png")) + list(d.glob("*.webp"))
            if rendered_files:
                rendered_dirs.append((d, rendered_files))

    has_rendered_output = len(rendered_dirs) > 0
    total_rendered = sum(len(rf) for _, rf in rendered_dirs)
    add_check(
        "batch_render_output_exists",
        has_rendered_output,
        f"Found {total_rendered} rendered image file(s) across {len(rendered_dirs)} director(y/ies): {[str(d) for d, _ in rendered_dirs]}" if has_rendered_output else "No rendered image files (svg/png/webp) found anywhere.",
        weight=2.0,
    )

    # Must have rendered at least 3 snippet files (there are 5 source snippets)
    add_check(
        "batch_render_sufficient_count",
        total_rendered >= 3,
        f"Found {total_rendered} rendered image(s). Expected at least 3 (from 5 source snippets).",
        weight=1.5,
    )

    # =========================================================
    # CHECK 5: Manifest JSON file exists and is valid
    # =========================================================
    manifest_files = list(workspace_path.rglob("manifest.json"))
    has_manifest = len(manifest_files) > 0
    add_check(
        "manifest_json_exists",
        has_manifest,
        f"Found manifest.json at: {[str(m) for m in manifest_files]}" if has_manifest else "No manifest.json file found. The batch command must include --json --manifest <path>.",
        weight=2.0,
    )

    manifest_valid = False
    if has_manifest:
        try:
            manifest_content = manifest_files[0].read_text()
            manifest_data = json.loads(manifest_content)
            # Manifest should be a list or dict with file entries
            manifest_valid = isinstance(manifest_data, (list, dict)) and len(manifest_data) > 0
            add_check(
                "manifest_json_is_valid_and_non_empty",
                manifest_valid,
                f"Manifest type: {type(manifest_data).__name__}, length/keys: {len(manifest_data)}",
                weight=2.0,
            )
        except json.JSONDecodeError as e:
            add_check("manifest_json_is_valid_and_non_empty", False, f"manifest.json is not valid JSON: {e}", weight=2.0)
        except Exception as e:
            add_check("manifest_json_is_valid_and_non_empty", False, f"Error reading manifest: {e}", weight=2.0)
    else:
        add_check("manifest_json_is_valid_and_non_empty", False, "No manifest.json found.", weight=2.0)

    # =========================================================
    # CHECK 6: Config file is in the workspace ROOT (not a subdir)
    # =========================================================
    if found_config:
        is_root = found_config.parent == workspace_path
        add_check(
            "config_in_workspace_root",
            is_root,
            f"Config found at: {found_config}. Root: {workspace_path}. In root: {is_root}",
            weight=1.0,
        )
    else:
        add_check("config_in_workspace_root", False, "No config file found.", weight=1.0)

    # =========================================================
    # Final scoring
    # =========================================================
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    passed = score >= 0.75

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))