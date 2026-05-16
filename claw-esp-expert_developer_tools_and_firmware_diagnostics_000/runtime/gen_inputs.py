#!/usr/bin/env python3
"""
Generate the sandbox workspace for the ESP-IDF GPIO audit + partition overflow task.
"""
import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Create the mock ESP-IDF tree (distractor + useful)
# ─────────────────────────────────────────────
IDF_PATH = WORKSPACE / "esp-idf"

examples_dirs = [
    "peripherals/gpio/generic_gpio",
    "peripherals/gpio/matrix_keyboard",
    "peripherals/uart/uart_echo",
    "peripherals/i2c/i2c_simple",
    "peripherals/spi_master/lcd",
    "wifi/getting_started/station",
    "bluetooth/bluedroid/ble/gatt_server",
    "storage/nvs_rw_value",
    "system/heap_task_tracking",
    "protocols/mqtt/tcp",
]

for d in examples_dirs:
    p = IDF_PATH / "examples" / d
    p.mkdir(parents=True, exist_ok=True)

# GPIO generic_gpio README
gpio_readme = textwrap.dedent("""\
# Generic GPIO Example

This example demonstrates basic GPIO usage on ESP32 series chips.

## Hardware Required

- Any ESP32 devkit board
- LED connected to GPIO 5 (output)
- Button connected to GPIO 9 (input, active low)
- 330 Ohm resistor

## How to use

```
idf.py set-target esp32c6
idf.py build
idf.py flash monitor
```

## Structure

- `main/gpio_example_main.c` — main application
- `CMakeLists.txt` — build system entry

## Supported Targets

esp32, esp32s3, esp32c3, esp32c6
""")
(IDF_PATH / "examples/peripherals/gpio/generic_gpio/README.md").write_text(gpio_readme)

# GPIO matrix_keyboard README
(IDF_PATH / "examples/peripherals/gpio/matrix_keyboard/README.md").write_text(
    "# Matrix Keyboard\nDemonstrates scanning a 4x4 key matrix via GPIO interrupts.\n"
    "## Hardware\n- 8 GPIO pins total\n- Pull-up resistors required\n"
)

# Distractor READMEs
(IDF_PATH / "examples/peripherals/uart/uart_echo/README.md").write_text(
    "# UART Echo Example\nEchoes data received on UART0.\n"
)
(IDF_PATH / "examples/wifi/getting_started/station/README.md").write_text(
    "# WiFi Station Example\nConnects to an AP and pings the gateway.\n"
)

# Fake idf_component_manager data
(IDF_PATH / "examples/storage/nvs_rw_value/README.md").write_text(
    "# NVS Read/Write\nStores and retrieves values from NVS flash.\n"
)

# ─────────────────────────────────────────────
# 2. Create the mock tool runner: scripts/run-tool.mjs
# ─────────────────────────────────────────────
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)

