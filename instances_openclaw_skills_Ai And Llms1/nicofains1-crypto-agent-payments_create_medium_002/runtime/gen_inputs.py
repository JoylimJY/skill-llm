from pathlib import Path

base = Path('.')

(base / 'wallet_notes.txt').write_text(
    'Project: OnlySwaps demo\n'
    'CHAIN: Base (8453)\n'
    'WALLET_MARKER: DEMO-WALLET-ALPHA-42\n'
    'PRIVATE_KEY_POLICY: use_existing_or_create_new\n'
    'COMMENT: This file contains the unique marker for eval verification.\n',
    encoding='utf-8'
)

(base / 'transfer_plan.csv').write_text(
    'token,to_address,amount,amount_format,chain_id\n'
    'USDC,0x1111111111111111111111111111111111111111,12.5,human,8453\n',
    encoding='utf-8'
)

(base / 'instructions.json').write_text(
    '{"task":"prepare-summary","required_fields":["wallet_marker","chain","token","amount_format"]}\n',
    encoding='utf-8'
)

(base / 'expected_marker.txt').write_text(
    'DEMO-WALLET-ALPHA-42\n',
    encoding='utf-8'
)
