#!/usr/bin/env python3
"""
Generate the sandbox workspace for the finishing-a-development-branch skill test.
Creates a realistic medical device firmware project with:
- A main git repo (infusion-firmware)
- A git worktree for feature/dose-calculation branch
- Passing pytest test suite in the worktree
- Distractor files throughout
"""

import os
import subprocess
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

def run(cmd, cwd=None, check=True):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return result

def git(cmd, cwd=None):
    return run(f"git {cmd}", cwd=cwd)

# ─── 1. Create the main repository ───────────────────────────────────────────
REPO = WORKSPACE / "infusion-firmware"
REPO.mkdir(parents=True, exist_ok=True)

git("init", cwd=REPO)
git("config user.email 'dev@medtech.local'", cwd=REPO)
git("config user.name 'MedTech Dev'", cwd=REPO)

# Create realistic project structure on main
(REPO / "src").mkdir()
(REPO / "src" / "pump_controller.py").write_text(textwrap.dedent("""\
    \"\"\"Core pump controller module for InfusionOS v2.\"\"\"

    class PumpController:
        def __init__(self, max_rate_ml_hr=500):
            self.max_rate = max_rate_ml_hr
            self.current_rate = 0
            self.running = False

        def start(self, rate_ml_hr):
            if rate_ml_hr > self.max_rate:
                raise ValueError(f"Rate {rate_ml_hr} exceeds max {self.max_rate}")
            self.current_rate = rate_ml_hr
            self.running = True

        def stop(self):
            self.running = False
            self.current_rate = 0

        def status(self):
            return {"running": self.running, "rate": self.current_rate}
"""))

(REPO / "src" / "alarm_manager.py").write_text(textwrap.dedent("""\
    \"\"\"Alarm management subsystem.\"\"\"
    import time

    ALARM_LEVELS = {"critical": 3, "warning": 2, "info": 1}

    class AlarmManager:
        def __init__(self):
            self._alarms = []

        def raise_alarm(self, level, message):
            if level not in ALARM_LEVELS:
                raise ValueError(f"Unknown alarm level: {level}")
            self._alarms.append({"level": level, "message": message, "ts": time.time()})

        def clear(self):
            self._alarms.clear()

        def active(self):
            return list(self._alarms)
"""))

(REPO / "src" / "__init__.py").write_text('"""InfusionOS source package."""\n')

(REPO / "tests").mkdir()
(REPO / "tests" / "__init__.py").write_text("")
(REPO / "tests" / "test_pump_controller.py").write_text(textwrap.dedent("""\
    import pytest
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from pump_controller import PumpController

    def test_start_normal():
        pc = PumpController()
        pc.start(100)
        assert pc.status()["running"] is True
        assert pc.status()["rate"] == 100

    def test_start_exceeds_max():
        pc = PumpController(max_rate_ml_hr=200)
        with pytest.raises(ValueError):
            pc.start(300)

    def test_stop():
        pc = PumpController()
        pc.start(50)
        pc.stop()
        assert pc.status()["running"] is False
"""))

(REPO / "tests" / "test_alarm_manager.py").write_text(textwrap.dedent("""\
    import pytest
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from alarm_manager import AlarmManager

    def test_raise_critical():
        am = AlarmManager()
        am.raise_alarm("critical", "Over-pressure")
        assert len(am.active()) == 1

    def test_raise_invalid_level():
        am = AlarmManager()
        with pytest.raises(ValueError):
            am.raise_alarm("fatal", "bad")

    def test_clear():
        am = AlarmManager()
        am.raise_alarm("info", "test")
        am.clear()
        assert am.active() == []
"""))

# Distractor files
(REPO / "docs").mkdir()
(REPO / "docs" / "architecture.md").write_text("# InfusionOS Architecture\n\nTBD - see Confluence\n")
(REPO / "docs" / "api_reference.md").write_text("# API Reference\n\nVersion 2.1.0\n")
(REPO / "docs" / "safety_analysis.md").write_text("# FMEA Safety Analysis\n\nRevision 3, 2024-01\n")
(REPO / "configs").mkdir()
(REPO / "configs" / "prod.yaml").write_text("pump:\n  max_rate: 500\n  units: ml_hr\nalarms:\n  critical_threshold: 10\n")
(REPO / "configs" / "dev.yaml").write_text("pump:\n  max_rate: 1000\n  units: ml_hr\nalarms:\n  critical_threshold: 5\n")
(REPO / "configs" / "test.yaml").write_text("pump:\n  max_rate: 200\n  units: ml_hr\n")
(REPO / "scripts").mkdir()
(REPO / "scripts" / "deploy.sh").write_text("#!/bin/bash\necho 'Deploying InfusionOS...'\n")
(REPO / "scripts" / "lint.sh").write_text("#!/bin/bash\npython3 -m flake8 src/ tests/\n")
(REPO / "scripts" / "build_firmware.sh").write_text("#!/bin/bash\necho 'Building firmware image v2.1.0'\n")
(REPO / ".ci").mkdir()
(REPO / ".ci" / "pipeline.yml").write_text(textwrap.dedent("""\
    stages:
      - lint
      - test
      - build
      - deploy
    test:
      script: pytest tests/ -v
      coverage: 80%
"""))
(REPO / "requirements.txt").write_text("pytest>=7.0\nflake8>=6.0\ncoverage>=7.0\n")
(REPO / "setup.py").write_text(textwrap.dedent("""\
    from setuptools import setup, find_packages
    setup(name='infusion-os', version='2.1.0', packages=find_packages())
"""))

