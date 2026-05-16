import os
import random

random.seed(42)

# Define workspace root
workspace = "/workspace"

# Create directory structure
dirs = [
    "infusion_pump_fw/src",
    "infusion_pump_fw/src/drivers",
    "infusion_pump_fw/src/control",
    "infusion_pump_fw/src/comms",
    "infusion_pump_fw/include",
    "infusion_pump_fw/tests",
    "infusion_pump_fw/tests/unit",
    "infusion_pump_fw/docs",
    "infusion_pump_fw/build",
    "infusion_pump_fw/scripts",
    "infusion_pump_fw/config",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─────────────────────────────────────────────
# MAIN SOURCE FILE: infusion_controller.c
# Contains: race condition, missing input validation,
# integer overflow, hardcoded password, magic numbers,
# function > 50 lines, no timeout on comms
# ─────────────────────────────────────────────
infusion_controller_c = r"""
/*
 * infusion_controller.c
 * Infusion Pump Flow Rate Controller
 * Device: MedFlow-3000 IV Infusion Pump
 * Version: 2.1.4
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "infusion_controller.h"
#include "sensor_driver.h"
#include "network_comm.h"

/* Global shared state - accessed by multiple threads */
static float g_current_flow_rate = 0.0f;
static float g_target_flow_rate  = 0.0f;
static int   g_alarm_active      = 0;

/* ============================================================
 * set_flow_rate()
 * Sets the target drug infusion flow rate (mL/hr).
 * Called from both the UI thread and the remote command thread.
 * ============================================================ */
void set_flow_rate(float rate_ml_per_hr)
{
    /* TODO: add mutex protection */
    g_target_flow_rate = rate_ml_per_hr;  /* RACE CONDITION: no lock */
}

/* ============================================================
 * calculate_dose()
 * Computes total dose in micrograms from concentration and volume.
 * concentration_ug_ml : drug concentration (micrograms/mL)
 * volume_ml           : total volume to infuse (mL)
 * Returns total dose in micrograms.
 * ============================================================ */
long calculate_dose(int concentration_ug_ml, int volume_ml)
{
    /* INTEGER OVERFLOW: both are int, product may overflow */
    return concentration_ug_ml * volume_ml;
}

/* ============================================================
 * validate_and_apply_prescription()
 * Receives prescription parameters from nurse workstation over
 * the hospital network and applies them to the pump controller.
 * This is the main entry point for remote dosing commands.
 * FUNCTION LENGTH VIOLATION: > 50 lines
 * ============================================================ */
int validate_and_apply_prescription(
        const char *patient_id,
        const char *drug_name,
        int         concentration_ug_ml,
        int         volume_ml,
        float       rate_ml_per_hr,
        const char *auth_token)
{
    char log_buffer[64];
    int  dose;

    /* MISSING INPUT VALIDATION: no bounds check on rate or concentration */
    /* rate_ml_per_hr could be negative, zero, or astronomically large    */

    /* Hardcoded admin backdoor credential check */
    if (strcmp(auth_token, "MEDFLOW_ADMIN_2024") == 0) {   /* HARDCODED CREDENTIAL */
        /* bypass all checks */
        g_target_flow_rate = rate_ml_per_hr;
        return 0;
    }

    /* No validation on concentration_ug_ml range */
    dose = (int)(concentration_ug_ml * volume_ml);   /* INTEGER OVERFLOW again */

    /* Log patient data in plaintext over network */
    /* UNENCRYPTED PHI TRANSMISSION */
    char phi_msg[256];
    snprintf(phi_msg, sizeof(phi_msg),
             "PATIENT:%s DRUG:%s DOSE:%d", patient_id, drug_name, dose);
    network_send_plaintext(phi_msg);   /* sends over HTTP, no TLS */

    /* Apply flow rate - still no mutex */
    g_target_flow_rate = rate_ml_per_hr;

    /* Magic numbers everywhere */
    if (rate_ml_per_hr > 500) {        /* MAGIC NUMBER: 500 not defined as constant */
        g_alarm_active = 1;
        return -1;
    }

    if (concentration_ug_ml > 10000) { /* MAGIC NUMBER */
        g_alarm_active = 1;
        return -2;
    }

    if (volume_ml < 1) {               /* partial validation only */
        return -3;
    }

    /* Prepare log entry - buffer possibly too small */
    snprintf(log_buffer, sizeof(log_buffer),
             "Applied: rate=%.2f conc=%d vol=%d",
             rate_ml_per_hr, concentration_ug_ml, volume_ml);
    audit_log(log_buffer);

    /* No error handling if audit_log fails */

    /* Poll sensor with NO timeout */
    float sensor_val = 0.0f;
    while (sensor_val == 0.0f) {              /* MISSING TIMEOUT */
        sensor_val = read_flow_sensor();       /* could block forever */
    }

    g_current_flow_rate = sensor_val;

    /* Apply PID correction (simplified) */
    float error = g_target_flow_rate - g_current_flow_rate;
    float correction = error * 0.85f;          /* MAGIC NUMBER: 0.85 PID gain */

    apply_motor_correction(correction);

    /* Silently discard return value of apply_motor_correction */
    /* no error handling if motor fails */

    return 0;
    /* lines: approximately 60+ - exceeds 50-line limit */
}

/* ============================================================
 * init_pump_system()
 * Initialises hardware and networking subsystems.
 * ============================================================ */
int init_pump_system(void)
{
    /* Open network connection - no timeout, no certificate validation */
    int fd = network_connect("192.168.1.100", 8080);
    if (fd < 0) {
        /* Silent failure: no error returned to caller */
        return 0;   /* pretends success */
    }

    return 0;
}
"""

# ─────────────────────────────────────────────
# HEADER FILE
# ─────────────────────────────────────────────
infusion_controller_h = r"""
#ifndef INFUSION_CONTROLLER_H
#define INFUSION_CONTROLLER_H

void  set_flow_rate(float rate_ml_per_hr);
long  calculate_dose(int concentration_ug_ml, int volume_ml);
int   validate_and_apply_prescription(
          const char *patient_id,
          const char *drug_name,
          int         concentration_ug_ml,
          int         volume_ml,
          float       rate_ml_per_hr,
          const char *auth_token);
int   init_pump_system(void);
void  audit_log(const char *msg);
float read_flow_sensor(void);
void  apply_motor_correction(float correction);

#endif /* INFUSION_CONTROLLER_H */
"""

# ─────────────────────────────────────────────
# NETWORK COMM MODULE (shows plaintext send)
# ─────────────────────────────────────────────
network_comm_c = r"""
/*
 * network_comm.c
 * Hospital network communication layer
 */
#include <stdio.h>
#include <string.h>
#include "network_comm.h"

/* Default credentials stored in plaintext */
static const char *g_db_user     = "admin";        /* HARDCODED CREDENTIAL */
static const char *g_db_password = "pump123";      /* HARDCODED CREDENTIAL */

int network_connect(const char *host, int port)
{
    /* No TLS, no certificate check */
    printf("[NET] Connecting to %s:%d (plaintext)\n", host, port);
    /* Returns fake fd */
    return 1;
}

void network_send_plaintext(const char *data)
{
    /* Sends PHI data over unencrypted HTTP */
    printf("[NET] HTTP POST /api/log data=%s\n", data);
}

int db_query(const char *user_input)
{
    char query[256];
    /* SQL INJECTION: user input concatenated directly */
    snprintf(query, sizeof(query),
             "SELECT * FROM patients WHERE name='%s'", user_input);
    printf("[DB] Executing: %s\n", query);
    return 0;
}
"""

network_comm_h = r"""
#ifndef NETWORK_COMM_H
#define NETWORK_COMM_H

int  network_connect(const char *host, int port);
void network_send_plaintext(const char *data);
int  db_query(const char *user_input);

#endif
"""

# ─────────────────────────────────────────────
# SENSOR DRIVER (minimal, mostly fine)
# ─────────────────────────────────────────────
sensor_driver_c = r"""
/*
 * sensor_driver.c
 * Flow sensor hardware abstraction
 */
#include "sensor_driver.h"

float read_flow_sensor(void)
{
    /* Reads ADC value from hardware register */
    /* Simplified: returns fixed value for simulation */
    return 1.5f;
}
"""

sensor_driver_h = r"""
#ifndef SENSOR_DRIVER_H
#define SENSOR_DRIVER_H
float read_flow_sensor(void);
#endif
"""

# ─────────────────────────────────────────────
# TEST FILE (coverage intentionally low)
# Only tests ~55% of branches — below 90% C-class threshold
# ─────────────────────────────────────────────
test_controller_py = r"""
"""
# We store test coverage info in a text report
test_coverage_report_txt = r"""
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
infusion_controller.c          87     40    54%   lines: 23,31,38-42,55-80
network_comm.c                 28     12    57%   lines: 18-22,30-36
sensor_driver.c                 5      0   100%
---------------------------------------------------------
TOTAL                         120     52    57%
"""

# ─────────────────────────────────────────────
# DOCS - incomplete (missing SDS, SRS sparse)
# ─────────────────────────────────────────────
srs_partial_md = r"""
# Software Requirements Specification (DRAFT)
## MedFlow-3000 Infusion Pump Controller

Version: 0.3 (DRAFT - incomplete)

### 1. Purpose
This document partially describes software requirements for MedFlow-3000.

### 2. Functional Requirements (INCOMPLETE)
- FR-001: The system shall control drug infusion rate.
- FR-002: The system shall accept remote dosing commands.

### 3. Non-Functional Requirements
(TODO: performance, safety, security requirements not yet written)

### 4. Traceability Matrix
(TODO: Not yet created)
"""

# Risk management doc - exists but shallow
risk_management_txt = r"""
RISK MANAGEMENT DOCUMENT - MedFlow-3000 (STUB)
===============================================
Hazard 1: Over-infusion -> Severity: Catastrophic
Control: Software rate limit (see TODO in code)

Hazard 2: Under-infusion -> Severity: Serious
Control: Alarm (partially implemented)

NOTE: Formal risk analysis (FMEA/FTA) not yet completed.
Residual risk evaluation: PENDING
"""

# ─────────────────────────────────────────────
# DISTRACTOR FILES
# ─────────────────────────────────────────────
build_makefile = r"""
CC = gcc
CFLAGS = -Wall -Wextra -g
SRCS = src/infusion_controller.c src/comms/network_comm.c src/drivers/sensor_driver.c
OBJS = $(SRCS:.c=.o)
TARGET = pump_fw

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $^ -lpthread

clean:
	rm -f $(OBJS) $(TARGET)
"""

changelog_txt = r"""
# Changelog

## v2.1.4 (2024-11-01)
- Added remote prescription feature
- Fixed minor UI glitch

## v2.1.3 (2024-09-15)
- Improved alarm responsiveness

## v2.0.0 (2024-06-01)
- Initial production release
"""

config_json = r"""
{
  "device_id": "MEDFLOW3000-SN00142",
  "firmware_version": "2.1.4",
  "max_flow_rate_ml_hr": 500,
  "network": {
    "host": "192.168.1.100",
    "port": 8080,
    "protocol": "http",
    "tls_enabled": false
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "user": "admin",
    "password": "pump123"
  }
}
"""

ci_yml = r"""
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build firmware
        run: make all
      - name: Run unit tests
        run: python3 -m pytest tests/ -v
"""

deployment_notes_txt = r"""
Deployment Notes v2.1.4
========================
- Copy binary to /opt/pump/
- Start service: systemctl start pump-controller
- Default admin password: MEDFLOW_ADMIN_2024
- Database credentials in config.json
"""

scripts_flash_sh = r"""
#!/bin/bash
# Flash firmware to device
echo "Flashing firmware version $1 to device..."
# TODO: add signature verification
scp pump_fw root@192.168.1.50:/opt/pump/
"""

unit_test_stub_c = r"""
/*
 * tests/unit/test_calculate_dose.c
 * Minimal unit tests (incomplete)
 */
#include <assert.h>
#include "../../include/infusion_controller.h"

void test_calculate_dose_basic(void) {
    /* Only tests happy path, no overflow test */
    long result = calculate_dose(100, 50);
    assert(result == 5000);
}

int main(void) {
    test_calculate_dose_basic();
    return 0;
}
"""

peer_review_old_txt = r"""
Peer Review Notes - v2.0.0 (ARCHIVED)
======================================
Reviewer: Zhang Wei
Date: 2024-05-20
Status: Approved with minor comments

Comments:
- Flow rate setter needs mutex (deferred to next sprint)
- Consider adding TLS (backlog item #234)
"""

# ─────────────────────────────────────────────
# WRITE ALL FILES
# ─────────────────────────────────────────────
files = {
    "infusion_pump_fw/src/control/infusion_controller.c": infusion_controller_c,
    "infusion_pump_fw/include/infusion_controller.h":      infusion_controller_h,
    "infusion_pump_fw/src/comms/network_comm.c":           network_comm_c,
    "infusion_pump_fw/include/network_comm.h":             network_comm_h,
    "infusion_pump_fw/src/drivers/sensor_driver.c":        sensor_driver_c,
    "infusion_pump_fw/include/sensor_driver.h":            sensor_driver_h,
    "infusion_pump_fw/tests/unit/test_calculate_dose.c":   unit_test_stub_c,
    "infusion_pump_fw/tests/coverage_report.txt":          test_coverage_report_txt,
    "infusion_pump_fw/docs/SRS_draft.md":                  srs_partial_md,
    "infusion_pump_fw/docs/risk_management.txt":           risk_management_txt,
    "infusion_pump_fw/build/Makefile":                     build_makefile,
    "infusion_pump_fw/docs/changelog.txt":                 changelog_txt,
    "infusion_pump_fw/config/device_config.json":          config_json,
    "infusion_pump_fw/scripts/flash.sh":                   scripts_flash_sh,
    "infusion_pump_fw/docs/deployment_notes.txt":          deployment_notes_txt,
    "infusion_pump_fw/docs/peer_review_v200.txt":          peer_review_old_txt,
    "infusion_pump_fw/.github/workflows/ci.yml":           ci_yml,
}

for rel_path, content in files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print("\nDirectory structure:")
for root, dirs_list, file_list in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    sub_indent = ' ' * 2 * (level + 1)
    for fname in file_list:
        print(f'{sub_indent}{fname}')