import sys
import json
import importlib
import inspect
import subprocess
import ast
import time
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
lobster_root = workspace / "lobster"

checks = []

def check(name, fn):
    try:
        passed, detail = fn()
    except Exception as e:
        passed, detail = False, f"Exception: {e}"
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


# ── 1. Package directory structure ────────────────────────────────────────────

def check_package_structure():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    if not pkg.exists():
        return False, "packages/lobster-epigenomics/ directory missing"
    
    agent_dir = pkg / "lobster" / "agents" / "epigenomics"
    if not agent_dir.exists():
        return False, f"Agent dir missing: {agent_dir.relative_to(lobster_root)}"
    
    svc_dir = pkg / "lobster" / "services" / "epigenomics"
    if not svc_dir.exists():
        return False, f"Service dir missing: {svc_dir.relative_to(lobster_root)}"
    
    # No __init__.py at lobster/ level (PEP 420 namespace)
    lobster_init = pkg / "lobster" / "__init__.py"
    if lobster_init.exists():
        return False, "lobster/__init__.py must NOT exist (PEP 420 namespace package)"
    
    return True, "Package directory structure is correct"

check("package_structure", check_package_structure)


# ── 2. pyproject.toml correctness ─────────────────────────────────────────────

def check_pyproject():
    import tomllib
    pyproject = lobster_root / "packages" / "lobster-epigenomics" / "pyproject.toml"
    if not pyproject.exists():
        return False, "pyproject.toml missing"
    
    try:
        data = tomllib.loads(pyproject.read_text())
    except Exception as e:
        return False, f"Invalid TOML: {e}"
    
    # Check entry points group
    eps = data.get("project", {}).get("entry-points", {})
    lobster_ep_group = eps.get("lobster.agents", {})
    if not lobster_ep_group:
        return False, "Missing [project.entry-points.\"lobster.agents\"] section"
    
    # At least one entry point must exist pointing to epigenomics agent
    ep_values = list(lobster_ep_group.values())
    if not any("epigenomics" in v for v in ep_values):
        return False, f"Entry point must reference epigenomics agent module, got: {ep_values}"
    
    # Check namespace package config
    setuptools = data.get("tool", {}).get("setuptools", {})
    packages_find = setuptools.get("packages", {}).get("find", {})
    include = packages_find.get("include", [])
    namespaces = packages_find.get("namespaces", False)
    
    if not any("lobster" in i for i in include):
        return False, f"packages.find.include must contain 'lobster*', got: {include}"
    
    if namespaces is not True:
        return False, "packages.find.namespaces must be true (PEP 420 requirement)"
    
    return True, f"pyproject.toml valid with entry points: {lobster_ep_group}"

check("pyproject_toml", check_pyproject)


# ── 3. AGENT_CONFIG defined before heavy imports ───────────────────────────────