# Commit the baseline to main
git("add -A", cwd=REPO)
git("commit -m 'chore: baseline InfusionOS v2.1.0 - pump controller and alarm subsystems'", cwd=REPO)

# ─── 2. Create the feature branch ────────────────────────────────────────────
git("checkout -b feature/dose-calculation", cwd=REPO)

# Add dose calculation module to the feature branch
(REPO / "src" / "dose_calculator.py").write_text(textwrap.dedent("""\
    \"\"\"
    Dose calculation engine for InfusionOS v2.
    Implements weight-based and BSA-based dosing per ICU protocol IC-2024-07.
    \"\"\"

    CONCENTRATION_LIMITS = {
        "dopamine": (0.8, 3.0),      # mcg/kg/min limits
        "norepinephrine": (0.01, 3.0),
        "epinephrine": (0.01, 1.0),
        "vasopressin": (0.01, 0.1),  # units/min
    }

    class DoseCalculator:
        def __init__(self, drug: str, weight_kg: float):
            if weight_kg <= 0:
                raise ValueError("Weight must be positive")
            if drug not in CONCENTRATION_LIMITS:
                raise KeyError(f"Unknown drug: {drug}")
            self.drug = drug
            self.weight_kg = weight_kg
            self._min, self._max = CONCENTRATION_LIMITS[drug]

        def validate_dose(self, dose_mcg_kg_min: float) -> bool:
            \"\"\"Return True if dose is within safe limits.\"\"\"
            return self._min <= dose_mcg_kg_min <= self._max

        def to_ml_hr(self, dose_mcg_kg_min: float, concentration_mcg_ml: float) -> float:
            \"\"\"Convert dose to infusion rate in mL/hr.\"\"\"
            if concentration_mcg_ml <= 0:
                raise ValueError("Concentration must be positive")
            if not self.validate_dose(dose_mcg_kg_min):
                raise ValueError(
                    f"Dose {dose_mcg_kg_min} out of range "
                    f"[{self._min}, {self._max}] for {self.drug}"
                )
            # dose (mcg/kg/min) * weight (kg) * 60 (min/hr) / concentration (mcg/mL)
            return (dose_mcg_kg_min * self.weight_kg * 60) / concentration_mcg_ml

        def titration_steps(self, current_dose: float, target_dose: float, steps: int = 4):
            \"\"\"Generate linear titration steps between current and target dose.\"\"\"
            if steps < 2:
                raise ValueError("Need at least 2 steps")
            delta = (target_dose - current_dose) / (steps - 1)
            return [round(current_dose + i * delta, 4) for i in range(steps)]
"""))

# Update tests directory with dose calculator tests
(REPO / "tests" / "test_dose_calculator.py").write_text(textwrap.dedent("""\
    import pytest
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from dose_calculator import DoseCalculator, CONCENTRATION_LIMITS

    def test_dopamine_valid_dose():
        calc = DoseCalculator("dopamine", weight_kg=70)
        assert calc.validate_dose(1.5) is True

    def test_dopamine_dose_too_high():
        calc = DoseCalculator("dopamine", weight_kg=70)
        assert calc.validate_dose(5.0) is False

    def test_dose_to_ml_hr():
        # dopamine 1.0 mcg/kg/min, 70kg, 400mcg/mL concentration
        calc = DoseCalculator("dopamine", weight_kg=70)
        rate = calc.to_ml_hr(dose_mcg_kg_min=1.0, concentration_mcg_ml=400)
        # 1.0 * 70 * 60 / 400 = 10.5 mL/hr
        assert abs(rate - 10.5) < 0.01

    def test_invalid_drug():
        with pytest.raises(KeyError):
            DoseCalculator("aspirin", weight_kg=70)

    def test_negative_weight():
        with pytest.raises(ValueError):
            DoseCalculator("dopamine", weight_kg=-5)

    def test_zero_concentration_raises():
        calc = DoseCalculator("norepinephrine", weight_kg=80)
        with pytest.raises(ValueError):
            calc.to_ml_hr(0.1, 0)

    def test_titration_steps_count():
        calc = DoseCalculator("dopamine", weight_kg=70)
        steps = calc.titration_steps(1.0, 2.0, steps=5)
        assert len(steps) == 5

    def test_titration_boundary_values():
        calc = DoseCalculator("epinephrine", weight_kg=60)
        steps = calc.titration_steps(0.01, 0.05, steps=3)
        assert abs(steps[0] - 0.01) < 0.001
        assert abs(steps[-1] - 0.05) < 0.001

    def test_out_of_range_dose_raises_on_convert():
        calc = DoseCalculator("vasopressin", weight_kg=70)
        with pytest.raises(ValueError):
            calc.to_ml_hr(5.0, 20)

    def test_all_drugs_present():
        expected = {"dopamine", "norepinephrine", "epinephrine", "vasopressin"}
        assert set(CONCENTRATION_LIMITS.keys()) == expected
"""))

