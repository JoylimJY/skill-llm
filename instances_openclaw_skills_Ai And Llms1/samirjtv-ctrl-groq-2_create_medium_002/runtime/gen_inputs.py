import os
from pathlib import Path


def main():
    notes = [
        "  Customer asked about refund timing  ",
        "Shipment delayed due to weather",
        "customer asked about refund timing",
        "Need follow-up on invoice #4821",
        "SHIPMENT delayed due to weather  ",
        "  Password reset instructions sent ",
    ]
    Path('support_notes.txt').write_text('\n'.join(notes) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()