import os
import json
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Core lobster SDK stub ──────────────────────────────────────────────────────
# Simulates the installed lobster-ai core package so agent code can import from it.

lobster_core = WORKSPACE / "lobster" / "lobster"

# lobster/lobster is a namespace package (no __init__.py at lobster/ level)
# but there IS one inside lobster/lobster/
(lobster_core).mkdir(parents=True, exist_ok=True)
(lobster_core / "__init__.py").write_text('# core SDK\n')

# lobster/lobster/config/
config_pkg = lobster_core / "config"
config_pkg.mkdir(parents=True, exist_ok=True)
(config_pkg / "__init__.py").write_text("")

(config_pkg / "agent_registry.py").write_text('''\
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AgentRegistryConfig:
    name: str
    display_name: str
    description: str
    factory_function: str
    handoff_tool_name: str
    handoff_tool_description: str
    tier_requirement: str = "free"
    child_agents: List[str] = field(default_factory=list)
''')

(config_pkg / "llm_factory.py").write_text('''\
from unittest.mock import MagicMock

def create_llm(agent_name, model_params, workspace_path=None):
    """Stub LLM factory."""
    llm = MagicMock()
    llm.invoke.return_value = "stub response"
    return llm
''')

(config_pkg / "settings.py").write_text('''\
class _Settings:
    def get_agent_llm_params(self, agent_name):
        return {}

_instance = _Settings()
def get_settings():
    return _instance
''')

# lobster/lobster/core/
core_pkg = lobster_core / "core"
core_pkg.mkdir(parents=True, exist_ok=True)
(core_pkg / "__init__.py").write_text("")

(core_pkg / "provenance.py").write_text('''\
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class AnalysisStep:
    activity_type: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    sub_steps: List[Any] = field(default_factory=list)

class ProvenanceTracker:
    def create_activity(self, name: str, step: AnalysisStep):
        pass
''')

(core_pkg / "data_manager_v2.py").write_text('''\
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

class DataManagerV2:
    def __init__(self, workspace_path=None, default_backend="local",
                 enable_provenance=True, auto_scan=True, console=None):
        self.workspace_path = workspace_path or Path("./workspace")

    def get_modality(self, name: str):
        import anndata as ad
        import numpy as np
        return ad.AnnData(X=np.random.rand(50, 30))

    def store_modality(self, name: str, data):
        pass

    def log_tool_usage(self, tool_name: str, params: dict, stats: dict, ir=None):
        pass

    def list_modalities(self):
        return []

    def has_modality(self, name: str) -> bool:
        return False
''')

(core_pkg / "component_registry.py").write_text('''\
import importlib.metadata
from typing import List, Dict, Any

class ComponentRegistry:
    def __init__(self):
        self._agents = {}
        self._discover()

    def _discover(self):
        try:
            eps = importlib.metadata.entry_points(group="lobster.agents")
            for ep in eps:
                try:
                    config = ep.load()
                    self._agents[config.name] = config
                except Exception:
                    pass
        except Exception:
            pass

    def get_available_agents(self) -> List[Dict[str, Any]]:
        return [{"name": c.name, "description": c.description} for c in self._agents.values()]

    def get_agent(self, name: str):
        return self._agents.get(name)

    def is_agent_available(self, name: str, tier: str = "free") -> bool:
        return name in self._agents
''')

# lobster/lobster/testing/
testing_pkg = lobster_core / "testing"
testing_pkg.mkdir(parents=True, exist_ok=True)
(testing_pkg / "__init__.py").write_text('''\
from .contract import AgentContractTestMixin
''')