# Additional distractor files on the feature branch
(REPO / "docs" / "dose_protocol.md").write_text(textwrap.dedent("""\
    # Dose Calculation Protocol IC-2024-07

    ## Background
    Vasoactive drug dosing requires real-time weight-based calculations.

    ## Approved Drugs
    - Dopamine: 0.8–3.0 mcg/kg/min
    - Norepinephrine: 0.01–3.0 mcg/kg/min
    - Epinephrine: 0.01–1.0 mcg/kg/min
    - Vasopressin: 0.01–0.1 units/min
"""))

(REPO / "configs" / "dose_limits.yaml").write_text(textwrap.dedent("""\
    drugs:
      dopamine:
        min_mcg_kg_min: 0.8
        max_mcg_kg_min: 3.0
      norepinephrine:
        min_mcg_kg_min: 0.01
        max_mcg_kg_min: 3.0
      epinephrine:
        min_mcg_kg_min: 0.01
        max_mcg_kg_min: 1.0
      vasopressin:
        min_units_min: 0.01
        max_units_min: 0.1
"""))

(REPO / "src" / "infusion_planner.py").write_text(textwrap.dedent("""\
    \"\"\"High-level infusion planner that integrates dose calculator with pump controller.\"\"\"
    from dose_calculator import DoseCalculator
    from pump_controller import PumpController

    class InfusionPlanner:
        def __init__(self, drug, weight_kg, concentration_mcg_ml, max_pump_rate=500):
            self.calc = DoseCalculator(drug, weight_kg)
            self.pump = PumpController(max_rate_ml_hr=max_pump_rate)
            self.concentration = concentration_mcg_ml

        def start_infusion(self, dose_mcg_kg_min):
            rate = self.calc.to_ml_hr(dose_mcg_kg_min, self.concentration)
            self.pump.start(rate)
            return rate

        def stop(self):
            self.pump.stop()
"""))

# Commit feature branch changes
git("add -A", cwd=REPO)
git("commit -m 'feat(dose): implement weight-based dose calculation engine per IC-2024-07'", cwd=REPO)
git("commit --allow-empty -m 'feat(dose): add titration step generator and boundary validation'", cwd=REPO)

# Switch back to main
git("checkout main", cwd=REPO)

# ─── 3. Create a git worktree for the feature branch ─────────────────────────
WORKTREE = WORKSPACE / "worktrees" / "dose-calculation-wt"
WORKTREE.parent.mkdir(parents=True, exist_ok=True)

git(f"worktree add {WORKTREE} feature/dose-calculation", cwd=REPO)

# ─── 4. Add more distractors to the workspace root ───────────────────────────
(WORKSPACE / "scratch_notes.txt").write_text(
    "TODO: review titration step edge cases\n"
    "Ask Sarah about the vasopressin upper limit\n"
    "Build passes on CI - check logs at internal-ci/runs/4892\n"
)
(WORKSPACE / "old_dose_calc_v1.py").write_text(textwrap.dedent("""\
    # DEPRECATED - replaced by src/dose_calculator.py
    def calc_dopamine(weight, dose):
        return (dose * weight * 60) / 400  # hardcoded concentration - BAD
"""))
(WORKSPACE / "meeting_notes_2024_03_15.txt").write_text(textwrap.dedent("""\
    Attendees: Dev Team, Clinical Informatics
    - Agreed on 4-step titration as default
    - Vasopressin upper limit confirmed at 0.1 units/min
    - Need to integrate DoseCalculator into InfusionPlanner by sprint end
    - Feature branch: feature/dose-calculation
    - Target merge: main by EOW
"""))

# ─── 5. Create a fake 'gh' CLI to avoid real GitHub calls ────────────────────
# (placed at /usr/local/bin/gh - done in setup_script)

print("Workspace generated successfully.")
print(f"  Main repo:    {REPO}")
print(f"  Worktree:     {WORKTREE}")
print(f"  Feature branch: feature/dose-calculation")
run(f"git -C {REPO} log --oneline --all", check=False)
run(f"git -C {REPO} worktree list", check=False)