from pathlib import Path
import json

workspace = Path('.')
notes = workspace / 'wallet_notes.txt'
ledger = workspace / 'transaction_markers.csv'

notes.write_text(
    'Agent payout target: Base chain\n'
    'Recipient label: QA-Runner\n'
    'Recipient address: 0x8c6d2f0b2a4f7d8c3e1a9b6f5d4c7e8a9b0c1d2e\n'
    'Asset: USDC\n'
    'Requested amount: 125.50\n'
    'Reference note: BOUNTY-ALPHA-2048\n'
    'Marker: WALLET-NOTE-7F3A\n',
    encoding='utf-8'
)

ledger.write_text(
    'marker,chain,token,amount,tx_hint\n'
    'TX-1001,8453,USDC,125.50,first-pass\n'
    'TX-1002,8453,USDC,12.00,refund\n'
    'TX-1003,1,ETH,0.05,legacy\n',
    encoding='utf-8'
)
