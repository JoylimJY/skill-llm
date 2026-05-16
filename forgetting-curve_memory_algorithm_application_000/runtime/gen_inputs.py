import os
import json
import random
import math
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create realistic distractor directory structure
dirs = [
    "app/core",
    "app/models",
    "app/api",
    "app/utils",
    "data/raw",
    "data/processed",
    "config",
    "tests/unit",
    "tests/integration",
    "scripts",
    "docs",
    "forgetting-curve/examples",
    "forgetting-curve/config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Create the actual forgetting_curve module ---
forgetting_curve_code = '''"""
Forgetting Curve Module - Ebbinghaus Memory Decay
"""
import math


class ForgettingCurve:
    def __init__(self, half_life_days=30.0, initial_strength=1.0,
                 minimum_strength=0.1, decay_function=None):
        self.half_life_days = half_life_days
        self.initial_strength = initial_strength
        self.minimum_strength = minimum_strength
        self._custom_decay = decay_function

    def calculate_decay(self, age_days):
        """Ebbinghaus exponential decay: 2^(-age_days / half_life_days)"""
        if self._custom_decay is not None:
            return self._custom_decay(age_days, self.initial_strength)
        return math.pow(2, -age_days / self.half_life_days)

    def apply_decay(self, original_strength, age_days):
        """Apply decay to a given memory strength."""
        decay = self.calculate_decay(age_days)
        result = original_strength * decay
        return max(result, self.minimum_strength)


class SpacedRepetitionScheduler:
    def __init__(self, base_interval=1.0, strength_factor=1.5,
                 easy_factor=1.3, hard_factor=0.8, minimum_strength=0.1):
        self.base_interval = base_interval
        self.strength_factor = strength_factor
        self.easy_factor = easy_factor
        self.hard_factor = hard_factor
        self.minimum_strength = minimum_strength

    def next_review_interval(self, current_strength):
        """Calculate next review interval in days.
        next_review_days = base_interval * (strength ^ factor)
        """
        return self.base_interval * math.pow(current_strength, self.strength_factor)

    def update_strength(self, current_strength, success=True, easy=False, hard=False):
        """Update memory strength after review."""
        if success:
            if easy:
                new_strength = min(1.0, current_strength * self.easy_factor)
            elif hard:
                new_strength = min(1.0, current_strength * self.hard_factor + 0.1)
            else:
                new_strength = min(1.0, current_strength + 0.15)
        else:
            new_strength = max(self.minimum_strength, current_strength * self.hard_factor)
        return new_strength


def batch_decay(memories, half_life_days=30.0):
    """
    Batch calculate decay for a list of memory dicts.
    Each dict must have: id, strength, age_days
    Returns list with added 'decayed_strength' field.
    """
    curve = ForgettingCurve(half_life_days=half_life_days)
    results = []
    for mem in memories:
        decayed = curve.apply_decay(mem["strength"], mem["age_days"])
        result = dict(mem)
        result["decayed_strength"] = decayed
        results.append(result)
    return results
'''

(workspace / "forgetting-curve" / "forgetting_curve.py").write_text(forgetting_curve_code)

# Copy to root for easy import
(workspace / "forgetting_curve.py").write_text(forgetting_curve_code)

# --- Test file ---
test_code = '''"""Unit tests for forgetting_curve module."""
import math
import pytest
from forgetting_curve import ForgettingCurve, SpacedRepetitionScheduler, batch_decay


def test_basic_decay():
    curve = ForgettingCurve(half_life_days=30.0)
    decay = curve.calculate_decay(30)
    assert abs(decay - 0.5) < 1e-6


def test_apply_decay():
    curve = ForgettingCurve(half_life_days=30.0)
    result = curve.apply_decay(1.0, 30)
    assert abs(result - 0.5) < 1e-6


def test_minimum_strength():
    curve = ForgettingCurve(half_life_days=1.0, minimum_strength=0.1)
    result = curve.apply_decay(0.01, 1000)
    assert result == 0.1


def test_srs_interval():
    sched = SpacedRepetitionScheduler()
    interval = sched.next_review_interval(0.6)
    expected = 1.0 * math.pow(0.6, 1.5)
    assert abs(interval - expected) < 1e-6
'''

(workspace / "forgetting-curve" / "test_decay.py").write_text(test_code)

# --- Distractor files ---
(workspace / "app" / "core" / "memory_manager.py").write_text('''
# Legacy memory manager - DO NOT USE DIRECTLY
# Uses hardcoded decay: decay = 2**(-age/30)
class LegacyMemoryManager:
    def compute_decay(self, age):
        return 2**(-age/30)
''')

(workspace / "app" / "models" / "vocabulary.py").write_text('''
from dataclasses import dataclass
from typing import Optional

@dataclass
class VocabularyItem:
    word_id: str
    word: str
    strength: float
    age_days: float
    tier: str  # "short_term", "procedural", "long_term"
    last_result: Optional[str] = None  # "success", "fail", "easy", "hard"
''')

(workspace / "app" / "api" / "routes.py").write_text('''
# API routes placeholder
# GET /api/vocabulary/review-schedule
# POST /api/vocabulary/update-strength
''')

(workspace / "app" / "utils" / "date_utils.py").write_text('''
from datetime import datetime, timedelta

def days_since(timestamp):
    return (datetime.now() - timestamp).days

def add_days(dt, days):
    return dt + timedelta(days=days)
''')

(workspace / "config" / "app_config.json").write_text(json.dumps({
    "app_name": "LinguaTrack",
    "version": "2.1.0",
    "default_deck_size": 50,
    "session_duration_minutes": 20
}, indent=2))

(workspace / "config" / "legacy_decay_config.json").write_text(json.dumps({
    "half_life": 30,
    "note": "OLD CONFIG - flat 30-day half-life for all items"
}, indent=2))

(workspace / "docs" / "architecture.md").write_text('''# LinguaTrack Architecture
...
Memory tiers: short_term (new words), procedural (grammar rules), long_term (mastered vocabulary)
Each tier has different retention characteristics.
''')

(workspace / "scripts" / "migrate_deck.py").write_text('''
# Data migration script (legacy)
import json, sys

def migrate(input_file, output_file):
    with open(input_file) as f:
        data = json.load(f)
    # TODO: apply new decay model
    with open(output_file, "w") as f:
        json.dump(data, f)
''')

(workspace / "tests" / "unit" / "test_legacy.py").write_text('''
def test_placeholder():
    pass
''')

(workspace / "tests" / "integration" / "test_api.py").write_text('''
def test_placeholder():
    pass
''')

(workspace / "forgetting-curve" / "config" / "defaults.json").write_text(json.dumps({
    "half_life_days": 30.0,
    "initial_strength": 1.0,
    "minimum_strength": 0.1,
    "base_interval": 1.0,
    "strength_factor": 1.5,
    "easy_factor": 1.3,
    "hard_factor": 0.8
}, indent=2))

(workspace / "forgetting-curve" / "examples" / "basic_usage.py").write_text('''
# Example usage - not a runnable script without context
from forgetting_curve import ForgettingCurve
curve = ForgettingCurve(half_life_days=30.0)
print(curve.calculate_decay(7))
''')

# --- THE MAIN INPUT: messy vocabulary review data ---
# These are vocabulary items with mixed tiers, various ages, and last review outcomes
# The agent must process these using the correct tier-specific half-lives

vocabulary_data = {
    "learner_id": "user_8472",
    "deck_name": "Spanish Essentials",
    "items": [
        # short_term tier (new words, half_life=3.0 days)
        {"word_id": "w001", "word": "hola", "tier": "short_term", "strength": 0.85, "age_days": 1, "last_result": "success"},
        {"word_id": "w002", "word": "gracias", "tier": "short_term", "strength": 0.72, "age_days": 2, "last_result": "easy"},
        {"word_id": "w003", "word": "adios", "tier": "short_term", "strength": 0.60, "age_days": 4, "last_result": "hard"},
        {"word_id": "w004", "word": "buenas", "tier": "short_term", "strength": 0.45, "age_days": 6, "last_result": "fail"},
        # procedural tier (grammar patterns, half_life=7.0 days)
        {"word_id": "w005", "word": "ser_vs_estar", "tier": "procedural", "strength": 0.78, "age_days": 3, "last_result": "success"},
        {"word_id": "w006", "word": "subjunctive_present", "tier": "procedural", "strength": 0.55, "age_days": 10, "last_result": "hard"},
        {"word_id": "w007", "word": "preterite_irregular", "tier": "procedural", "strength": 0.40, "age_days": 14, "last_result": "fail"},
        {"word_id": "w008", "word": "reflexive_verbs", "tier": "procedural", "strength": 0.90, "age_days": 1, "last_result": "easy"},
        # long_term tier (mastered vocabulary, half_life=90.0 days)
        {"word_id": "w009", "word": "hablar", "tier": "long_term", "strength": 0.95, "age_days": 30, "last_result": "success"},
        {"word_id": "w010", "word": "comer", "tier": "long_term", "strength": 0.88, "age_days": 60, "last_result": "easy"},
        {"word_id": "w011", "word": "vivir", "tier": "long_term", "strength": 0.70, "age_days": 120, "last_result": "hard"},
        {"word_id": "w012", "word": "tener", "tier": "long_term", "strength": 0.50, "age_days": 200, "last_result": "fail"},
    ]
}

(workspace / "data" / "raw" / "vocabulary_review_session.json").write_text(
    json.dumps(vocabulary_data, indent=2)
)

# Also create a confusing "processed" stub
(workspace / "data" / "processed" / ".gitkeep").write_text("")

print("Workspace initialized successfully.")
print(f"Input file: {workspace / 'data' / 'raw' / 'vocabulary_review_session.json'}")