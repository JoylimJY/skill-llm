import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "src",
    "src/network",
    "src/sensors",
    "src/protocol",
    "config",
    "config/templates",
    "build",
    "tests",
    "tests/unit",
    "tests/integration",
    "docs",
    "scripts",
    "legacy",
    "legacy/v0.9",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- The actual code.c (the config library that must be included) ---
code_c = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_KEY_LEN 128
#define MAX_VAL_LEN 256
#define MAX_CONFIGS 64

typedef enum { CFG_STRING, CFG_INT, CFG_BOOL } ConfigType;

typedef struct {
    char key[MAX_KEY_LEN];
    ConfigType type;
    union {
        char sval[MAX_VAL_LEN];
        int  ival;
        int  bval;
    } value;
} ConfigEntry;

typedef struct {
    ConfigEntry entries[MAX_CONFIGS];
    int count;
} ConfigManager;

ConfigManager* config_create() {
    ConfigManager* cm = (ConfigManager*)malloc(sizeof(ConfigManager));
    if (!cm) return NULL;
    cm->count = 0;
    return cm;
}

void config_destroy(ConfigManager* cm) {
    if (cm) free(cm);
}

void config_add_string(ConfigManager* cm, const char* key, const char* value) {
    if (!cm || cm->count >= MAX_CONFIGS) return;
    ConfigEntry* e = &cm->entries[cm->count++];
    strncpy(e->key, key, MAX_KEY_LEN - 1);
    e->key[MAX_KEY_LEN - 1] = '\0';
    e->type = CFG_STRING;
    strncpy(e->value.sval, value, MAX_VAL_LEN - 1);
    e->value.sval[MAX_VAL_LEN - 1] = '\0';
}

void config_add_int(ConfigManager* cm, const char* key, int value) {
    if (!cm || cm->count >= MAX_CONFIGS) return;
    ConfigEntry* e = &cm->entries[cm->count++];
    strncpy(e->key, key, MAX_KEY_LEN - 1);
    e->key[MAX_KEY_LEN - 1] = '\0';
    e->type = CFG_INT;
    e->value.ival = value;
}

void config_add_bool(ConfigManager* cm, const char* key, int value) {
    if (!cm || cm->count >= MAX_CONFIGS) return;
    ConfigEntry* e = &cm->entries[cm->count++];
    strncpy(e->key, key, MAX_KEY_LEN - 1);
    e->key[MAX_KEY_LEN - 1] = '\0';
    e->type = CFG_BOOL;
    e->value.bval = value ? 1 : 0;
}

const char* config_get_string(ConfigManager* cm, const char* key, const char* default_val) {
    if (!cm) return default_val;
    for (int i = 0; i < cm->count; i++) {
        if (strcmp(cm->entries[i].key, key) == 0 && cm->entries[i].type == CFG_STRING)
            return cm->entries[i].value.sval;
    }
    return default_val;
}

int config_get_int(ConfigManager* cm, const char* key, int default_val) {
    if (!cm) return default_val;
    for (int i = 0; i < cm->count; i++) {
        if (strcmp(cm->entries[i].key, key) == 0 && cm->entries[i].type == CFG_INT)
            return cm->entries[i].value.ival;
    }
    return default_val;
}

int config_get_bool(ConfigManager* cm, const char* key, int default_val) {
    if (!cm) return default_val;
    for (int i = 0; i < cm->count; i++) {
        if (strcmp(cm->entries[i].key, key) == 0 && cm->entries[i].type == CFG_BOOL)
            return cm->entries[i].value.bval;
    }
    return default_val;
}

