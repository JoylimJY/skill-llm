#!/usr/bin/env python3
"""
Evaluation script for the Maven Central publishing task.
Checks that the agent has correctly configured:
1. A compliant pom.xml with all required metadata and plugins
2. ~/.m2/settings.xml with correct server ID and GPG profile
3. ~/.gnupg/gpg-agent.conf with allow-loopback-pinentry
4. ~/.gnupg/gpg.conf with pinentry-mode loopback
"""

import sys
import json
import os
from pathlib import Path

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None

def find_pom(workspace):
    """Find the main pom.xml in the project."""
    candidates = list(Path(workspace).rglob("pom.xml"))
    # Prefer the one in currencykit-sdk
    for c in candidates:
        if "currencykit-sdk" in str(c) and c.parent.name == "currencykit-sdk":
            return c
    # Fallback: any pom.xml
    return candidates[0] if candidates else None

def parse_xml(filepath):
    try:
        tree = ET.parse(str(filepath))
        return tree.getroot()
    except Exception as e:
        return None

def get_ns(root):
    """Extract namespace from root tag."""
    if root is None:
        return ""
    tag = root.tag
    if tag.startswith("{"):
        return tag.split("}")[0] + "}"
    return ""

def find_text(root, path, ns=""):
    """Find text at a given tag path, handling namespace."""
    try:
        parts = path.split("/")
        node = root
        for p in parts:
            node = node.find(f"{ns}{p}")
            if node is None:
                return None
        return node.text
    except:
        return None

def find_all_plugins(root, ns):
    """Return all plugin elements from both main build and profiles."""
    plugins = []
    # Main build plugins
    build = root.find(f"{ns}build")
    if build is not None:
        for plugins_block in build.findall(f"{ns}plugins"):
            plugins.extend(plugins_block.findall(f"{ns}plugin"))
    # Profile build plugins
    profiles_el = root.find(f"{ns}profiles")
    if profiles_el is not None:
        for profile in profiles_el.findall(f"{ns}profile"):
            pbuild = profile.find(f"{ns}build")
            if pbuild is not None:
                for pb in pbuild.findall(f"{ns}plugins"):
                    plugins.extend(pb.findall(f"{ns}plugin"))
    return plugins

def plugin_has_value(plugin, ns, *path_and_value):
    """Check deep nested value in plugin XML."""
    path, value = path_and_value[:-1], path_and_value[-1]
    node = plugin
    for p in path:
        node = node.find(f"{ns}{p}")
        if node is None:
            return False
    return node.text is not None and value.lower() in node.text.lower()

def check_plugin_present(plugins, ns, artifact_id, group_id=None):
    """Check if a plugin with given artifactId (and optionally groupId) is present."""
    for p in plugins:
        aid = p.find(f"{ns}artifactId")
        gid = p.find(f"{ns}groupId")
        if aid is not None and aid.text == artifact_id:
            if group_id is None:
                return p
            if gid is not None and gid.text == group_id:
                return p
    return None

def check_file_contains(filepath, *strings):
    """Check if file contains all given strings."""
    try:
        content = Path(filepath).read_text()
        return all(s in content for s in strings), content
    except:
        return False, ""

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ─────────────────────────────────────────────
# SECTION 1: pom.xml validation
# ─────────────────────────────────────────────
workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
pom_path = find_pom(workspace)

if pom_path is None:
    add_check("pom.xml exists", False, "No pom.xml found in workspace")
    root = None
    ns = ""
else:
    add_check("pom.xml exists", True, f"Found at {pom_path}")
    root = parse_xml(pom_path)
    ns = get_ns(root)

# 1a. Required metadata fields
required_metadata = ["name", "description", "url"]
for field in required_metadata:
    if root is not None:
        val = find_text(root, field, ns)
        passed = val is not None and len(val.strip()) > 3
        add_check(f"pom.xml has <{field}>", passed, f"Value: '{val}'" if val else "Missing or empty")
    else:
        add_check(f"pom.xml has <{field}>", False, "pom.xml could not be parsed")

# 1b. Licenses section
if root is not None:
    licenses = root.find(f"{ns}licenses")
    passed = licenses is not None and licenses.find(f"{ns}license") is not None
    add_check("pom.xml has <licenses>", passed, "Found licenses block" if passed else "Missing <licenses><license>")
else:
    add_check("pom.xml has <licenses>", False, "pom.xml not parsed")

# 1c. Developers section
if root is not None:
    developers = root.find(f"{ns}developers")
    passed = developers is not None and developers.find(f"{ns}developer") is not None
    add_check("pom.xml has <developers>", passed, "Found developers block" if passed else "Missing <developers><developer>")
else:
    add_check("pom.xml has <developers>", False, "pom.xml not parsed")

# 1d. SCM section
if root is not None:
    scm = root.find(f"{ns}scm")
    passed = scm is not None
    add_check("pom.xml has <scm>", passed, "Found scm block" if passed else "Missing <scm>")
