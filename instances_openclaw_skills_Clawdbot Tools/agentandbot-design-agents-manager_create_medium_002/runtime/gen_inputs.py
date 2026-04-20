from pathlib import Path
import json

base = Path('.')
(base / 'references').mkdir(exist_ok=True)

registry = {
    "agents": [
        {
            "id": "main",
            "name": "Clawdia",
            "model": "glm-4.7",
            "reports_to": {"type": "human", "target": "Ilkerkaan"},
            "can_assign_to": [],
            "requires_approval": False,
            "agent_card": {
                "id": "main",
                "name": "Clawdia",
                "description": "Main orchestrator agent.",
                "capabilities": ["general assistance", "task routing"],
                "input_format": "Natural language",
                "output_format": "Plain text",
                "routing": {"reports_to": "Ilkerkaan", "can_assign_to": []}
            }
        }
    ]
}
(base / 'references' / 'agent-registry.json').write_text(json.dumps(registry, indent=2), encoding='utf-8')

notes = """# Routing Notes\n\n- SAP work should be delegated to a specialized agent when available.\n- If the target agent requires approval, ask the human supervisor first.\n- Non-SAP work should remain with the main agent unless otherwise specified.\n\nMARKER: ROUTING_NOTES_V1\n"""
(base / 'references' / 'task-routing-rules.md').write_text(notes, encoding='utf-8')
