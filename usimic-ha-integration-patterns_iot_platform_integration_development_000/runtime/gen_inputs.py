import os
import json
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── distractor tree ──────────────────────────────────────────────────────────
distractor_dirs = [
    "legacy_integrations/old_sensor",
    "legacy_integrations/deprecated_lights",
    "docs/architecture",
    "docs/api_notes",
    "scripts/deploy",
    "scripts/test_runners",
    "scratch/experiments",
    "scratch/proto_nestguard",
    "config_backups",
    "tools/linters",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files (red herrings)
distractor_files = {
    "legacy_integrations/old_sensor/__init__.py": textwrap.dedent("""\
        # OLD pattern — do NOT use this as a reference
        def setup(hass, config):
            hass.services.register('old_sensor', 'ping', lambda call: None)
            return True
    """),
    "legacy_integrations/old_sensor/manifest.json": json.dumps({
        "domain": "old_sensor",
        "name": "Old Sensor",
        "version": "0.1.0"
        # Intentionally missing required fields
    }, indent=2),
    "legacy_integrations/deprecated_lights/__init__.py": textwrap.dedent("""\
        # Uses private APIs — WRONG pattern
        async def async_setup(hass, config):
            storage = hass.data['_storage_collection']  # BAD: underscore API
            return True
    """),
    "docs/architecture/overview.txt": textwrap.dedent("""\
        NestGuard Integration Architecture
        ===================================
        The integration exposes:
          1. A REST endpoint at /api/nestguard/zones  (GET, auth required)
          2. A service   nestguard.get_zone_config    (must return data synchronously)
          3. Persistent storage of zone configurations

        Zone data shape:
          {
            "zones": [
              {"id": "z1", "name": "Front Door", "armed": true},
              {"id": "z2", "name": "Back Window", "armed": false}
            ]
          }
    """),
    "docs/api_notes/service_notes.txt": textwrap.dedent("""\
        IMPORTANT: The get_zone_config service must RETURN data to the caller.
        Legacy fire-and-forget pattern will NOT work here.
        The endpoint /api/nestguard/zones must require authentication.
        Storage key should be: nestguard.zones
        Storage version: 1
    """),
    "docs/api_notes/broken_example.py": textwrap.dedent("""\
        # Broken example — do NOT copy
        # Missing supports_response, wrong view registration
        hass.services.async_register('nestguard', 'get_zone_config', handler)

        class ZonesView:  # Not subclassing HomeAssistantView
            url = '/api/nestguard/zones'
            async def get(self, request):
                return {}
    """),
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploy script placeholder'\n",
    "scripts/test_runners/run_tests.sh": "#!/bin/bash\npytest tests/\n",
    "scratch/experiments/test_response.py": textwrap.dedent("""\
        # Scratch — exploring service response
        # SupportsResponse exists in homeassistant.helpers.service
        # but this file is incomplete and wrong
        from homeassistant.helpers.service import SupportsResponse
        # TODO: figure out which value to use
    """),
    "scratch/proto_nestguard/rough_init.py": textwrap.dedent("""\
        # Prototype — abandoned
        async def async_setup_entry(hass, entry):
            # store data incorrectly
            hass.data['nestguard'] = {}
            return True
    """),
    "config_backups/old_config.json": json.dumps({
        "nestguard": {"zones": [], "version": "0.0.1"}
    }, indent=2),
    "tools/linters/check_imports.py": textwrap.dedent("""\
        import ast, sys
        # Checks for underscore-prefixed hass.data access
        def check(filepath):
            with open(filepath) as f:
                tree = ast.parse(f.read())
            # stub
            print('OK')
        if __name__ == '__main__':
            check(sys.argv[1])
    """),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── partial / broken scaffold the agent must FIX & COMPLETE ──────────────────
# The agent must create: custom_components/nestguard/{__init__.py, config_flow.py,
#   manifest.json, services.yaml, storage_services.py}
# We intentionally do NOT pre-create these files so the agent builds from scratch.

# BUT we drop a requirements stub to show the domain name
requirements_stub = os.path.join(BASE, "docs", "architecture", "requirements_stub.txt")
with open(requirements_stub, "w") as f:
    f.write(textwrap.dedent("""\
        Integration domain : nestguard
        Display name       : NestGuard Security
        HACS compliant     : yes
        Config flow UI     : required
        Codeowner          : @nestguard-dev

        Services to expose:
          nestguard.get_zone_config
            - Must return zone data to the caller (not fire-and-forget)

        HTTP endpoint:
          GET /api/nestguard/zones
            - Requires authentication
            - Returns current zone configuration from storage

        Storage:
          - Key  : nestguard.zones
          - Ver  : 1
          - Saves and loads zone JSON data
    """))

print("Workspace generated successfully.")