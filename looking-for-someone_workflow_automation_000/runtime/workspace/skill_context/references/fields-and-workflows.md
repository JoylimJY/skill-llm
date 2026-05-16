# Fields and Workflows

## Core case fields

Required fields for a minimally useful case:

- name
- age
- gender
- lastSeenDate
- lastSeenLocation

Optional but recommended:

- phone
- birthDate
- idNumber
- height
- clothing
- distinguishingFeatures
- circumstances
- possibleDestinations
- familyContacts

## Suggested workflow

1. Create a case with the core facts first.
2. If the case is high risk, tell the user to报警 immediately.
3. Add appearance details and family contact information.
4. Add clues as they arrive and mark them for later verification.
5. Generate a poster only after checking the user is comfortable with the exposed fields.
6. Review progress and next actions regularly.
7. Reiterate scam warnings whenever a stranger claims to have a clue.

## Caveats

- Current clue analysis is heuristic, not investigative proof.
- Current platform poster generation is text-only.
- Current implementation is local record-keeping plus guidance, not active search.
