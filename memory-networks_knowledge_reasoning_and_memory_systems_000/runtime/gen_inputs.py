import os
import json
import random

random.seed(42)

base = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "research_institute/papers/2024/ai",
    "research_institute/papers/2024/ml",
    "research_institute/papers/2023",
    "research_institute/researchers/profiles",
    "research_institute/researchers/publications",
    "research_institute/knowledge_base/raw",
    "research_institute/knowledge_base/processed",
    "research_institute/knowledge_base/archive",
    "research_institute/config/legacy",
    "research_institute/config/drafts",
    "research_institute/experiments/results",
    "research_institute/experiments/logs",
    "tools/encoders",
    "tools/scorers",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractor_files = {
    "research_institute/papers/2024/ai/attention_is_all_you_need.txt": 
        "Transformer architecture introduced self-attention mechanism in 2017.",
    "research_institute/papers/2024/ai/bert_paper.txt": 
        "BERT uses bidirectional training of Transformer for language understanding.",
    "research_institute/papers/2024/ml/gradient_descent.txt": 
        "Gradient descent is an optimization algorithm for minimizing loss functions.",
    "research_institute/papers/2023/lstm_overview.txt": 
        "Long Short-Term Memory networks solve the vanishing gradient problem.",
    "research_institute/researchers/profiles/hinton.txt": 
        "Geoffrey Hinton is often called the godfather of deep learning.",
    "research_institute/researchers/profiles/lecun.txt": 
        "Yann LeCun pioneered convolutional neural networks.",
    "research_institute/researchers/publications/weston_2014.txt": 
        "Jason Weston published Memory Networks paper at arXiv 1410.3916 in 2014.",
    "research_institute/knowledge_base/raw/unstructured_notes.txt": 
        "Various unstructured notes about AI concepts mixed together without categorization.",
    "research_institute/knowledge_base/archive/old_facts.json": 
        json.dumps({"facts": ["old fact 1", "old fact 2"], "version": "0.1"}),
    "research_institute/config/legacy/old_config.json": 
        json.dumps({"embedding_dim": 64, "max_memory": 500, "hops": 2}),
    "research_institute/config/drafts/partial_config.json": 
        json.dumps({"memory_network": {"embedding_dim": 256}}),
    "research_institute/experiments/results/baseline_accuracy.txt": 
        "Baseline accuracy: 67.3% on bAbI tasks.",
    "research_institute/experiments/logs/run_001.log": 
        "Epoch 1: loss=2.34\nEpoch 2: loss=1.87\nEpoch 3: loss=1.45",
    "tools/encoders/tfidf_encoder.py": 
        "# TF-IDF based text encoder\ndef encode(text):\n    pass",
    "tools/scorers/cosine_scorer.py": 
        "# Cosine similarity scorer\ndef score(a, b):\n    pass",
}

for path, content in distractor_files.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM INPUT: A raw knowledge dump that the agent must process
# This contains facts with importance hints, episodic events, and associative knowledge
# The agent must build the memory system from this data