(testing_pkg / "contract.py").write_text('''\
import inspect
import importlib
import time


class AgentContractTestMixin:
    """Mixin that validates agent plugin contracts."""

    agent_module: str = ""
    factory_name: str = ""
    expected_tier: str = None

    def test_agent_config_exists(self):
        mod = importlib.import_module(self.agent_module)
        from lobster.config.agent_registry import AgentRegistryConfig
        assert hasattr(mod, "AGENT_CONFIG"), "AGENT_CONFIG missing"
        assert isinstance(mod.AGENT_CONFIG, AgentRegistryConfig)

    def test_agent_config_loads_fast(self):
        start = time.time()
        mod = importlib.import_module(self.agent_module)
        _ = mod.AGENT_CONFIG
        elapsed = time.time() - start
        assert elapsed < 0.05, f"Config load {elapsed:.3f}s > 50ms"

    def test_factory_has_standard_params(self):
        mod = importlib.import_module(self.agent_module)
        factory = getattr(mod, self.factory_name)
        sig = inspect.signature(factory)
        params = list(sig.parameters.keys())
        assert "data_manager" in params, "Missing data_manager param"
        assert "delegation_tools" in params, "Missing delegation_tools param"
        assert "workspace_path" in params, "Missing workspace_path param"
        assert "callback_handler" in params, "Missing callback_handler param"

    def test_no_deprecated_handoff_tools(self):
        mod = importlib.import_module(self.agent_module)
        factory = getattr(mod, self.factory_name)
        sig = inspect.signature(factory)
        params = list(sig.parameters.keys())
        assert "handoff_tools" not in params, "handoff_tools is deprecated, use delegation_tools"

    def test_tier_requirement_valid(self):
        mod = importlib.import_module(self.agent_module)
        config = mod.AGENT_CONFIG
        valid_tiers = ("free", "premium", "enterprise")
        assert config.tier_requirement in valid_tiers

    def test_expected_tier(self):
        if self.expected_tier is None:
            return
        mod = importlib.import_module(self.agent_module)
        assert mod.AGENT_CONFIG.tier_requirement == self.expected_tier
''')

# lobster/lobster/tools/ stub
tools_pkg = lobster_core / "tools"
tools_pkg.mkdir(parents=True, exist_ok=True)
(tools_pkg / "__init__.py").write_text("")

# ── lobster-ai as installable package (core) ──────────────────────────────────
lobster_root = WORKSPACE / "lobster"
(lobster_root / "pyproject.toml").write_text('''\
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lobster-ai"
version = "1.0.0"
description = "Lobster AI core SDK"
requires-python = ">=3.12"
dependencies = []

[tool.setuptools]
packages.find = {where = ["."], include = ["lobster*"], namespaces = true}
''')

# ── existing packages for context (distractors) ───────────────────────────────
packages_dir = WORKSPACE / "lobster" / "packages"

existing_pkgs = {
    "lobster-transcriptomics": {
        "agents": ["transcriptomics_expert", "annotation_expert", "de_analysis_expert"],
        "services": ["normalization_service", "clustering_service", "de_service",
                     "qc_service", "embedding_service", "marker_service",
                     "integration_service", "trajectory_service"],
    },
    "lobster-research": {
        "agents": ["research_agent", "data_expert_agent"],
        "services": ["pubmed_service"],
    },
    "lobster-visualization": {
        "agents": ["visualization_expert"],
        "services": ["plot_service"],
    },
    "lobster-metadata": {
        "agents": ["metadata_assistant"],
        "services": ["geo_service", "sra_service", "annotation_service",
                     "format_service", "qc_service", "harmonization_service",
                     "ontology_service", "validation_service"],
    },
}

for pkg_name, contents in existing_pkgs.items():
    domain = pkg_name.replace("lobster-", "").replace("-", "_")
    pkg_root = packages_dir / pkg_name

    # pyproject.toml
    pkg_root.mkdir(parents=True, exist_ok=True)
    agent_ep_lines = "\n".join(
        f'{a} = "lobster.agents.{domain}.{a}:AGENT_CONFIG"'
        for a in contents["agents"]
    )
    (pkg_root / "pyproject.toml").write_text(f'''\
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkg_name}"
version = "1.0.0"
description = "{domain.replace("_", " ").title()} agents for Lobster AI"
requires-python = ">=3.12"
dependencies = [
    "lobster-ai~=1.0.0",
]

[project.entry-points."lobster.agents"]
{agent_ep_lines}

[tool.setuptools]
packages.find = {{where = ["."], include = ["lobster*"], namespaces = true}}
''')

    # Stub agent files
    for agent_name in contents["agents"]:
        agent_dir = pkg_root / "lobster" / "agents" / domain
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "__init__.py").write_text("")
        (agent_dir / f"{agent_name}.py").write_text(f'''\
from lobster.config.agent_registry import AgentRegistryConfig

AGENT_CONFIG = AgentRegistryConfig(
    name="{agent_name}",
    display_name="{agent_name.replace("_", " ").title()}",
    description="Expert agent for {domain} analysis",
    factory_function="lobster.agents.{domain}.{agent_name}.{agent_name}",
    handoff_tool_name="handoff_to_{agent_name}",
    handoff_tool_description="Assign {domain} tasks",
    tier_requirement="free",
)

# Heavy imports AFTER config
from pathlib import Path
from typing import Optional, List
from lobster.core.data_manager_v2 import DataManagerV2


def {agent_name}(
    data_manager: DataManagerV2,
    callback_handler=None,
    agent_name: str = "{agent_name}",
    delegation_tools: Optional[List] = None,
    workspace_path: Optional[Path] = None,
    **kwargs
):
    pass
''')

    # Stub service files
    svc_dir = pkg_root / "lobster" / "services" / domain
    svc_dir.mkdir(parents=True, exist_ok=True)
    (svc_dir / "__init__.py").write_text("")
    for svc_name in contents["services"]:
        (svc_dir / f"{svc_name}.py").write_text(f'''\
from typing import Tuple, Dict
import anndata as ad
from lobster.core.provenance import AnalysisStep


class {svc_name.replace("_", " ").title().replace(" ", "")}:
    def analyze(self, adata, **params) -> Tuple[ad.AnnData, Dict, AnalysisStep]:
        stats = {{"n_cells": adata.n_obs, "status": "complete"}}
        ir = AnalysisStep(
            activity_type="{svc_name}",
            inputs={{"n_obs": adata.n_obs}},
            outputs=stats,
            params=params,
        )
        return adata.copy(), stats, ir
''')

