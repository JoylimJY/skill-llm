# syntax=docker/dockerfile:1
FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pathlib2 -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the flutter-schema scripts directory and the validate.py script
RUN mkdir -p /root/flutter-schema/scripts

RUN cat > /root/flutter-schema/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
"""
Validates the Flutter GetX architecture of the workspace.
"""
import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Validate Flutter GetX project structure.")
    parser.add_argument("--workspace", default="/workspace", help="Path to the workspace root.")
    parser.add_argument("--help-extra", action="store_true", help="Show extra help.")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    errors = []
    warnings = []

    lib = workspace / "lib"
    if not lib.exists():
        errors.append("Missing lib/ directory.")

    modules = lib / "modules"
    if modules.exists():
        for module_dir in modules.iterdir():
            if not module_dir.is_dir():
                continue
            name = module_dir.name
            # Check snake_case
            if name != name.lower().replace("-", "_"):
                errors.append(f"Module folder '{name}' is not snake_case.")
            # Check for logic files extending GetxController instead of BaseController
            for dart_file in module_dir.glob("*.dart"):
                content = dart_file.read_text()
                if "extends GetxController" in content:
                    errors.append(f"{dart_file.relative_to(workspace)}: Logic class extends GetxController instead of BaseController.")
                if "Widget extends GetView" in content or dart_file.stem.endswith("Widget"):
                    errors.append(f"{dart_file.relative_to(workspace)}: View class should end with 'Page' or 'View', not 'Widget'.")

    core = lib / "core"
    required_core_subdirs = ["config", "constants", "navigation", "services", "utils", "widgets"]
    for sub in required_core_subdirs:
        if not (core / sub).exists():
            errors.append(f"Missing core/{sub}/ directory.")

    shared = lib / "shared"
    required_shared_subdirs = [
        "data/base_business",
        "data/local",
        "data/download",
        "data/upload",
        "domain",
    ]
    for sub in required_shared_subdirs:
        if not (shared / sub).exists():
            errors.append(f"Missing shared/{sub}/ directory.")

    required_modules = ["shipment_tracking", "warehouse_inventory"]
    for mod in required_modules:
        if not (modules / mod).exists():
            errors.append(f"Missing modules/{mod}/ directory.")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  [ERROR] {e}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: All checks OK.")
        sys.exit(0)

if __name__ == "__main__":
    main()
EOF

RUN chmod +x /root/flutter-schema/scripts/validate.py

WORKDIR /workspace