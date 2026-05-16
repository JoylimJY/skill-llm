import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "scripts",
    "docs/legal/drafts",
    "docs/legal/archive",
    "docs/marketing",
    "docs/internal",
    "product/specs",
    "product/releases",
    "assets/icons",
    "assets/fonts",
    "config",
    "tests/unit",
    "tests/integration",
    "build/output",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "docs/legal/archive/old_eula_v1.txt": textwrap.dedent("""\
        OUTDATED EULA - DO NOT USE
        This agreement was valid until 2019.
        License: perpetual, non-transferable.
        No warranty provided.
    """),
    "docs/legal/archive/terms_of_service_draft.txt": textwrap.dedent("""\
        DRAFT ToS - incomplete
        1. Acceptance of Terms
        2. [TODO: fill in]
        3. [TODO: liability]
    """),
    "docs/legal/drafts/nda_template.txt": textwrap.dedent("""\
        NON-DISCLOSURE AGREEMENT TEMPLATE
        This NDA is between [PARTY A] and [PARTY B].
        Confidential information shall not be disclosed.
    """),
    "docs/marketing/press_release_v2.txt": "VectorCraft Pro launches Spring 2025. New features: AI curves, live preview.",
    "docs/internal/legal_notes.txt": "Note: check with counsel on GDPR clause placement. Confirm jurisdiction.",
    "docs/internal/team_contacts.txt": "Legal: legal@vectorcraft.io\nProduct: pm@vectorcraft.io",
    "product/specs/feature_list.md": textwrap.dedent("""\
        # VectorCraft Pro Feature List
        - Bezier curve editor
        - SVG import/export
        - Layer management
        - Cloud sync (optional add-on)
        - Plugin API
    """),
    "product/releases/changelog_v2.3.txt": "v2.3 - Fixed crash on large SVG import. Added dark mode.",
    "config/build.cfg": "BUILD_TARGET=release\nPLATFORM=linux,win,mac\nVERSION=2.3.0",
    "tests/unit/test_license_check.py": "def test_license_check(): assert True  # placeholder",
    "tests/integration/test_activation.py": "def test_activation(): pass  # TODO",
    "assets/icons/placeholder.txt": "icon assets placeholder",
    "assets/fonts/placeholder.txt": "font assets placeholder",
    "build/output/manifest.txt": "build manifest - generated 2025-01-10",
}
for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The main skill scripts directory ---
# The skill script must already exist per instructions: "All scripts mentioned in the SKILL.md already exist"
# We create a realistic script that outputs useful EULA reference content
script_content = r"""#!/usr/bin/env bash
# VectorCraft EULA Reference Tool - Powered by BytesAgain
set -e

EULA_DIR="${EULA_DIR:-$HOME/.eula}"
mkdir -p "$EULA_DIR"

VERSION="1.0.0"
PRODUCT="VectorCraft Pro"

cmd="${1:-help}"

case "$cmd" in
  intro)
    cat <<'EOF'
## EULA Overview

An End User License Agreement (EULA) is a legal contract between a software vendor
and the end user, governing how the software may be used. Unlike a sale, a EULA
grants a *license* — not ownership — of the software.

**EULA vs Terms of Service:**
- EULA: governs installed/downloadable software; accepted at install time
- ToS: governs ongoing service use; typically web-based

**Legal Basis:**
- Contract law: offer (EULA), acceptance (click-wrap/browse-wrap), consideration (license grant)
- Copyright law: software is protected; license defines permitted use
- Breach of EULA can constitute copyright infringement

**Key acceptance mechanisms:**
- Click-wrap: user clicks "I Agree" before installation (strongly enforceable)
- Browse-wrap: user agrees by continued use (weaker enforceability)
- Shrink-wrap: opening package implies acceptance (weakest, often unenforceable)
EOF
    ;;

  grant)
    cat <<'EOF'
## License Grant

The license grant is the core of the EULA — it defines what the user MAY do.

**Required Elements:**
1. **Scope**: Single-user, multi-seat, site license, enterprise, etc.
2. **Exclusivity**: Non-exclusive (standard) or exclusive (rare, negotiated)
3. **Transferability**: Non-transferable (standard) or transferable with notice
4. **Duration**: Perpetual or subscription-based (define term and renewal)
5. **Territory**: Worldwide or region-restricted
6. **Medium**: Installation on N devices, cloud instance, or both

**Sample Grant Language:**
> Subject to the terms of this Agreement, Licensor grants to Licensee a
> non-exclusive, non-transferable, limited license to install and use
> the Software on a single device owned or controlled by Licensee,
> solely for Licensee's internal business purposes.

**Permitted Use Clarifications:**
- Backup copies (one copy permitted for archival purposes)
- Network use: must specify if prohibited or permitted
- Evaluation/trial: time-limited grant with automatic expiry language
EOF
    ;;

  restrictions)
    cat <<'EOF'
## License Restrictions

Restrictions define what the user MUST NOT do. These must be explicit.

**Standard Restrictions (must include all of the following):**
1. No reverse engineering, decompilation, or disassembly
2. No modification, adaptation, or creation of derivative works
3. No redistribution, sublicensing, rental, or lending
4. No removal of proprietary notices (copyright, trademark)
5. No use for unlawful purposes or in violation of applicable law
6. No circumvention of technical protection measures (TPMs)
7. No benchmarking or comparative testing for publication without consent

**Export Control Clause:**
> Licensee shall comply with all applicable export laws and regulations.
> Licensee represents it is not located in a US-embargoed country.

**Audit Rights (commercial licenses):**
> Licensor reserves the right to audit Licensee's use of the Software
> upon reasonable notice to verify compliance with this Agreement.
EOF
    ;;

  ip)
    cat <<'EOF'
## Intellectual Property

**Ownership:**
> The Software, including all copies, modifications, and derivative works,
> is and remains the sole and exclusive property of Licensor.
> This Agreement does not transfer any ownership rights to Licensee.

**Copyright Notice:**
- Must reference copyright holder and year range
- Must state all rights reserved

**Trademarks:**
> All trademarks, service marks, and trade names are the property of
> Licensor. No right or license is granted to use Licensor's marks.

**User-Generated Content / Output:**
> Output files generated by the Software (e.g., documents, images, designs)
> are owned by the Licensee. Licensor claims no ownership over user output.

**Open Source Components:**
> The Software may include open-source components governed by separate
> licenses. A list of open-source components and their licenses is
> available at [URL or Appendix A].

**Feedback Clause:**
> Any feedback, suggestions, or improvements provided by Licensee to
> Licensor may be used by Licensor without restriction or compensation.
EOF
    ;;

  liability)
    cat <<'EOF'
## Liability Limitations & Warranty Disclaimer

**Warranty Disclaimer (MUST be in ALL CAPS or conspicuous format):**
> THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
> EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF
> MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

**Limitation of Liability:**
> IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL,
> SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF
> PROFITS, DATA, OR BUSINESS INTERRUPTION, HOWEVER CAUSED.
>
> LICENSOR'S TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT PAID BY
> LICENSEE FOR THE SOFTWARE IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.

**Indemnification:**
> Licensee shall indemnify and hold harmless Licensor from any claims
> arising from Licensee's use of the Software in violation of this Agreement.

**Exceptions:**
- Some jurisdictions do not allow exclusion of implied warranties
- Include savings clause: "to the extent permitted by applicable law"
EOF
    ;;

  termination)
    cat <<'EOF'
## Termination

**Termination for Breach (automatic):**
> This Agreement terminates automatically and immediately, without notice,
> upon any breach by Licensee of any term of this Agreement.

**Termination for Convenience:**
> Licensee may terminate this Agreement at any time by destroying all
> copies of the Software and certifying such destruction in writing.

**Licensor Termination Right:**
> Licensor may terminate this Agreement upon thirty (30) days written
> notice if Licensee fails to cure a material breach within that period.

**Effects of Termination:**
> Upon termination, Licensee must immediately:
> (a) cease all use of the Software;
> (b) destroy or return all copies, including backups;
> (c) certify compliance in writing upon request.

**Survival Clause (CRITICAL — must explicitly list surviving sections):**
> The following sections survive termination of this Agreement:
> Intellectual Property, Liability Limitations, Indemnification,
> Governing Law, and any accrued obligations.
EOF
    ;;

  enforcement)
    cat <<'EOF'
## Enforceability

**Click-Wrap Best Practices (highest enforceability):**
1. Present full EULA text before acceptance (scrollable, readable)
2. Use affirmative action: "I have read and agree to the terms"
3. Timestamp and log acceptance with user identifier
4. Do not pre-check the acceptance checkbox
5. Provide link to download/print the EULA

**Browse-Wrap Risks:**
- Courts increasingly reject browse-wrap absent conspicuous notice
- Must have prominent hyperlink near action button ("By clicking Download, you agree to our EULA")
- Recommended only as a secondary mechanism

**Unconscionability Defense:**
- Procedural: was the user given meaningful opportunity to read?
- Substantive: are terms unreasonably one-sided?
- Mitigation: plain language, reasonable terms, prominent presentation

**Governing Law & Dispute Resolution:**
> This Agreement is governed by the laws of [State/Country], without
> regard to conflict of laws principles. Any dispute shall be resolved
> by binding arbitration in [City, State] under [AAA/JAMS] rules,
> except Licensor may seek injunctive relief in any court of competent
> jurisdiction.

**Severability:**
> If any provision of this Agreement is found invalid, the remaining
> provisions continue in full force and effect.

**Entire Agreement:**
> This Agreement constitutes the entire agreement between the parties
> and supersedes all prior negotiations, representations, or agreements.
EOF
    ;;

  checklist)
    cat <<'EOF'
## EULA Drafting Checklist

Use this checklist to verify completeness before finalizing any EULA.

### Identity & Parties
- [ ] Full legal name of Licensor (software vendor)
- [ ] Definition of "Licensee" (individual, business entity, or both)
- [ ] Effective date or "as of installation" language

### License Grant
- [ ] Scope defined (single-user, multi-seat, enterprise)
- [ ] Non-exclusive and non-transferable stated explicitly
- [ ] Duration specified (perpetual or subscription term)
- [ ] Permitted devices/installations number stated
- [ ] Backup copy allowance addressed

### Restrictions
- [ ] Reverse engineering prohibited
- [ ] Redistribution and sublicensing prohibited
- [ ] No removal of proprietary notices
- [ ] Export control clause included
- [ ] Unlawful use prohibited

### Intellectual Property
- [ ] Licensor retains all ownership
- [ ] Copyright notice included
- [ ] Trademark non-use clause
- [ ] User output ownership addressed
- [ ] Open source component disclosure (if applicable)
- [ ] Feedback clause included

### Liability & Warranty
- [ ] "AS IS" warranty disclaimer (conspicuous/ALL CAPS)
- [ ] Consequential damages exclusion
- [ ] Liability cap (e.g., 12-month fees paid)
- [ ] Indemnification clause
- [ ] Savings clause for jurisdictions that restrict disclaimers

### Termination
- [ ] Automatic termination on breach
- [ ] Termination for convenience by Licensee
- [ ] Effects of termination (cease use, destroy copies)
- [ ] Survival clause with explicitly listed surviving sections

### Enforceability
- [ ] Acceptance mechanism defined (click-wrap preferred)
- [ ] Governing law and jurisdiction specified
- [ ] Dispute resolution / arbitration clause
- [ ] Severability clause
- [ ] Entire Agreement / Integration clause

### Optional but Recommended
- [ ] Updates and upgrades policy
- [ ] Privacy policy cross-reference
- [ ] Support and maintenance terms (or reference to separate SLA)
- [ ] Amendment procedure
EOF
    ;;

  version)
    echo "eula skill version $VERSION"
    ;;

  help|*)
    cat <<'EOF'
EULA Reference Skill - BytesAgain v1.0.0

Usage: scripts/script.sh <command>

Commands:
  intro        Overview of EULAs, legal basis, EULA vs ToS
  grant        License grant clauses — scope, limitations, permitted use
  restrictions Common restrictions — reverse engineering, redistribution
  ip           Intellectual property clauses — ownership, trademarks
  liability    Liability limitations, warranty disclaimers, indemnification
  termination  Termination clauses — breach, convenience, effects, survival
  enforcement  Enforceability — click-wrap, browse-wrap, unconscionability
  checklist    EULA drafting checklist
  help         Show this help message
  version      Show version

Configuration:
  EULA_DIR     Data directory (default: ~/.eula/)
EOF
    ;;
esac
"""

