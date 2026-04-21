import random
from openpyxl import Workbook

random.seed(12345)

wb = Workbook()
ws = wb.active
ws.title = "Entries"

headers = ["Participant ID", "Name", "Email", "Entries"]
ws.append(headers)

# Create 100 deterministic participants with varied weights
for i in range(1, 101):
    participant_id = f"PID{i:03d}"
    name = f"Participant{i}"
    email = f"participant{i}@email.com"
    # Entries vary between 1 and 10 in a repeatable pattern
    entries = (i % 10) + 1
    ws.append([participant_id, name, email, entries])

wb.save("contest-entries.xlsx")

# Marker comment for eval verification
with open("marker.txt", "w") as f:
    f.write("[MARKER-Weighted-Contest-Entries-100]")