int config_load_file(ConfigManager* cm, const char* filepath) {
    if (!cm) return -1;
    FILE* f = fopen(filepath, "r");
    if (!f) return -1;
    char line[MAX_KEY_LEN + MAX_VAL_LEN + 4];
    while (fgets(line, sizeof(line), f)) {
        /* strip newline */
        size_t len = strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r')) line[--len] = '\0';
        /* skip comments and blanks */
        if (line[0] == '#' || line[0] == '\0') continue;
        char* eq = strchr(line, '=');
        if (!eq) continue;
        *eq = '\0';
        const char* k = line;
        const char* v = eq + 1;
        /* detect type: bool */
        if (strcmp(v, "true") == 0) { config_add_bool(cm, k, 1); continue; }
        if (strcmp(v, "false") == 0) { config_add_bool(cm, k, 0); continue; }
        /* detect type: integer */
        char* endp;
        long iv = strtol(v, &endp, 10);
        if (*endp == '\0') { config_add_int(cm, k, (int)iv); continue; }
        /* fallback: string */
        config_add_string(cm, k, v);
    }
    fclose(f);
    return 0;
}

int config_save_file(ConfigManager* cm, const char* filepath) {
    if (!cm) return -1;
    FILE* f = fopen(filepath, "w");
    if (!f) return -1;
    for (int i = 0; i < cm->count; i++) {
        ConfigEntry* e = &cm->entries[i];
        if (e->type == CFG_STRING)      fprintf(f, "%s=%s\n", e->key, e->value.sval);
        else if (e->type == CFG_INT)    fprintf(f, "%s=%d\n", e->key, e->value.ival);
        else if (e->type == CFG_BOOL)   fprintf(f, "%s=%s\n", e->key, e->value.bval ? "true" : "false");
    }
    fclose(f);
    return 0;
}

