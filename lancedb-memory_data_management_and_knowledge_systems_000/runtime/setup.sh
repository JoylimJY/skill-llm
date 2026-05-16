#!/bin/bash
set -e

echo "=== Setting up LanceDB memory management sandbox ==="

# Make workspace writable
chmod -R 755 /workspace

# Write the SKILL.md implementation as memory_skill.py in workspace
cat > /workspace/memory_skill.py << 'PYEOF'
#!/usr/bin/env python3
"""
LanceDB integration for long-term memory management.
Provides vector search and semantic memory capabilities.
"""

import os
import json
import lancedb
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class LanceMemoryDB:
    """LanceDB wrapper for long-term memory storage and retrieval."""

    def __init__(self, db_path: str = "/workspace/lab_memory/lancedb"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.db_path))

        # Ensure memory table exists
        if "memory" not in self.db.table_names():
            self._create_memory_table()

    def _create_memory_table(self):
        """Create the memory table with appropriate schema."""
        import pyarrow as pa
        schema = pa.schema([
            pa.field("id", pa.int64(), nullable=False),
            pa.field("timestamp", pa.timestamp("us"), nullable=False),
            pa.field("content", pa.utf8(), nullable=False),
            pa.field("category", pa.utf8(), nullable=True),
            pa.field("tags", pa.list_(pa.utf8()), nullable=True),
            pa.field("importance", pa.int64(), nullable=True),
            pa.field("metadata", pa.utf8(), nullable=True),
        ])
        self.db.create_table("memory", schema=schema)

    def add_memory(self, content: str, category: str = "general", tags: List[str] = None,
                   importance: int = 5, metadata: Dict[str, Any] = None) -> int:
        """Add a new memory entry."""
        table = self.db.open_table("memory")

        df = table.to_pandas()
        max_id = int(df["id"].max()) if len(df) > 0 else 0
        new_id = max_id + 1

        memory_data = [{
            "id": new_id,
            "timestamp": datetime.now(),
            "content": content,
            "category": category,
            "tags": tags or [],
            "importance": importance,
            "metadata": json.dumps(metadata or {}),
        }]

        table.add(memory_data)
        return new_id

    def get_memories_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get memories by category."""
        table = self.db.open_table("memory")
        df = table.to_pandas()
        filtered = df[df["category"] == category].head(limit)
        return filtered.to_dict("records")

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict]:
        """Get a specific memory by ID."""
        table = self.db.open_table("memory")
        df = table.to_pandas()
        result = df[df["id"] == memory_id]
        return result.to_dict("records")[0] if len(result) > 0 else None

    def update_memory(self, memory_id: int, **kwargs) -> bool:
        """Update a memory entry."""
        table = self.db.open_table("memory")

        valid_fields = ["content", "category", "tags", "importance", "metadata"]
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}

        if not updates:
            return False

        # Apply updates row by row via pandas
        df = table.to_pandas()
        mask = df["id"] == memory_id
        if mask.sum() == 0:
            return False

        for field, value in updates.items():
            if field == "tags" and isinstance(value, list):
                df.loc[mask, field] = [value] * mask.sum()
            elif field == "metadata" and isinstance(value, dict):
                df.loc[mask, field] = json.dumps(value)
            elif field == "metadata" and isinstance(value, str):
                df.loc[mask, field] = value
            elif field == "importance":
                df.loc[mask, field] = int(value)
            else:
                df.loc[mask, field] = value

        # Overwrite table
        self.db.drop_table("memory")
        import pyarrow as pa
        schema = pa.schema([
            pa.field("id", pa.int64(), nullable=False),
            pa.field("timestamp", pa.timestamp("us"), nullable=False),
            pa.field("content", pa.utf8(), nullable=False),
            pa.field("category", pa.utf8(), nullable=True),
            pa.field("tags", pa.list_(pa.utf8()), nullable=True),
            pa.field("importance", pa.int64(), nullable=True),
            pa.field("metadata", pa.utf8(), nullable=True),
        ])
        new_table = self.db.create_table("memory", schema=schema)
        # Re-add rows
        records = df.to_dict("records")
        if records:
            new_table.add(records)
        return True

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory entry."""
        table = self.db.open_table("memory")
        current_count = len(table)
        table.delete(f"id = {memory_id}")
        return len(table) < current_count

    def get_all_categories(self) -> List[str]:
        """Get all unique categories."""
        table = self.db.open_table("memory")
        df = table.to_pandas()
        return df["category"].dropna().unique().tolist()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory storage."""
        table = self.db.open_table("memory")
        df = table.to_pandas()

        return {
            "total_memories": len(df),
            "categories": len(self.get_all_categories()),
            "by_category": df["category"].value_counts().to_dict(),
            "date_range": {
                "earliest": df["timestamp"].min().isoformat() if len(df) > 0 else None,
                "latest": df["timestamp"].max().isoformat() if len(df) > 0 else None,
            },
        }
PYEOF

chmod +x /workspace/memory_skill.py
echo "memory_skill.py written to /workspace"

# Create the output directory for the DB
mkdir -p /workspace/lab_memory/lancedb

echo "=== Setup complete ==="