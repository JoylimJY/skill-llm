import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure mimicking sonic-buildimage ---
dirs = [
    "sonic-buildimage/rules",
    "sonic-buildimage/src/sonic-utilities",
    "sonic-buildimage/src/sonic-swss",
    "sonic-buildimage/src/libswsscommon",
    "sonic-buildimage/src/sonic-sairedis",
    "sonic-buildimage/src/sonic-platform-common",
    "sonic-buildimage/platform/vs",
    "sonic-buildimage/platform/broadcom",
    "sonic-buildimage/platform/mellanox",
    "sonic-buildimage/target/debs/bookworm",
    "sonic-buildimage/target/debs/trixie",
    "sonic-buildimage/target/docker-images",
    "sonic-buildimage/references",
    "sonic-buildimage/dockers/docker-syncd-vs",
    "sonic-buildimage/dockers/docker-orchagent",
    "sonic-buildimage/slave.mk.d",
    "sonic-buildimage/build_metadata",
    "ci-logs/2024-01-15",
    "ci-logs/2024-01-16",
    "team-docs",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Realistic distractor files ---

# rules/config — the REAL config (agent must NOT edit this, must create config.user)
config_content = textwrap.dedent("""\
    # SONiC Build Configuration
    # DO NOT EDIT — use rules/config.user to override
    SONIC_CONFIG_BUILD_JOBS ?= 1
    SONIC_CONFIG_MAKE_JOBS ?= $(shell nproc)
    BUILD_SKIP_TEST ?= n
    SONIC_BUILD_MEMORY ?=
    SONIC_DPKG_CACHE_METHOD ?= none
    SONIC_DPKG_CACHE_SOURCE ?= /var/cache/sonic/artifacts
    SONIC_VERSION_CACHE_METHOD ?= none
    DEFAULT_BUILD_LOG_TIMESTAMP ?= none
    SONIC_CONFIG_USE_NATIVE_DOCKERD_FOR_BUILD ?=
    BLDENV ?= bookworm
""")
with open(os.path.join(WORKSPACE, "sonic-buildimage/rules/config"), "w") as f:
    f.write(config_content)

# rules/Makefile.dep — distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/rules/Makefile.dep"), "w") as f:
    f.write("# Package dependency graph\nlibswsscommon: python3-swsscommon\nSONIC_INSTALL_PKGS += libswsscommon\n")

# Makefile — distractor
makefile_content = textwrap.dedent("""\
    .PHONY: init configure all clean
    include Makefile.work
    init:
    \tgit submodule update --init --recursive
    configure:
    \t$(eval PLATFORM := $(PLATFORM))
    \t@echo Configuring for $(PLATFORM)
    all: target/sonic-vs.img.gz
""")
with open(os.path.join(WORKSPACE, "sonic-buildimage/Makefile"), "w") as f:
    f.write(makefile_content)

# slave.mk — distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/slave.mk"), "w") as f:
    f.write("# Slave build orchestration\nSONIC_SLAVE_DOCKER_ARGS += --memory=$(SONIC_BUILD_MEMORY)\n")

# A broken/stale config.user that existed before — WRONG values, agent must fix/replace
bad_config_user = textwrap.dedent("""\
    # Old config - DO NOT USE
    SONIC_CONFIG_BUILD_JOBS = 16
    BUILD_SKIP_TEST = n
    SONIC_BUILD_MEMORY = 999g
    DEFAULT_BUILD_LOG_TIMESTAMP = verbose
    SONIC_DPKG_CACHE_METHOD = none
""")
with open(os.path.join(WORKSPACE, "sonic-buildimage/rules/config.user"), "w") as f:
    f.write(bad_config_user)

# references/troubleshooting.md — distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/references/troubleshooting.md"), "w") as f:
    f.write("# Troubleshooting\n\nSee logs in target/. OOM errors usually mean SONIC_BUILD_MEMORY is not set.\n")

# references/prerequisites.md — distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/references/prerequisites.md"), "w") as f:
    f.write("# Prerequisites\n\nDocker >= 20.10, Python 3.9+, jinjanator\n")

# references/vs-platform.md — distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/references/vs-platform.md"), "w") as f:
    f.write("# VS Platform\n\nUses TAP devices for port emulation. sai.profile controls port count.\n")

# CI logs — distractors showing OOM errors
oom_log = textwrap.dedent("""\
    2024-01-15 03:22:11 [ERROR] Killed process 4521 (cc1plus) total-vm:8192000kB
    2024-01-15 03:22:11 [ERROR] Out of memory: Kill process 4521
    2024-01-15 03:22:12 [INFO] Build FAILED: sonic-utilities
    2024-01-15 03:22:12 [INFO] SONIC_CONFIG_BUILD_JOBS was 8, RAM available: 32GB
""")
with open(os.path.join(WORKSPACE, "ci-logs/2024-01-15/build.log"), "w") as f:
    f.write(oom_log)

with open(os.path.join(WORKSPACE, "ci-logs/2024-01-16/build.log"), "w") as f:
    f.write("2024-01-16 01:00:00 [INFO] Build started PLATFORM=vs JOBS=1\n2024-01-16 04:10:00 [INFO] Build SUCCESS (3h10m)\n")

# team-docs — distractor
with open(os.path.join(WORKSPACE, "team-docs/ci-strategy.md"), "w") as f:
    f.write(textwrap.dedent("""\
        # CI Strategy Notes
        - We have 36GB RAM on CI runners
        - Builds are taking too long (3+ hours)
        - We keep hitting OOM with JOBS=8
        - Incremental caching not configured
        - src/sonic-swss submodule keeps failing to init properly
        - Need to document the fix command for the corrupted submodule
    """))

# Submodule corruption indicator
with open(os.path.join(WORKSPACE, "sonic-buildimage/src/sonic-swss/.git"), "w") as f:
    f.write("gitdir: ../../.git/modules/src/sonic-swss\n")

with open(os.path.join(WORKSPACE, "sonic-buildimage/src/libswsscommon/.git"), "w") as f:
    f.write("gitdir: ../../.git/modules/src/libswsscommon\n# CORRUPTED - reinit needed\n")

# Build metadata distractors
with open(os.path.join(WORKSPACE, "sonic-buildimage/build_metadata/last_platform"), "w") as f:
    f.write("vs\n")

with open(os.path.join(WORKSPACE, "sonic-buildimage/build_metadata/build_id"), "w") as f:
    f.write("build-2024-01-16-001\n")

# platform distractors
with open(os.path.join(WORKSPACE, "sonic-buildimage/platform/vs/sai.profile"), "w") as f:
    f.write("SAI_VS_SWITCH_TYPE=SAI_VS_SWITCH_TYPE_BCM_NPLS\nSAI_VS_NUM_FP_PORTS=32\n")

with open(os.path.join(WORKSPACE, "sonic-buildimage/platform/broadcom/PLATFORM"), "w") as f:
    f.write("broadcom\n")

# docker distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/dockers/docker-syncd-vs/Dockerfile"), "w") as f:
    f.write("FROM debian:bookworm\nRUN apt-get update\n")

# slave.mk.d distractor
with open(os.path.join(WORKSPACE, "sonic-buildimage/slave.mk.d/caching.mk"), "w") as f:
    f.write("# DPKG cache logic\nifeq ($(SONIC_DPKG_CACHE_METHOD), rwcache)\n  DPKG_CACHE_ARGS = --cache-dir $(SONIC_DPKG_CACHE_SOURCE)\nendif\n")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}/")