def check_agent_config_placement():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        return False, "No agent .py file found in lobster/agents/epigenomics/"
    
    agent_file = agent_files[0]
    source = agent_file.read_text()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error in agent file: {e}"
    
    # Find line of AGENT_CONFIG assignment
    agent_config_line = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "AGENT_CONFIG":
                    agent_config_line = node.lineno
                    break
    
    if agent_config_line is None:
        return False, "AGENT_CONFIG not found in agent file"
    
    # Find lines of heavy imports (anything other than lobster.config)
    heavy_import_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Consider imports of heavy libs as "heavy"
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                # Skip lobster.config imports (they are expected before AGENT_CONFIG)
                if module.startswith("lobster.config.agent_registry"):
                    continue
                heavy_import_lines.append((node.lineno, module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    heavy_import_lines.append((node.lineno, alias.name))
    
    # Check that heavy imports come AFTER AGENT_CONFIG
    before_config = [(line, mod) for line, mod in heavy_import_lines if line < agent_config_line]
    
    # Allow only lobster.config.agent_registry before AGENT_CONFIG
    truly_early = [(line, mod) for line, mod in before_config 
                   if not mod.startswith("lobster.config.agent_registry") 
                   and mod not in ("", "lobster.config.agent_registry")]
    
    if truly_early:
        return False, (f"AGENT_CONFIG at line {agent_config_line} but heavy imports appear "
                       f"before it at lines: {truly_early[:3]}")
    
    return True, f"AGENT_CONFIG correctly defined at line {agent_config_line} before heavy imports"

check("agent_config_placement", check_agent_config_placement)


# ── 4. AGENT_CONFIG fields and tier ───────────────────────────────────────────

def check_agent_config_fields():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        return False, "No agent file found"
    
    agent_file = agent_files[0]
    source = agent_file.read_text()
    
    # Check tier_requirement is "free"
    if 'tier_requirement="free"' not in source and "tier_requirement='free'" not in source:
        return False, "tier_requirement must be 'free' for official agents"
    
    # Check required fields are present
    required_fields = ["name=", "display_name=", "description=", "factory_function=",
                       "handoff_tool_name=", "handoff_tool_description="]
    missing = [f for f in required_fields if f not in source]
    if missing:
        return False, f"AGENT_CONFIG missing fields: {missing}"
    
    return True, "AGENT_CONFIG has all required fields with tier_requirement='free'"

check("agent_config_fields", check_agent_config_fields)


# ── 5. Factory function signature (delegation_tools, NOT handoff_tools) ────────

def check_factory_signature():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        return False, "No agent file found"
    
    agent_file = agent_files[0]
    source = agent_file.read_text()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    
    # Find factory function definitions (not AGENT_CONFIG, something callable)
    factory_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip private/dunder
            if not node.name.startswith("_"):
                factory_funcs.append(node)
    
    if not factory_funcs:
        return False, "No public factory function found in agent file"
    
    all_params = []
    for fn in factory_funcs:
        params = [arg.arg for arg in fn.args.args]
        params += [arg.arg for arg in fn.args.kwonlyargs]
        if fn.args.varkw:
            params.append("**kwargs")
        all_params.extend(params)
    
    # Must have delegation_tools
    if "delegation_tools" not in all_params:
        return False, f"Factory function missing 'delegation_tools' parameter. Found params: {all_params}"
    
    # Must NOT have handoff_tools (deprecated)
    if "handoff_tools" in all_params:
        return False, "Factory uses deprecated 'handoff_tools' - must use 'delegation_tools'"
    
    # Must have standard params
    required = ["data_manager", "callback_handler", "workspace_path"]
    missing = [p for p in required if p not in all_params]
    if missing:
        return False, f"Factory missing required params: {missing}"
    
    return True, f"Factory signature correct with delegation_tools and standard params"

check("factory_signature", check_factory_signature)


# ── 6. Service file exists and returns 3-tuple ────────────────────────────────

def check_service_structure():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    svc_dir = pkg / "lobster" / "services" / "epigenomics"
    
    svc_files = [f for f in svc_dir.glob("*.py") if f.name != "__init__.py"]
    if not svc_files:
        return False, "No service .py file found in services/epigenomics/"
    
    svc_file = svc_files[0]
    source = svc_file.read_text()
    
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error in service file: {e}"
    
    # Check AnalysisStep is imported
    if "AnalysisStep" not in source:
        return False, "Service must import and use AnalysisStep from lobster.core.provenance"
    
    # Check for 3-tuple return hint or Tuple in return annotation
    if "Tuple" not in source and "tuple" not in source.lower():
        # Be lenient - check for 3 returns in analyze method
        pass
    
    # Check there's a class with an analyze method
    classes_with_analyze = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [m.name for m in ast.walk(node) if isinstance(m, ast.FunctionDef)]
            if "analyze" in methods:
                classes_with_analyze.append(node.name)
    
    if not classes_with_analyze:
        return False, "Service must define a class with an 'analyze' method"
    
    # Check the analyze method returns a 3-tuple (look for return with tuple)
    has_triple_return = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 3:
                has_triple_return = True
                break
    
    if not has_triple_return:
        return False, (f"Service analyze method must return a 3-tuple (AnnData, Dict, AnalysisStep). "
                       f"No 3-element return tuple found.")
    
    return True, f"Service class(es) {classes_with_analyze} found with proper 3-tuple return"

check("service_3tuple", check_service_structure)


# ── 7. log_tool_usage called with ir=ir ───────────────────────────────────────

def check_log_tool_usage_ir():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        return False, "No agent file found"
    
    agent_file = agent_files[0]
    source = agent_file.read_text()
    
    # Check log_tool_usage is called with ir= keyword
    if "log_tool_usage" not in source:
        return False, "log_tool_usage not called in agent file"
    
    # Parse and look for keyword arg 'ir' in log_tool_usage calls
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    
    found_ir_kwarg = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if this is a log_tool_usage call
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            
            if func_name == "log_tool_usage":
                for kw in node.keywords:
                    if kw.arg == "ir":
                        found_ir_kwarg = True
                        break
    
    if not found_ir_kwarg:
        return False, "log_tool_usage must be called with 'ir=ir' keyword argument for provenance"
    
    return True, "log_tool_usage correctly called with ir=ir keyword argument"

check("log_tool_usage_ir", check_log_tool_usage_ir)


# ── 8. Contract tests file exists and uses AgentContractTestMixin ─────────────

def check_contract_tests():
    tests_base = lobster_root / "tests"
    
    # Search for contract test file
    contract_files = list(tests_base.rglob("test_contract*.py")) + \
                     list(tests_base.rglob("*contract*test*.py"))
    
    # Also search in the package itself
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    contract_files += list(pkg.rglob("test_contract*.py"))
    
    if not contract_files:
        return False, "No contract test file found (e.g., test_contract.py)"
    
    contract_file = contract_files[0]
    source = contract_file.read_text()
    
    if "AgentContractTestMixin" not in source:
        return False, f"Contract test file {contract_file.name} must use AgentContractTestMixin"
    
    # Check it references the epigenomics agent module
    if "epigenomics" not in source:
        return False, "Contract test must reference the epigenomics agent module"
    
    # Check agent_module is set
    if "agent_module" not in source:
        return False, "Contract test class must set agent_module attribute"
    
    # Check factory_name is set
    if "factory_name" not in source:
        return False, "Contract test class must set factory_name attribute"
    
    return True, f"Contract test file found at {contract_file.relative_to(lobster_root)} with AgentContractTestMixin"

check("contract_tests", check_contract_tests)


# ── 9. Package can be installed and agent importable ─────────────────────────

def check_installable():
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    if not pkg.exists():
        return False, "Package directory missing"
    if not (pkg / "pyproject.toml").exists():
        return False, "pyproject.toml missing"
    
    result = subprocess.run(
        ["pip", "install", "-e", ".", "--quiet",
         "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        cwd=str(pkg),
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        return False, f"pip install failed: {result.stderr[-500:]}"
    
    return True, "Package installed successfully in editable mode"

check("package_installable", check_installable)


# ── 10. AGENT_CONFIG importable at runtime ────────────────────────────────────

def check_runtime_import():
    # Must run after install check
    if not checks[-1]["passed"]:
        return False, "Skipped: package not installed"
    
    pkg = lobster_root / "packages" / "lobster-epigenomics"
    agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
    agent_files = [f for f in agent_files if f.name != "__init__.py"]
    
    if not agent_files:
        return False, "No agent file to import"
    
    agent_stem = agent_files[0].stem
    module_path = f"lobster.agents.epigenomics.{agent_stem}"
    
    try:
        # Force reimport
        if module_path in sys.modules:
            del sys.modules[module_path]
        
        start = time.time()
        mod = importlib.import_module(module_path)
        elapsed = time.time() - start
        
        if not hasattr(mod, "AGENT_CONFIG"):
            return False, f"Module {module_path} has no AGENT_CONFIG"
        
        from lobster.config.agent_registry import AgentRegistryConfig
        if not isinstance(mod.AGENT_CONFIG, AgentRegistryConfig):
            return False, "AGENT_CONFIG is not an AgentRegistryConfig instance"
        
        if elapsed >= 0.05:
            return False, f"AGENT_CONFIG import took {elapsed:.3f}s, must be <50ms"
        
        return True, f"AGENT_CONFIG importable in {elapsed*1000:.1f}ms as AgentRegistryConfig"
    except ImportError as e:
        return False, f"ImportError: {e}"
    except Exception as e:
        return False, f"Exception during import: {e}"

check("runtime_import", check_runtime_import)


# ── 11. Entry point registered in ComponentRegistry ──────────────────────────

def check_entry_point_discovery():
    if not checks[-1]["passed"]:
        return False, "Skipped: package not importable"
    
    try:
        # Clear cached registry
        if "lobster.core.component_registry" in sys.modules:
            del sys.modules["lobster.core.component_registry"]
        
        from lobster.core.component_registry import ComponentRegistry
        registry = ComponentRegistry()
        agents = registry.get_available_agents()
        agent_names = [a["name"] for a in agents]
        
        # The epigenomics agent should be discoverable
        # Its name comes from AGENT_CONFIG.name
        pkg = lobster_root / "packages" / "lobster-epigenomics"
        agent_files = list((pkg / "lobster" / "agents" / "epigenomics").glob("*.py"))
        agent_files = [f for f in agent_files if f.name != "__init__.py"]
        
        if not agent_files:
            return False, "No agent file found"
        
        # Try to get the name from the module
        agent_stem = agent_files[0].stem
        module_path = f"lobster.agents.epigenomics.{agent_stem}"
        mod = importlib.import_module(module_path)
        expected_name = mod.AGENT_CONFIG.name
        
        if expected_name not in agent_names:
            return False, (f"Agent '{expected_name}' not found in ComponentRegistry. "
                           f"Discovered agents: {agent_names}. "
                           f"Check entry point registration in pyproject.toml.")
        
        return True, f"Agent '{expected_name}' correctly discovered via ComponentRegistry entry points"
    except Exception as e:
        return False, f"ComponentRegistry check failed: {e}"

check("entry_point_discovery", check_entry_point_discovery)


# ── Final scoring ─────────────────────────────────────────────────────────────

passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 3)
all_passed = passed_count == total

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, indent=2))