#ifdef CONFIG_DEMO
int main() {
    ConfigManager* cm = config_create();
    config_add_string(cm, "server.host", "localhost");
    config_add_int(cm, "server.port", 8080);
    config_add_bool(cm, "server.ssl", 0);
    printf("host=%s port=%d ssl=%s\n",
        config_get_string(cm, "server.host", "localhost"),
        config_get_int(cm, "server.port", 80),
        config_get_bool(cm, "server.ssl", 0) ? "true" : "false");
    config_destroy(cm);
    return 0;
}
#endif
"""

with open(os.path.join(WORKSPACE, "code.c"), "w") as f:
    f.write(code_c)

# --- Distractor files ---

# Legacy hardcoded gateway source (the "messy old code" the agent is refactoring away from)
legacy_gateway_c = r"""
/* legacy/v0.9/gateway.c — DO NOT USE — replaced by config-driven approach */
#include <stdio.h>
int main() {
    /* hardcoded values — this is what we're moving away from */
    const char* mqtt_broker  = "192.168.1.100";
    int         mqtt_port    = 1883;
    int         tls_enabled  = 0;
    const char* device_id    = "GW-UNIT-007";
    int         poll_interval = 30;
    int         max_retries  = 5;
    printf("broker=%s port=%d tls=%d id=%s poll=%d retries=%d\n",
           mqtt_broker, mqtt_port, tls_enabled,
           device_id, poll_interval, max_retries);
    return 0;
}
"""
with open(os.path.join(WORKSPACE, "legacy/v0.9/gateway.c"), "w") as f:
    f.write(legacy_gateway_c)

# A broken/incomplete config template (distractor — wrong format, has JSON-like syntax)
broken_cfg = """\
{
  "mqtt_broker": "192.168.1.100",
  "mqtt_port": 1883,
  "tls_enabled": false
}
"""
with open(os.path.join(WORKSPACE, "config/templates/gateway_template.json"), "w") as f:
    f.write(broken_cfg)

# An incomplete .ini style file (wrong format for the library)
ini_distractor = """\
[mqtt]
broker = 10.0.0.5
port = 1883
[security]
tls = no
"""
with open(os.path.join(WORKSPACE, "config/templates/old_settings.ini"), "w") as f:
    f.write(ini_distractor)

# Sensor module source (distractor)
sensor_c = r"""
/* src/sensors/temp_sensor.c */
#include <stdio.h>
float read_temperature() { return 23.5f; }
"""
with open(os.path.join(WORKSPACE, "src/sensors/temp_sensor.c"), "w") as f:
    f.write(sensor_c)

# Network helper (distractor)
net_h = r"""
/* src/network/net_utils.h */
#ifndef NET_UTILS_H
#define NET_UTILS_H
int connect_tcp(const char* host, int port);
void disconnect_tcp(int fd);
#endif
"""
with open(os.path.join(WORKSPACE, "src/network/net_utils.h"), "w") as f:
    f.write(net_h)

# Protocol parser (distractor)
proto_c = r"""
/* src/protocol/mqtt_parser.c */
#include <stdio.h>
void parse_mqtt_packet(const char* buf, int len) {
    printf("parsed %d bytes\n", len);
}
"""
with open(os.path.join(WORKSPACE, "src/protocol/mqtt_parser.c"), "w") as f:
    f.write(proto_c)

# Makefile (distractor — references old approach)
makefile = """\
# Makefile (legacy build)
CC=gcc
all: legacy
legacy: legacy/v0.9/gateway.c
\t$(CC) -o build/gateway_legacy legacy/v0.9/gateway.c
clean:
\trm -f build/*
"""
with open(os.path.join(WORKSPACE, "Makefile"), "w") as f:
    f.write(makefile)

# Build notes (distractor)
build_notes = """\
build_notes.txt
===============
Old gateway was compiled with: gcc -o gateway legacy/v0.9/gateway.c
Unit tests are in tests/unit/
Integration tests require hardware.
"""
with open(os.path.join(WORKSPACE, "build_notes.txt"), "w") as f:
    f.write(build_notes)

# Test stubs (distractors)
test_unit = """\
/* tests/unit/test_sensors.c */
#include <assert.h>
/* placeholder */
int main() { return 0; }
"""
with open(os.path.join(WORKSPACE, "tests/unit/test_sensors.c"), "w") as f:
    f.write(test_unit)

test_int = """\
/* tests/integration/test_gateway_connect.c */
/* requires hardware — skip in CI */
int main() { return 0; }
"""
with open(os.path.join(WORKSPACE, "tests/integration/test_gateway_connect.c"), "w") as f:
    f.write(test_int)

# Scripts (distractor)
deploy_sh = """\
#!/bin/bash
# scripts/deploy.sh — copies binary to /opt/gateway/
cp build/gateway /opt/gateway/ 2>/dev/null || echo "deploy failed"
"""
with open(os.path.join(WORKSPACE, "scripts/deploy.sh"), "w") as f:
    f.write(deploy_sh)

# Docs (distractor)
arch_doc = """\
docs/architecture.md
====================
The IoT gateway connects field sensors to a cloud MQTT broker.
All settings were previously hardcoded in legacy/v0.9/gateway.c.
The new config-driven approach must read all parameters from an
external file so the firmware can be redeployed without recompilation.

Required parameters:
  mqtt.broker   — broker hostname or IP
  mqtt.port     — TCP port (default 1883 if missing from file)
  mqtt.tls      — boolean, enable TLS (default false if missing)
  device.id     — string identifier (default "UNKNOWN" if missing)
  poll.interval — integer seconds (default 60 if missing)
  retry.max     — integer count (default 3 if missing)
"""
with open(os.path.join(WORKSPACE, "docs/architecture.md"), "w") as f:
    f.write(arch_doc)

# The actual gateway config file the agent must create AND read
# This is the input config (with some values, but deliberately missing poll.interval and retry.max
# to force default-fallback testing)
gateway_cfg_content = """\
# IoT Gateway Configuration
# key=value format
mqtt.broker=10.42.0.1
mqtt.port=8883
mqtt.tls=true
device.id=GW-PROD-042
"""
with open(os.path.join(WORKSPACE, "config/gateway.cfg"), "w") as f:
    f.write(gateway_cfg_content)

print("Workspace generated successfully.")
print(f"Files created under: {WORKSPACE}")