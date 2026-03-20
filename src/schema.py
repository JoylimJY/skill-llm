"""Data models for SkillBench instances and evaluation results."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
from typing import Any


@dataclass
class InstanceSpec:
    """Complete instance specification returned by Claude API."""

    instance_id: str
    skill_name: str
    category: str
    difficulty: str  # "easy" / "medium" / "hard"
    prompt: str  # Natural language user request
    dockerfile: str  # Dockerfile content
    gen_inputs_script: str  # Python script to generate input files
    setup_script: str  # Bash setup script
    eval_script: str  # Python eval script
    expected: dict = field(default_factory=dict)  # Expected output metadata

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "InstanceSpec":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class EvalResult:
    """Result from running evaluation on a completed task."""

    instance_id: str
    passed: bool
    score: float  # 0.0 - 1.0
    details: list[dict] = field(default_factory=list)  # Per-check results

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class RunSummary:
    """Aggregate statistics for one evaluation run."""

    run_name: str
    model: str
    api_base: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    total: int = 0
    passed: int = 0
    failed: int = 0
    avg_score: float = 0.0
    instances: dict = field(default_factory=dict)  # {instance_id: {passed, score}}

    def update_from_result(self, result: "EvalResult"):
        score = result.score if result.score <= 1.0 else result.score / 100.0
        self.instances[result.instance_id] = {"passed": result.passed, "score": score}
        self._recalculate()

    def _recalculate(self):
        self.total = len(self.instances)
        self.passed = sum(1 for v in self.instances.values() if v["passed"])
        self.failed = self.total - self.passed
        self.avg_score = (
            sum(v["score"] for v in self.instances.values()) / self.total
            if self.total > 0
            else 0.0
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def load(cls, path: str) -> "RunSummary":
        d = json.loads(open(path).read())
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def save(self, path: str):
        open(path, "w").write(self.to_json())
