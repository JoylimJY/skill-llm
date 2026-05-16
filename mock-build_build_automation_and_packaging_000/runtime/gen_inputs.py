#!/usr/bin/env python3
"""Generate the sandbox workspace for the mock RPM build task."""

import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "project/SPECS",
    "project/SOURCES",
    "project/SRPMS",
    "project/RPMS/x86_64",
    "project/BUILD",
    "project/BUILDROOT",
    "configs",
    "scripts",
    "results/batch",
    "results/single",
    "archive/old_builds",
    "archive/failed_builds",
    "docs",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# 1. A broken/outdated mock config that uses wrong syntax (INI style, not Python dict)
broken_cfg = """\
# WRONG FORMAT - do not use this
[main]
root = old-custom-x86_64
target_arch = x86_64
dist = fc38
releasever = 38
chroot_additional_packages = gcc make
"""
with open(os.path.join(workspace, "configs/broken_old.cfg"), "w") as f:
    f.write(broken_cfg)

# 2. Another broken config missing required keys
incomplete_cfg = """\
config_opts['root'] = 'incomplete-build'
config_opts['target_arch'] = 'x86_64'
# missing yum.conf, missing chroot_setup_cmd
"""
with open(os.path.join(workspace, "configs/incomplete.cfg"), "w") as f:
    f.write(incomplete_cfg)

# 3. A spec file for the security package
spec_content = """\
Name:           secpkg
Version:        2.1.0
Release:        1%{?dist}
Summary:        Security Package for Enterprise Linux

License:        MIT
URL:            https://example.com/secpkg
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  openssl-devel

%description
A security-sensitive package built in isolated chroot environments.

%prep
%autosetup

%build
%configure
%make_build

%install
%make_install

%files
%license LICENSE
%doc README.md
/usr/bin/secpkg
/usr/lib/libsecpkg.so.1

%changelog
* Mon Mar 23 2026 Build Agent <build@example.com> - 2.1.0-1
- Initial package release
"""
with open(os.path.join(workspace, "project/SPECS/secpkg.spec"), "w") as f:
    f.write(spec_content)

# 4. Source tarball placeholder
with open(os.path.join(workspace, "project/SOURCES/secpkg-2.1.0.tar.gz"), "wb") as f:
    f.write(b"\x1f\x8b\x08\x00" + b"\x00" * 20)  # fake gzip header

# 5. Fake SRPMs to batch-build
srpms = [
    "libcrypto-utils-1.4-2.fc39.src.rpm",
    "auth-daemon-3.0.1-1.fc39.src.rpm",
    "secaudit-0.9.5-3.fc39.src.rpm",
]
for srpm in srpms:
    with open(os.path.join(workspace, "project/SRPMS", srpm), "wb") as f:
        # Fake RPM magic bytes
        f.write(b"\xed\xab\xee\xdb" + srpm.encode() + b"\x00" * 16)

# 6. Old/wrong build scripts (distractors)
old_build_sh = """\
#!/bin/bash
# OLD SCRIPT - uses wrong flags
rpmbuild -ba project/SPECS/secpkg.spec
# This does NOT use isolated chroot - insecure!
"""
with open(os.path.join(workspace, "scripts/old_build.sh"), "w") as f:
    f.write(old_build_sh)
os.chmod(os.path.join(workspace, "scripts/old_build.sh"), 0o755)

# 7. Wrong config with bad chroot_setup_cmd
wrong_setup_cfg = """\
config_opts['root'] = 'wrong-setup-x86_64'
config_opts['target_arch'] = 'x86_64'
config_opts['legal_host_arches'] = ('x86_64',)
config_opts['dist'] = 'fc39'
config_opts['releasever'] = '39'
# WRONG: using yum install instead of install
config_opts['chroot_setup_cmd'] = 'yum install bash gcc make rpm-build'
config_opts['chroot_additional_packages'] = 'gcc gcc-c++ make rpm-build'
config_opts['yum.conf'] = \"\"\"
[main]
cachedir=/var/cache/yum
\"\"\"
"""
with open(os.path.join(workspace, "configs/wrong_setup.cfg"), "w") as f:
    f.write(wrong_setup_cfg)

# 8. A note file describing the project (not a hint, just context)
with open(os.path.join(workspace, "docs/project_overview.txt"), "w") as f:
    f.write("""\
SecPkg Build Pipeline
=====================
This directory contains source files for the enterprise security package suite.
Packages must be built in isolated environments to prevent host contamination.
Build results must be separated by package name.

Packages to batch build:
  - libcrypto-utils
  - auth-daemon  
  - secaudit

The build system requires compiler caching for performance.
All batch build results go into results/batch/<package-name>/
Single SRPM build result: results/single/
""")

# 9. Distractor config files in archive
for i in range(3):
    with open(os.path.join(workspace, f"archive/old_builds/build_{i}.log"), "w") as f:
        f.write(f"Build {i} log - FAILED\nError: chroot not initialized\n")

# 10. A mock-like template file (wrong Python syntax)
with open(os.path.join(workspace, "configs/template_bad.cfg"), "w") as f:
    f.write("""\
# Template - has syntax errors
config_opts['root'] = 'template-x86_64'
config_opts['target_arch'] = x86_64   # missing quotes - syntax error
config_opts['dist'] = 'fc39'
""")

# 11. Integration test placeholder
with open(os.path.join(workspace, "tests/integration/test_build.sh"), "w") as f:
    f.write("""\
#!/bin/bash
# Integration test placeholder
echo "Tests not yet implemented"
""")
os.chmod(os.path.join(workspace, "tests/integration/test_build.sh"), 0o755)

# 12. requirements-like file for distracting
with open(os.path.join(workspace, "docs/dependencies.txt"), "w") as f:
    f.write("""\
Required build dependencies:
- gcc >= 11.0
- gcc-c++
- make
- openssl-devel
- rpm-build
- bash
- bzip2
- coreutils
- cpio
- diffutils
- findutils
- gawk
- grep
- gzip
- info
- patch
- redhat-rpm-config
- sed
- shadow-utils
- tar
- unzip
- util-linux
- which
- xz
""")

print("Workspace generated successfully.")
print(f"Directories created: {len(dirs)}")
print(f"SRPMs created: {len(srpms)}")