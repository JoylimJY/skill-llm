import openpyxl
from openpyxl import Workbook

# Fixed seed for deterministic output
import random
random.seed(42)

wb = Workbook()
ws = wb.active
ws.title = "Entries"
cols = ["ID", "Name", "Email", "Entries"]
ws.append(cols)

# Create 12 entries with known markers
names = ["Alice Smith", "Bob Jones", "Carol White", "David Brown", "Eva Green", "Frank Black", "Grace Liu", "Henry Ford", "Ivy Scott", "Jack Lee", "Kara Wang", "Leo Kim"]
emails = ["alice@example.com", "bob@example.com", "carol@example.com", "david@example.com", "eva@example.com", "frank@example.com", "grace@example.com", "henry@example.com", "ivy@example.com", "jack@example.com", "kara@example.com", "leo@example.com"]
entries = [5, 3, 2, 4, 1, 6, 3, 2, 1, 4, 2, 7]

for i in range(12):
    ws.append([i + 1, names[i], emails[i], entries[i]])

# Save the file named exactly
wb.save("contest-entries.xlsx")