else:
    add_check("pom.xml has <scm>", False, "pom.xml not parsed")

# 1e. Plugin checks
if root is not None:
    all_plugins = find_all_plugins(root, ns)

    # Source plugin
    source_plugin = check_plugin_present(all_plugins, ns, "maven-source-plugin")
    add_check("maven-source-plugin present", source_plugin is not None,
              "Found maven-source-plugin" if source_plugin else "Missing maven-source-plugin")

    # Javadoc plugin
    javadoc_plugin = check_plugin_present(all_plugins, ns, "maven-javadoc-plugin")
    add_check("maven-javadoc-plugin present", javadoc_plugin is not None,
              "Found maven-javadoc-plugin" if javadoc_plugin else "Missing maven-javadoc-plugin")

    # Javadoc doclint=none
    if javadoc_plugin is not None:
        pom_text = Path(pom_path).read_text()
        has_doclint = "doclint" in pom_text and "none" in pom_text
        add_check("maven-javadoc-plugin has doclint=none",
                  has_doclint,
                  "doclint=none found in pom" if has_doclint else "Missing <doclint>none</doclint>")
        has_failonerror = "failOnError" in pom_text and "false" in pom_text
        add_check("maven-javadoc-plugin has failOnError=false",
                  has_failonerror,
                  "failOnError=false found" if has_failonerror else "Missing <failOnError>false</failOnError>")
    else:
        add_check("maven-javadoc-plugin has doclint=none", False, "javadoc plugin missing")
        add_check("maven-javadoc-plugin has failOnError=false", False, "javadoc plugin missing")

    # GPG plugin
    gpg_plugin = check_plugin_present(all_plugins, ns, "maven-gpg-plugin")
    add_check("maven-gpg-plugin present", gpg_plugin is not None,
              "Found maven-gpg-plugin" if gpg_plugin else "Missing maven-gpg-plugin")

    # GPG plugin: pinentry-mode loopback args
    if gpg_plugin is not None:
        pom_text = Path(pom_path).read_text()
        has_pinentry = "--pinentry-mode" in pom_text and "loopback" in pom_text
        add_check("maven-gpg-plugin has --pinentry-mode loopback args",
                  has_pinentry,
                  "Found pinentry-mode loopback in gpg plugin config" if has_pinentry else
                  "Missing <gpgArguments><arg>--pinentry-mode</arg><arg>loopback</arg></gpgArguments>")
    else:
        add_check("maven-gpg-plugin has --pinentry-mode loopback args", False, "gpg plugin missing")

    # GPG plugin: verify phase
    if gpg_plugin is not None:
        pom_text = Path(pom_path).read_text()
        has_verify = "<phase>verify</phase>" in pom_text
        add_check("maven-gpg-plugin bound to verify phase", has_verify,
                  "Found <phase>verify</phase>" if has_verify else "Missing phase=verify in gpg plugin")
    else:
        add_check("maven-gpg-plugin bound to verify phase", False, "gpg plugin missing")

    # Central Publishing Plugin
    central_plugin = check_plugin_present(all_plugins, ns,
                                          "central-publishing-maven-plugin",
                                          "org.sonatype.central")
    add_check("central-publishing-maven-plugin present (correct groupId: org.sonatype.central)",
              central_plugin is not None,
              "Found central-publishing-maven-plugin with correct groupId" if central_plugin
              else "Missing or wrong groupId for central-publishing-maven-plugin (must be org.sonatype.central)")

    # Central plugin: extensions=true
    if central_plugin is not None:
        ext_el = central_plugin.find(f"{ns}extensions")
        ext_ok = ext_el is not None and ext_el.text == "true"
        add_check("central-publishing-maven-plugin has <extensions>true</extensions>",
                  ext_ok,
                  "extensions=true found" if ext_ok else "Missing <extensions>true</extensions>")

        # publishingServerId = central
        pom_text = Path(pom_path).read_text()
        has_server_id = "<publishingServerId>central</publishingServerId>" in pom_text
        add_check("central-publishing-maven-plugin publishingServerId=central",
                  has_server_id,
                  "Found publishingServerId=central" if has_server_id
                  else "Missing <publishingServerId>central</publishingServerId>")
    else:
        add_check("central-publishing-maven-plugin has <extensions>true</extensions>", False, "central plugin missing")
        add_check("central-publishing-maven-plugin publishingServerId=central", False, "central plugin missing")

    # Release profile: GPG and central plugin should be in a 'release' profile
    profiles_el = root.find(f"{ns}profiles")
    release_profile = None
    if profiles_el is not None:
        for profile in profiles_el.findall(f"{ns}profile"):
            pid = profile.find(f"{ns}id")
            if pid is not None and pid.text == "release":
                release_profile = profile
                break
    add_check("release profile exists in pom.xml",
              release_profile is not None,
              "Found <profile><id>release</id>..." if release_profile else "Missing <profile id='release'>")

    if release_profile is not None:
        pbuild = release_profile.find(f"{ns}build")
        profile_plugins = []
        if pbuild is not None:
            for pb in pbuild.findall(f"{ns}plugins"):
                profile_plugins.extend(pb.findall(f"{ns}plugin"))
        gpg_in_profile = check_plugin_present(profile_plugins, ns, "maven-gpg-plugin") is not None
        central_in_profile = check_plugin_present(profile_plugins, ns,
                                                   "central-publishing-maven-plugin",
                                                   "org.sonatype.central") is not None
        # Accept if either plugin is in the release profile (or both)
        any_in_profile = gpg_in_profile or central_in_profile
        add_check("GPG or central plugin configured within release profile",
                  any_in_profile,
                  f"GPG in profile: {gpg_in_profile}, Central in profile: {central_in_profile}")
    else:
        add_check("GPG or central plugin configured within release profile", False, "No release profile found")

