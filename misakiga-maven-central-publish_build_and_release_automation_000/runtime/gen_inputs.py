#!/usr/bin/env python3
"""
Generates a realistic, messy sandbox workspace for the Maven Central publishing task.
The workspace contains a partially broken Java project skeleton with distractor files.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Project structure
# ─────────────────────────────────────────────
project_root = WORKSPACE / "currencykit-sdk"
src_main = project_root / "src" / "main" / "java" / "io" / "github" / "fintechoss" / "currencykit"
src_test = project_root / "src" / "test" / "java" / "io" / "github" / "fintechoss" / "currencykit"
resources = project_root / "src" / "main" / "resources"
docs_dir = project_root / "docs"
scripts_dir = project_root / "scripts"
ci_dir = project_root / ".github" / "workflows"
notes_dir = project_root / "notes"

for d in [src_main, src_test, resources, docs_dir, scripts_dir, ci_dir, notes_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 2. Java source files (realistic content)
# ─────────────────────────────────────────────
(src_main / "CurrencyConverter.java").write_text("""package io.github.fintechoss.currencykit;

/**
 * Converts between currency pairs using real-time rates.
 */
public class CurrencyConverter {
    private final RateProvider provider;

    public CurrencyConverter(RateProvider provider) {
        this.provider = provider;
    }

    /**
     * Converts an amount from one currency to another.
     * @param amount the amount to convert
     * @param from source currency code
     * @param to target currency code
     * @return converted amount
     */
    public double convert(double amount, String from, String to) {
        double rate = provider.getRate(from, to);
        return amount * rate;
    }
}
""")

(src_main / "RateProvider.java").write_text("""package io.github.fintechoss.currencykit;

/**
 * Interface for rate data sources.
 */
public interface RateProvider {
    double getRate(String from, String to);
}
""")

(src_main / "StaticRateProvider.java").write_text("""package io.github.fintechoss.currencykit;

import java.util.Map;
import java.util.HashMap;

/**
 * A static, fixed-rate provider for testing purposes.
 */
public class StaticRateProvider implements RateProvider {
    private final Map<String, Double> rates = new HashMap<>();

    public StaticRateProvider() {
        rates.put("USD-EUR", 0.92);
        rates.put("USD-GBP", 0.79);
        rates.put("EUR-USD", 1.09);
    }

    @Override
    public double getRate(String from, String to) {
        String key = from + "-" + to;
        return rates.getOrDefault(key, 1.0);
    }
}
""")

(src_main / "CurrencyKitException.java").write_text("""package io.github.fintechoss.currencykit;

public class CurrencyKitException extends RuntimeException {
    public CurrencyKitException(String message) {
        super(message);
    }
    public CurrencyKitException(String message, Throwable cause) {
        super(message, cause);
    }
}
""")

(src_test / "CurrencyConverterTest.java").write_text("""package io.github.fintechoss.currencykit;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class CurrencyConverterTest {
    @Test
    public void testUsdToEur() {
        StaticRateProvider provider = new StaticRateProvider();
        CurrencyConverter converter = new CurrencyConverter(provider);
        double result = converter.convert(100.0, "USD", "EUR");
        assertEquals(92.0, result, 0.001);
    }
}
""")

(resources / "currencykit.properties").write_text("""# CurrencyKit SDK Properties
version=1.2.0
default.currency=USD
""")

# ─────────────────────────────────────────────
# 3. BROKEN / INCOMPLETE pom.xml (the primary problem file)
# ─────────────────────────────────────────────
# Missing: proper metadata, wrong plugin versions, missing plugins,
# wrong server ID hints, no release profile, no signing config
broken_pom = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>io.github.fintechoss</groupId>
    <artifactId>currencykit-sdk</artifactId>
    <version>1.2.0</version>
    <packaging>jar</packaging>

    <!-- TODO: Add required metadata for central publishing -->
    <!-- name, description, url are missing -->

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
            <!-- MISSING: source, javadoc, gpg, and central publishing plugins -->
        </plugins>
    </build>

</project>
"""
(project_root / "pom.xml").write_text(broken_pom)

# ─────────────────────────────────────────────
# 4. Distractor / legacy files
# ─────────────────────────────────────────────
(docs_dir / "ARCHITECTURE.md").write_text("""# CurrencyKit Architecture

## Modules
- `currencykit-sdk`: Core conversion logic
- Future: `currencykit-spring`: Spring Boot auto-configuration

## Design Principles
- Immutability first
- Provider-pattern for rate sources
""")

(docs_dir / "CHANGELOG.md").write_text("""# Changelog

## 1.2.0
- Add StaticRateProvider
- Improve error messages

## 1.1.0
- Initial public release
""")

(scripts_dir / "build.sh").write_text("""#!/bin/bash
# Legacy build script - do not use for publishing
mvn clean package
""")

(scripts_dir / "test.sh").write_text("""#!/bin/bash
mvn test
""")

(ci_dir / "ci.yml").write_text("""name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: mvn clean test
""")

# A red-herring old-style sonatype settings snippet (wrong approach)
(project_root / "legacy-settings-example.xml").write_text("""<!-- OLD OSSRH style - DO NOT USE for new projects -->
<!-- This is for the deprecated oss.sonatype.org workflow -->
<settings>
  <servers>
    <server>
      <id>ossrh</id>
      <username>old_user</username>
      <password>old_pass</password>
    </server>
  </servers>
  <profiles>
    <profile>
      <id>ossrh</id>
      <activation><activeByDefault>true</activeByDefault></activation>
      <properties>
        <gpg.executable>gpg</gpg.executable>
        <gpg.passphrase>changeme</gpg.passphrase>
      </properties>
    </profile>
  </profiles>
</settings>
""")

# Wrong/old plugin reference as a distractor note
(notes_dir / "old-deploy-notes.txt").write_text("""Old deployment used:
  groupId: org.sonatype.plugins
  artifactId: nexus-staging-maven-plugin

This is DEPRECATED. The new portal uses a different plugin.
Ask the team lead for the correct coordinates.
""")

# A partial, wrong settings.xml in the project (not ~/.m2/)
(project_root / "settings-template.xml").write_text("""<!-- Fill this in and copy to ~/.m2/settings.xml -->
<settings>
  <servers>
    <server>
      <id>PLACEHOLDER_SERVER_ID</id>
      <username>YOUR_TOKEN_USER</username>
      <password>YOUR_TOKEN_PASS</password>
    </server>
  </servers>
</settings>
""")

# Misc distractor files
(WORKSPACE / "scratch.txt").write_text("random notes from sprint planning\n- finish SDK\n- publish to maven\n- update docs\n")
(WORKSPACE / "env-notes.json").write_text(json.dumps({
    "java_version": "17",
    "gpg_note": "need to configure properly for headless CI",
    "status": "in-progress"
}, indent=2))
(WORKSPACE / "todo.md").write_text("""# TODOs
- [ ] Fix pom.xml for central publishing
- [ ] Set up GPG signing
- [ ] Configure maven settings
- [ ] Get namespace approved: io.github.fintechoss
""")

print("Workspace generated successfully.")
print(f"Project root: {project_root}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")