run_tool_mjs = r"""#!/usr/bin/env node
/**
 * Mock run-tool.mjs for claw-esp-expert skill evaluation.
 * Reads tool name from argv[2], reads JSON from stdin when --stdin is passed.
 */
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const toolName = process.argv[2];
const useStdin = process.argv.includes('--stdin');

async function readStdin() {
  return new Promise((resolve) => {
    const chunks = [];
    process.stdin.on('data', d => chunks.push(d));
    process.stdin.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  });
}

async function main() {
  let inputJson = {};
  if (useStdin) {
    const raw = await readStdin();
    try { inputJson = JSON.parse(raw); } catch(e) {
      process.stderr.write('Invalid JSON on stdin: ' + raw + '\n');
      process.exit(1);
    }
  }

  const IDF_PATH = process.env.IDF_PATH || '/workspace/esp-idf';

  switch(toolName) {

    case 'manage_env': {
      const action = inputJson.action || 'check';
      if (action === 'check') {
        const result = {
          tool: 'manage_env',
          action: 'check',
          idf_path: IDF_PATH,
          idf_path_status: 'FOUND',
          idf_py: '/workspace/bin/idf.py',
          idf_py_status: 'FOUND',
          python: '/usr/bin/python3',
          python_status: 'FOUND',
          summary: 'ESP-IDF environment is available.'
        };
        process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      } else if (action === 'install') {
        process.stdout.write(JSON.stringify({
          tool: 'manage_env',
          action: 'install',
          guidance: 'Run: git clone --recursive https://github.com/espressif/esp-idf.git && cd esp-idf && ./install.sh'
        }, null, 2) + '\n');
      }
      break;
    }

    case 'explore_demo': {
      const query = (inputJson.query || '').toLowerCase();
      const idfExamples = path.join(IDF_PATH, 'examples');

      // Find matching demos by keyword scan
      let matches = [];
      function walk(dir) {
        if (!fs.existsSync(dir)) return;
        for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
          const full = path.join(dir, entry.name);
          if (entry.isDirectory()) walk(full);
          else if (entry.name === 'README.md' || entry.name === 'README_CN.md') {
            const rel = path.relative(idfExamples, path.dirname(full));
            const content = fs.readFileSync(full, 'utf8');
            if (rel.toLowerCase().includes(query) || content.toLowerCase().includes(query)) {
              matches.push({ path: path.dirname(full), readme: full, content });
            }
          }
        }
      }
      walk(idfExamples);

      if (matches.length === 0) {
        process.stdout.write(JSON.stringify({ tool: 'explore_demo', query, matches: [] }, null, 2) + '\n');
        break;
      }

      // Best match: first result
      const best = matches[0];
      const readmeContent = best.content;
      // Extract hardware section
      const hwMatch = readmeContent.match(/## Hardware[^\n]*\n([\s\S]*?)(?=\n##|$)/);
      const hwSection = hwMatch ? hwMatch[1].trim() : 'See README for hardware details.';

      const result = {
        tool: 'explore_demo',
        query,
        total_matches: matches.length,
        best_match: {
          path: best.path,
          readme: best.readme,
          summary: readmeContent.split('\n').slice(0,4).join('\n'),
          hardware_requirements: hwSection,
          structure: ['main/', 'CMakeLists.txt', 'README.md']
        },
        all_matches: matches.map(m => m.path)
      };
      process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      break;
    }

    case 'safe_build': {
      const projectPath = inputJson.projectPath || '/workspace/sensor_project';
      const chip = (inputJson.chip || 'esp32').toLowerCase();

      // Normalize SKU names
      const chipNormMap = {
        'esp32-c6fh4': 'esp32c6', 'esp32-s3-pico-1-n8r2': 'esp32s3',
        'esp32c6fh4': 'esp32c6', 'esp32s3pico': 'esp32s3'
      };
      const normalizedChip = chipNormMap[chip] || chip;

      // Read source files for GPIO audit
      let auditFindings = [];
      let buildStatus = 'SUCCESS';
      let buildLog = '';
      let partitionOverflow = null;

      const mainC = path.join(projectPath, 'main', 'sensor_main.c');
      if (fs.existsSync(mainC)) {
        const src = fs.readFileSync(mainC, 'utf8');
        // Check for strapping pin conflicts (esp32c6: GPIO 8, 9 are strapping pins)
        const strapPins = { esp32c6: [8, 9], esp32: [0, 2, 5, 12, 15], esp32s3: [0, 3, 45, 46] };
        const forbidden = strapPins[normalizedChip] || [];
        const pinPattern = /gpio_num_t\s+\w+\s*=\s*(\d+)|GPIO_NUM_(\d+)|#define\s+\w+_PIN\s+(\d+)/g;
        let m;
        while ((m = pinPattern.exec(src)) !== null) {
          const pinNum = parseInt(m[1] || m[2] || m[3]);
          if (forbidden.includes(pinNum)) {
            auditFindings.push({
              severity: 'FATAL',
              pin: pinNum,
              reason: `GPIO ${pinNum} is a strapping pin on ${normalizedChip} and must not be used as application GPIO`,
              file: mainC,
              line: src.substring(0, m.index).split('\n').length,
              evidence: m[0].trim()
            });
            buildStatus = 'AUDIT_REJECTED';
          }
        }
      }

      // Check partitions.csv for overflow simulation
      const partCsv = path.join(projectPath, 'partitions.csv');
      if (fs.existsSync(partCsv)) {
        // Simulate overflow: factory partition is too small
        buildLog = [
          'Configuring done',
          'Generating done',
          `-- IDF_TARGET: ${normalizedChip}`,
          'Compiling sensor_main.c...',
          'Linking sensor_project.elf...',
          'sensor_project.elf: section .flash.text is too large for partition factory',
          `FAILED: partition 'factory' overflow by 0x14000 bytes (app binary 0x1b4000, partition size 0x1a0000)`,
          'ninja: build stopped: subcommand failed.',
        ].join('\n');
        partitionOverflow = {
          partition: 'factory',
          overflow_bytes: '0x14000',
          app_binary_size: '0x1b4000',
          partition_size: '0x1a0000'
        };
        if (buildStatus !== 'AUDIT_REJECTED') buildStatus = 'BUILD_FAILED';
      }

      const result = {
        tool: 'safe_build',
        projectPath,
        chip: normalizedChip,
        audit: {
          status: auditFindings.length > 0 ? 'FAILED' : 'PASSED',
          findings: auditFindings,
          fatal_count: auditFindings.filter(f => f.severity === 'FATAL').length
        },
        build: {
          status: buildStatus,
          log: buildLog,
          partition_overflow: partitionOverflow,
          errors: buildStatus === 'AUDIT_REJECTED'
            ? ['Build aborted: GPIO audit found FATAL pin conflicts. Fix pin assignments before building.']
            : ['Partition overflow detected in factory partition']
        }
      };
      process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      break;
    }

    case 'analyze_partitions': {
      const projectPath = inputJson.projectPath || '/workspace/sensor_project';
      const rawLog = inputJson.rawLog || '';

      const partCsv = path.join(projectPath, 'partitions.csv');
      let csvContent = '';
      if (fs.existsSync(partCsv)) {
        csvContent = fs.readFileSync(partCsv, 'utf8');
      }

      // Parse overflow from log
      const overflowMatch = rawLog.match(/partition '(\w+)' overflow by (0x[0-9a-fA-F]+)/i)
        || rawLog.match(/partition[:\s]+(\w+)[^\n]*overflow[^\n]*(0x[0-9a-fA-F]+)/i);

      const partName = overflowMatch ? overflowMatch[1] : 'factory';
      const overflowHex = overflowMatch ? overflowMatch[2] : '0x14000';
      const overflowBytes = parseInt(overflowHex, 16);

      // Current size from CSV
      const currentSizeMatch = csvContent.match(/factory[^,]*,[^,]*,\s*(0x[0-9a-fA-F]+)/i);
      const currentSize = currentSizeMatch ? parseInt(currentSizeMatch[1], 16) : 0x1a0000;
      const recommendedSize = currentSize + overflowBytes + 0x10000; // add 64KB buffer
      const recHex = '0x' + recommendedSize.toString(16).toUpperCase();

      // Build before/after patch
      const beforeLine = csvContent.split('\n').find(l => l.toLowerCase().includes('factory')) || '';
      const afterLine = beforeLine.replace(
        /0x[0-9a-fA-F]+(\s*)$/i,
        recHex + '$1'
      );

      const result = {
        tool: 'analyze_partitions',
        projectPath,
        detected_app_partition: partName,
        overflow: {
          partition: partName,
          overflow_hex: overflowHex,
          current_size_hex: '0x' + currentSize.toString(16).toUpperCase(),
          recommended_size_hex: recHex
        },
        patch: {
          before: beforeLine.trim(),
          after: afterLine.trim(),
          csv_draft: csvContent.replace(beforeLine, afterLine)
        },
        instructions: `Update partitions.csv: change the '${partName}' partition size from ${'0x' + currentSize.toString(16).toUpperCase()} to ${recHex}. Then rebuild.`
      };
      process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      break;
    }

    case 'resolve_component': {
      const query = inputJson.query || '';
      const target = inputJson.target || 'esp32';
      const result = {
        tool: 'resolve_component',
        query,
        target,
        best_match: {
          name: 'espressif/' + query.replace(/[^a-z0-9_]/gi,'_'),
          version: '^1.0.0',
          registry_url: 'https://components.espressif.com/components/espressif/' + query,
          supported_targets: [target],
          docs: 'https://components.espressif.com/components/espressif/' + query
        },
        idf_component_yml_snippet: `dependencies:\n  espressif/${query}: "^1.0.0"\n`,
        patch: {
          before: '# no existing idf_component.yml',
          after: `dependencies:\n  espressif/${query}: "^1.0.0"\n`
        }
      };
      process.stdout.write(JSON.stringify(result, null, 2) + '\n');
      break;
    }

    default: {
      process.stderr.write(`Unknown tool: ${toolName}\n`);
      process.exit(1);
    }
  }
}

main().catch(e => { process.stderr.write(e.stack + '\n'); process.exit(1); });
"""

