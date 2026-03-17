"""Data models for SkillBench instances and evaluation results."""

from dataclasses import dataclass, field, asdict
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
