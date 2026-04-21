import csv
import random
random.seed(12345)

entries = [
    ("Alice Smith", "alice@example.com"),
    ("Bob Jones", "bob@example.com"),
    ("Carol White", "carol@example.com"),
    ("David Green", "david@example.com"),
    ("Eva Blue", "eva@example.com")
]

with open("entries.csv", "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Email"])
    for name, email in entries:
        writer.writerow([name, email])