(scripts_dir / "run-tool.mjs").write_text(run_tool_mjs)

# ─────────────────────────────────────────────
# 3. Create the sensor project with intentional issues
# ─────────────────────────────────────────────
project_dir = WORKSPACE / "sensor_project"
(project_dir / "main").mkdir(parents=True, exist_ok=True)
(project_dir / "components" / "sensor_driver").mkdir(parents=True, exist_ok=True)

# Main C file — uses GPIO 9 (strapping pin on esp32c6) and GPIO 5
sensor_main_c = textwrap.dedent("""\
    #include <stdio.h>
    #include "driver/gpio.h"
    #include "freertos/FreeRTOS.h"
    #include "freertos/task.h"

    /* Sensor output data pin */
    #define DATA_OUT_PIN   5
    /* Status LED */
    #define STATUS_LED_PIN 9

    /* Trigger pin via gpio_num_t alias */
    static const gpio_num_t TRIGGER_PIN = GPIO_NUM_8;

    void configure_gpio(void) {
        gpio_config_t io_conf = {
            .pin_bit_mask = (1ULL << DATA_OUT_PIN) | (1ULL << STATUS_LED_PIN) | (1ULL << TRIGGER_PIN),
            .mode = GPIO_MODE_OUTPUT,
            .pull_up_en = 0,
            .pull_down_en = 0,
            .intr_type = GPIO_INTR_DISABLE,
        };
        gpio_config(&io_conf);
    }

    void sensor_task(void *arg) {
        configure_gpio();
        while (1) {
            gpio_set_level(DATA_OUT_PIN, 1);
            gpio_set_level(STATUS_LED_PIN, 0);
            gpio_set_level(TRIGGER_PIN, 1);
            vTaskDelay(pdMS_TO_TICKS(500));
            gpio_set_level(DATA_OUT_PIN, 0);
            gpio_set_level(STATUS_LED_PIN, 1);
            gpio_set_level(TRIGGER_PIN, 0);
            vTaskDelay(pdMS_TO_TICKS(500));
        }
    }

    void app_main(void) {
        xTaskCreate(sensor_task, "sensor_task", 4096, NULL, 5, NULL);
    }
""")
(project_dir / "main" / "sensor_main.c").write_text(sensor_main_c)

