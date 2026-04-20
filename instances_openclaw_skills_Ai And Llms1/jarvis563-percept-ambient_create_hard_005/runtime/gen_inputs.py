from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')
input_dir = base / 'input_conversations'
input_dir.mkdir(exist_ok=True)

files = {
    'chat_01.txt': """[2025-04-02 09:15] Maya: Northstar kickoff moved to Thursday.
[2025-04-02 09:17] Leo: Alice from Orion Labs wants a revised milestone plan.
[2025-04-02 09:20] Maya: Please note that Northstar is owned by Priya and Sam.
MARKER:CONV-ALPHA-17
""",
    'chat_02.txt': """[2025-04-03 14:05] Sam: Client onboarding is blocked until legal approves the DPA.
[2025-04-03 14:11] Priya: Orion Labs is the client, and Northstar still needs a timeline update.
[2025-04-03 14:15] Leo: I spoke with Alice; she mentioned the deadline shift again.
MARKER:CONV-BETA-42
""",
    'chat_03.txt': """[2025-04-04 08:30] Maya: The vector index should include the onboarding issue and the deadline change.
[2025-04-04 08:33] Priya: Keep the summary local only, no audio, just transcripts.
[2025-04-04 08:40] Sam: Northstar is related to Orion Labs via the pilot contract.
MARKER:CONV-GAMMA-88
""",
}
for name, content in files.items():
    (input_dir / name).write_text(content, encoding='utf-8')

meta = {
    'seed': 1337,
    'project': 'Northstar',
    'client': 'Orion Labs',
    'markers': ['CONV-ALPHA-17', 'CONV-BETA-42', 'CONV-GAMMA-88']
}
(base / 'input_manifest.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