script_path = os.path.join(BASE, "scripts", "script.sh")
with open(script_path, "w") as f:
    f.write(script_content)

# --- Product brief that agent needs to incorporate ---
product_brief = textwrap.dedent("""\
    PRODUCT BRIEF — VectorCraft Pro 2.3
    =====================================
    Vendor (Licensor): VectorCraft Technologies, Inc.
    Product: VectorCraft Pro
    Version: 2.3.0
    Target Market: Freelance designers and small creative agencies
    License Model: Single-user, perpetual license (non-subscription)
    Price Point: $149 one-time purchase per seat
    Platforms: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+)
    Max Installs per License: 2 devices (owned by same individual)
    Includes Plugin API: Yes (third-party plugins allowed, but redistribution of core software prohibited)
    Open Source Components: Yes (libpng, zlib, FreeType — see Appendix A)
    Acceptance Mechanism: Click-wrap dialog at first launch
    Governing Law: State of Delaware, USA
    Dispute Resolution: Binding arbitration (AAA rules), Delaware
    Support: Community forum only; no SLA
    Copyright Year: 2025
    
    LEGAL NOTES:
    - Users own their output files (SVG, PNG, PDF exports)
    - No cloud component; all processing is local
    - Export control: standard US export compliance required
    - No telemetry or user data collection in v2.3
""")

brief_path = os.path.join(BASE, "docs/legal/product_brief.txt")
with open(brief_path, "w") as f:
    f.write(product_brief)

# --- A messy incomplete internal EULA fragment to NOT use as-is ---
incomplete_fragment = textwrap.dedent("""\
    INTERNAL FRAGMENT - INCOMPLETE - DO NOT FINALIZE
    
    1. LICENSE
    We grant you a license to use the software. Don't abuse it.
    
    2. RESTRICTIONS
    Don't reverse engineer or redistribute.
    
    3. TERMINATION
    We can terminate if you violate these terms.
    
    *** MISSING: IP clause, liability, enforcement, survival, checklist review ***
""")
fragment_path = os.path.join(BASE, "docs/legal/drafts/incomplete_eula_fragment.txt")
with open(fragment_path, "w") as f:
    f.write(incomplete_fragment)

print("Workspace generated successfully.")
print(f"Files created under: {BASE}")