# CMakeLists.txt files
(project_dir / "CMakeLists.txt").write_text(textwrap.dedent("""\
    cmake_minimum_required(VERSION 3.16)
    include($ENV{IDF_PATH}/tools/cmake/project.cmake)
    project(sensor_project)
"""))
(project_dir / "main" / "CMakeLists.txt").write_text(textwrap.dedent("""\
    idf_component_register(SRCS "sensor_main.c"
                           INCLUDE_DIRS ".")
"""))

# partitions.csv — factory partition intentionally too small
partitions_csv = textwrap.dedent("""\
    # Name,   Type, SubType,  Offset,   Size,    Flags
    nvs,      data, nvs,      0x9000,   0x6000,
    phy_init, data, phy,      0xf000,   0x1000,
    factory,  app,  factory,  0x10000,  0x1A0000,
    storage,  data, spiffs,   0x1B0000, 0x50000,
""")
(project_dir / "partitions.csv").write_text(partitions_csv)

# sdkconfig stub
(project_dir / "sdkconfig").write_text(textwrap.dedent("""\
    CONFIG_IDF_TARGET="esp32c6"
    CONFIG_PARTITION_TABLE_CUSTOM=y
    CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"
    CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y
"""))

# Distractor files
(project_dir / "components" / "sensor_driver" / "sensor_driver.h").write_text(
    "#pragma once\nvoid sensor_init(void);\nfloat sensor_read_temp(void);\n"
)
(project_dir / "components" / "sensor_driver" / "sensor_driver.c").write_text(
    '#include "sensor_driver.h"\nvoid sensor_init(void){}\nfloat sensor_read_temp(void){return 25.0f;}\n'
)
(project_dir / "components" / "sensor_driver" / "CMakeLists.txt").write_text(
    'idf_component_register(SRCS "sensor_driver.c" INCLUDE_DIRS ".")\n'
)