else:
    # pom.xml couldn't be parsed - fail all plugin checks
    for check_name in [
        "maven-source-plugin present", "maven-javadoc-plugin present",
        "maven-javadoc-plugin has doclint=none", "maven-javadoc-plugin has failOnError=false",
        "maven-gpg-plugin present", "maven-gpg-plugin has --pinentry-mode loopback args",
        "maven-gpg-plugin bound to verify phase",
        "central-publishing-maven-plugin present (correct groupId: org.sonatype.central)",
        "central-publishing-maven-plugin has <extensions>true</extensions>",
        "central-publishing-maven-plugin publishingServerId=central",
        "release profile exists in pom.xml",
        "GPG or central plugin configured within release profile",
    ]:
        add_check(check_name, False, "pom.xml could not be parsed")

# ─────────────────────────────────────────────
# SECTION 2: ~/.m2/settings.xml
# ─────────────────────────────────────────────
settings_path = Path.home() / ".m2" / "settings.xml"

if not settings_path.exists():
    add_check("~/.m2/settings.xml exists", False, f"Not found at {settings_path}")
    for n in ["settings.xml server id=central", "settings.xml has GPG passphrase in release profile",
              "settings.xml release profile has gpg.executable"]:
        add_check(n, False, "settings.xml missing")
else:
    add_check("~/.m2/settings.xml exists", True, str(settings_path))
    settings_root = parse_xml(settings_path)
    settings_ns = get_ns(settings_root)
    settings_text = settings_path.read_text()

    # Server with id=central
    server_central = False
    if settings_root is not None:
        servers = settings_root.find(f"{settings_ns}servers")
        if servers is not None:
            for srv in servers.findall(f"{settings_ns}server"):
                sid = srv.find(f"{settings_ns}id")
                if sid is not None and sid.text == "central":
                    server_central = True
    add_check("settings.xml server id=central", server_central,
              "Found <server><id>central</id>" if server_central
              else "Missing server with id=central (must match publishingServerId)")

    # Release profile with GPG properties
    has_release_profile = "<id>release</id>" in settings_text
    add_check("settings.xml has release profile", has_release_profile,
              "Found release profile in settings.xml" if has_release_profile else "Missing release profile")

    has_gpg_passphrase = "gpg.passphrase" in settings_text
    add_check("settings.xml has GPG passphrase in release profile", has_gpg_passphrase,
              "Found gpg.passphrase property" if has_gpg_passphrase else "Missing <gpg.passphrase> in settings.xml")

    has_gpg_exec = "gpg.executable" in settings_text
    add_check("settings.xml release profile has gpg.executable", has_gpg_exec,
              "Found gpg.executable property" if has_gpg_exec else "Missing <gpg.executable> in settings.xml")

# ─────────────────────────────────────────────
# SECTION 3: GPG loopback pinentry configuration
# ─────────────────────────────────────────────
gpg_agent_conf = Path.home() / ".gnupg" / "gpg-agent.conf"
gpg_conf = Path.home() / ".gnupg" / "gpg.conf"

# gpg-agent.conf: allow-loopback-pinentry
ok, content = check_file_contains(gpg_agent_conf, "allow-loopback-pinentry")
add_check("~/.gnupg/gpg-agent.conf has allow-loopback-pinentry", ok,
          "Found 'allow-loopback-pinentry'" if ok
          else f"Missing 'allow-loopback-pinentry' in {gpg_agent_conf} (content: {content[:200] if content else 'file missing'})")

# gpg.conf: pinentry-mode loopback
ok2, content2 = check_file_contains(gpg_conf, "pinentry-mode", "loopback")
add_check("~/.gnupg/gpg.conf has pinentry-mode loopback", ok2,
          "Found 'pinentry-mode loopback'" if ok2
          else f"Missing 'pinentry-mode loopback' in {gpg_conf} (content: {content2[:200] if content2 else 'file missing'})")

# ─────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
passed = score >= 0.80  # Require 80%+ to pass

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))