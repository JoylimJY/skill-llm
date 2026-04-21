import csv
import random

random.seed(42)  # deterministic

entries = [
    {"Name": "Alice Smith", "Email": "alice@example.com"},
    {"Name": "Bob Johnson", "Email": "bob@example.com"},
    {"Name": "Carol Lee", "Email": "carol@example.com"},
    {"Name": "David Brown", "Email": "david@example.com"},
    {"Name": "Eve Davis", "Email": "eve@example.com"}
]

with open('participants.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["Name", "Email"])
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)