# Old build artifacts (distractors)
build_dir = project_dir / "build"
build_dir.mkdir(exist_ok=True)
(build_dir / "compile_commands.json").write_text("[]")
(build_dir / "CMakeCache.txt").write_text("CMAKE_BUILD_TYPE:STRING=Release\n")
(build_dir / "sensor_project.map").write_text("# Linker map placeholder\n")

# Extra distractor: a stale notes file
(project_dir / "NOTES.txt").write_text(textwrap.dedent("""\
    Module: ESP32-C6FH4
    Flash: 4MB
    RAM: 512KB SRAM
    Target market: industrial sensor nodes
    TODO: check pin assignments for production PCB
    TODO: partition table needs review after binary grew
"""))

# ─────────────────────────────────────────────
# 4. Create dist/index.js stub (referenced by SKILL.md)
# ─────────────────────────────────────────────
dist_dir = WORKSPACE / "dist" / "data" / "soc"
dist_dir.mkdir(parents=True, exist_ok=True)

soc_esp32c6 = {
    "chip": "esp32c6",
    "strapping_pins": [8, 9],
    "forbidden_pins": [8, 9],
    "uart_pins": [16, 17],
    "max_gpio": 30
}
(dist_dir / "esp32c6.json").write_text(json.dumps(soc_esp32c6, indent=2))

soc_esp32 = {
    "chip": "esp32",
    "strapping_pins": [0, 2, 5, 12, 15],
    "forbidden_pins": [6, 7, 8, 9, 10, 11],
    "uart_pins": [1, 3],
    "max_gpio": 39
}
(dist_dir / "esp32.json").write_text(json.dumps(soc_esp32, indent=2))

(WORKSPACE / "dist" / "index.js").write_text(
    "// Bundled runtime entry — see scripts/run-tool.mjs for CLI dispatch\n"
)

# ─────────────────────────────────────────────
# 5. Create a mock idf.py in a local bin
# ─────────────────────────────────────────────
bin_dir = WORKSPACE / "bin"
bin_dir.mkdir(exist_ok=True)
idf_py_mock = textwrap.dedent("""\
    #!/usr/bin/env python3
    import sys
    print(f"[mock idf.py] called with: {' '.join(sys.argv[1:])}")
    print("ESP-IDF v5.2.0-mock")
    sys.exit(0)
""")
(bin_dir / "idf.py").write_text(idf_py_mock)

print("Workspace generated successfully.")
print(f"  ESP-IDF mock: {IDF_PATH}")
print(f"  Project: {project_dir}")
print(f"  Tool runner: {scripts_dir / 'run-tool.mjs'}")