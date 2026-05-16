# Privacy and Boundaries

## Storage

- Current version stores data locally in JSON files under `~/.openclaw/skills-data/looking-for-someone/`.
- Current version does not implement field-level encryption.
- Current version does not implement image matching, face recognition, or identity verification.
- Current version does not connect to police systems, surveillance systems, or real-time social network search.

## Output rules

- Do not expose exact home address, bank card number, verification code, or full ID number.
- Mask identity numbers if the user provides them.
- Treat clues as unverified information unless independently confirmed.
- For high-risk missing cases, recommend报警 and official channels first.

## Scam escalation

Prioritize warnings when someone:

- asks for money before giving clues
- asks for personal financial information
- claims to be police without a verifiable identity
- asks the family to install suspicious software or enable screen sharing
- asks to click unknown links or download unknown apps