# ── tests/unit/ stubs ──────────────────────────────────────────────────────────
tests_dir = WORKSPACE / "lobster" / "tests"
unit_dir = tests_dir / "unit"
(unit_dir / "agents").mkdir(parents=True, exist_ok=True)
(unit_dir / "services").mkdir(parents=True, exist_ok=True)
(unit_dir / "core").mkdir(parents=True, exist_ok=True)

(tests_dir / "conftest.py").write_text('''\
import pytest
import anndata as ad
import numpy as np
from unittest.mock import MagicMock


@pytest.fixture
def sample_adata():
    return ad.AnnData(
        X=np.random.rand(100, 50),
        obs={"cell_type": ["A"] * 50 + ["B"] * 50},
        var={"gene_name": [f"gene_{i}" for i in range(50)]}
    )


@pytest.fixture
def mock_data_manager(sample_adata):
    dm = MagicMock()
    dm.get_modality.return_value = sample_adata
    dm.list_modalities.return_value = ["test_modality"]
    dm.store_modality.return_value = None
    dm.log_tool_usage.return_value = None
    return dm
''')

(unit_dir / "agents" / "__init__.py").write_text("")
(unit_dir / "services" / "__init__.py").write_text("")
(unit_dir / "core" / "__init__.py").write_text("")

# Distractor test files
(unit_dir / "core" / "test_component_registry.py").write_text('''\
def test_registry_importable():
    from lobster.core.component_registry import ComponentRegistry
    r = ComponentRegistry()
    assert r is not None
''')

(unit_dir / "services" / "test_transcriptomics_service.py").write_text('''\
import anndata as ad
import numpy as np

def test_stub():
    adata = ad.AnnData(X=np.random.rand(10, 5))
    assert adata.n_obs == 10
''')

# Distractor docs
docs_dir = WORKSPACE / "lobster" / "docs"
docs_dir.mkdir(parents=True, exist_ok=True)
(docs_dir / "architecture.md").write_text("# Architecture\nSee references/architecture.md\n")
(docs_dir / "api-reference.md").write_text("# API Reference\nService API documentation.\n")
(docs_dir / "developer-guide.md").write_text("# Developer Guide\nHow to contribute.\n")

# Planning file distractor
planning_dir = WORKSPACE / "lobster" / ".planning"
planning_dir.mkdir(parents=True, exist_ok=True)
(planning_dir / "PROJECT.md").write_text("# Project\nLobster AI multi-agent bioinformatics platform.\n")
(planning_dir / "ROADMAP.md").write_text("# Roadmap\n- v1.1: Add epigenomics support\n- v1.2: Add metabolomics\n")

# Makefile distractor
(WORKSPACE / "lobster" / "Makefile").write_text('''\
.PHONY: test dev-install format

dev-install:
\tpip install -e .

test:
\tpytest tests/unit/ -v

format:
\tblack . && isort .
''')

# Wiki distractors
wiki_dir = WORKSPACE / "lobster" / "wiki"
wiki_dir.mkdir(parents=True, exist_ok=True)
for i in range(5):
    (wiki_dir / f"page_{i+1:02d}.md").write_text(f"# Wiki Page {i+1}\nContent for page {i+1}.\n")

print("Workspace generated successfully.")
print(f"Structure rooted at: {WORKSPACE}/lobster")