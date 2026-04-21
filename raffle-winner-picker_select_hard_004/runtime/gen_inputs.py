import pandas as pd
import numpy as np

def create_excel():
    np.random.seed(42)
    ids = range(1, 501)
    names = [f"Participant_{i:03d}" for i in ids]
    emails = [f"user{i:03d}@example.com" for i in ids]
    # Entries from 1 to 10
    entries = np.random.randint(1, 11, size=500)
    # Randomly assign Status: 80% Eligible, 20% Disqualified
    statuses = np.where(np.random.rand(500) < 0.8, "Eligible", "Disqualified")

    df = pd.DataFrame({
        "ID": ids,
        "Name": names,
        "Email": emails,
        "Entries": entries,
        "Status": statuses
    })
    df.to_excel("contest-entries.xlsx", index=False)

if __name__ == "__main__":
    create_excel()