knowledge_dump = {
    "description": "Raw knowledge entries collected from the AI Research Institute. Each entry has a content, type hint, and an importance_score. The system needs to be built to properly categorize and reason over these.",
    "entries": [
        {
            "id": "e001",
            "content": "Memory Networks paper (Weston et al., 2014) introduced the I-G-O-R framework for reasoning with long-term memory",
            "type_hint": "fact",
            "subject": "Memory Networks",
            "predicate": "introduced",
            "object": "I-G-O-R framework",
            "importance_score": 0.95,
            "confidence": 0.99
        },
        {
            "id": "e002",
            "content": "The research team held a seminar on neural reasoning on 2024-06-15",
            "type_hint": "episodic",
            "timestamp": "2024-06-15T14:00:00",
            "participants": ["Dr. Chen", "Dr. Patel", "Dr. Kim"],
            "action": "held seminar on neural reasoning",
            "context": "Annual AI symposium",
            "importance_score": 0.75
        },
        {
            "id": "e003",
            "content": "Transformer architecture relies on self-attention for sequence modeling",
            "type_hint": "fact",
            "subject": "Transformer",
            "predicate": "relies_on",
            "object": "self-attention",
            "importance_score": 0.92,
            "confidence": 0.98
        },
        {
            "id": "e004",
            "content": "Deep learning is a subset of machine learning",
            "type_hint": "fact",
            "subject": "deep learning",
            "predicate": "is_subset_of",
            "object": "machine learning",
            "importance_score": 0.91,
            "confidence": 0.99
        },
        {
            "id": "e005",
            "content": "Neural networks are the foundation of deep learning",
            "type_hint": "fact",
            "subject": "neural networks",
            "predicate": "foundation_of",
            "object": "deep learning",
            "importance_score": 0.93,
            "confidence": 0.97
        },
        {
            "id": "e006",
            "content": "Transformer is a type of neural network architecture",
            "type_hint": "fact",
            "subject": "Transformer",
            "predicate": "is_a",
            "object": "neural network architecture",
            "importance_score": 0.94,
            "confidence": 0.99
        },
        {
            "id": "e007",
            "content": "Dr. Patel submitted a grant proposal for memory-augmented AI systems",
            "type_hint": "episodic",
            "timestamp": "2024-07-01T09:30:00",
            "participants": ["Dr. Patel"],
            "action": "submitted grant proposal",
            "context": "NSF funding round 2024",
            "importance_score": 0.78
        },
        {
            "id": "e008",
            "content": "attention mechanism",
            "type_hint": "associative",
            "trigger": "attention mechanism",
            "associations": [
                {"content": "self-attention", "strength": 0.95},
                {"content": "Transformer", "strength": 0.92},
                {"content": "query-key-value", "strength": 0.88}
            ],
            "importance_score": 0.65
        },
        {
            "id": "e009",
            "content": "Dr. Chen reviewed three papers on multi-hop reasoning last week",
            "type_hint": "episodic",
            "timestamp": "2024-08-10T16:00:00",
            "participants": ["Dr. Chen"],
            "action": "reviewed papers on multi-hop reasoning",
            "context": "Weekly literature review",
            "importance_score": 0.72
        },
        {
            "id": "e010",
            "content": "backpropagation",
            "type_hint": "associative",
            "trigger": "backpropagation",
            "associations": [
                {"content": "gradient descent", "strength": 0.93},
                {"content": "chain rule", "strength": 0.91},
                {"content": "weight update", "strength": 0.87}
            ],
            "importance_score": 0.60
        },
        {
            "id": "e011",
            "content": "The institute published 42 papers in top-tier venues in 2023",
            "type_hint": "fact",
            "subject": "institute",
            "predicate": "published",
            "object": "42 papers in 2023",
            "importance_score": 0.55,
            "confidence": 0.95
        },
        {
            "id": "e012",
            "content": "overfitting",
            "type_hint": "associative",
            "trigger": "overfitting",
            "associations": [
                {"content": "regularization", "strength": 0.90},
                {"content": "dropout", "strength": 0.88},
                {"content": "data augmentation", "strength": 0.82}
            ],
            "importance_score": 0.58
        }
    ],
    "reasoning_queries": [
        {
            "id": "q001",
            "question": "What is the relationship between Transformer and machine learning?",
            "expected_chain": ["Transformer is a type of neural network architecture", 
                               "Neural networks are the foundation of deep learning",
                               "Deep learning is a subset of machine learning"],
            "expected_answer_keywords": ["Transformer", "machine learning", "deep learning", "neural network"]
        },
        {
            "id": "q002", 
            "question": "What framework did the Memory Networks paper introduce?",
            "expected_chain": ["Memory Networks paper (Weston et al., 2014) introduced the I-G-O-R framework for reasoning with long-term memory"],
            "expected_answer_keywords": ["I-G-O-R", "Memory Networks", "reasoning"]
        }
    ]
}

with open(os.path.join(base, "research_institute/knowledge_base/raw/knowledge_dump.json"), "w") as f:
    json.dump(knowledge_dump, f, indent=2)

# A partially wrong config that the agent must fix/complete
wrong_config = {
    "memory_network": {
        "embedding_dim": 64,
        "max_memory": 500,
        "hops": 1,
        "scoring": {
            "method": "cosine",
            "temperature": 2.0
        },
        "memory_management": {
            "consolidation": False,
            "forgetting_threshold": 0.5,
            "importance_weight": 0.8
        }
    }
}
with open(os.path.join(base, "research_institute/config/drafts/broken_config.json"), "w") as f:
    json.dump(wrong_config, f, indent=2)

# Instructions file (business requirement, not technical hints)
instructions = """RESEARCH INSTITUTE KNOWLEDGE SYSTEM - REQUIREMENTS
===================================================

We need a working knowledge reasoning system implemented in Python.

DELIVERABLES:
1. A Python implementation file: memory_system.py
   - Must implement tiered memory storage for all entries in knowledge_dump.json
   - Must implement multi-hop chain reasoning over the stored knowledge
   - Must process all entries from knowledge_dump.json and store them in the correct tier
   - Must answer the reasoning queries in knowledge_dump.json

2. A corrected system configuration file: system_config.json
   - Based on the broken_config.json in config/drafts/, produce a corrected version
   - All parameters must match the reference architecture specifications

3. A results file: reasoning_results.json
   - Must contain the reasoning chain and answer for each query in knowledge_dump.json
   - Format: {"results": [{"query_id": str, "chain": [str], "answer": str, "hops_used": int}]}

4. A memory_state.json report showing how the entries were distributed across tiers:
   - Format: {"tier1_working": [list of entry ids], "tier2_short_term": [list of entry ids], "tier3_long_term": [list of entry ids]}
"""

with open(os.path.join(base, "REQUIREMENTS.txt"), "w") as f:
    f.write(instructions)

print("Workspace generated successfully.")
print(f"Knowledge dump: {len(knowledge_dump['entries'])} entries, {len(knowledge_dump['reasoning_queries'])} queries")