from pathlib import Path

marker = "ATLAS_SYNC_MARKER_2025"
files = {
    "seed_notes.txt": f"Project: atlas-sync\nMarker: {marker}\nCore docs: TASK.md, CHANGELOG.md, CONTEXT.md, WEEKLY-REPORT.md, llms.txt\n",
    "reference_manifest.json": '{"project":"atlas-sync","marker":"ATLAS_SYNC_MARKER_2025","documents":["TASK.md","CHANGELOG.md","CONTEXT.md","WEEKLY-REPORT.md","llms.txt"]}\n',
}
for name, content in files.items():
    Path(name).write_text(content, encoding="utf-8")
