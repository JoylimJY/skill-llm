import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create a realistic, messy directory structure for a boutique media agency
dirs = [
    "intake/2024/Q3",
    "intake/2024/Q4",
    "intake/2025/Q1",
    "archive/released",
    "archive/drafts",
    "collab/external_partners",
    "collab/tools_output",
    "distribution/platform_configs",
    "distribution/pending_review",
    "admin/contracts",
    "admin/invoices",
    "admin/correspondence",
    "assets/audio",
    "assets/visual",
    "assets/video",
    "temp/scratch",
    "temp/exports",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# Old release notes
with open(os.path.join(BASE, "archive/released/release_notes_2024.txt"), "w") as f:
    f.write("Q3 2024 releases: tracks 001-045 cleared for YouTube, Spotify.\nQ4 2024: visual pack V12 released to Getty.\n")

# Platform config (irrelevant)
with open(os.path.join(BASE, "distribution/platform_configs/youtube_settings.json"), "w") as f:
    json.dump({"monetization": True, "default_lang": "en", "auto_chapters": False}, f, indent=2)

with open(os.path.join(BASE, "distribution/platform_configs/spotify_settings.json"), "w") as f:
    json.dump({"explicit_filter": False, "territory": "GLOBAL", "mood_tags": ["ambient", "lo-fi"]}, f, indent=2)

# Invoice distractor
with open(os.path.join(BASE, "admin/invoices/inv_0042.txt"), "w") as f:
    f.write("Invoice #0042\nClient: NovaBrand Inc.\nServices: Sync license consultation\nAmount: $1,200.00\n")

# Old contract stub
with open(os.path.join(BASE, "admin/contracts/collab_agreement_draft.txt"), "w") as f:
    f.write("DRAFT - NOT EXECUTED\nParties: Meridian Audio LLC and SkyVault Productions\nTerm: 12 months from signing\n[REDACTED - pending legal review]\n")

# Scratch exports
with open(os.path.join(BASE, "temp/exports/batch_export_log.txt"), "w") as f:
    f.write("Batch export 2025-01-10 03:12 UTC\nFiles: 17 audio, 5 visual\nStatus: COMPLETE\nWarnings: 2 files missing ISRC\n")

# Collab partner notes
with open(os.path.join(BASE, "collab/external_partners/partner_list.csv"), "w") as f:
    f.write("PartnerID,Name,Specialty,ContactEmail\n"
            "P001,Lena Voss,Vocals,lena@example.net\n"
            "P002,DeepBeat Studio,Mixing,info@deepbeat.example\n"
            "P003,ArtiGen LLC,AI Visuals,contact@artigen.example\n")

# Tools output log
with open(os.path.join(BASE, "collab/tools_output/ai_assist_log.txt"), "w") as f:
    f.write("Session: 2025-01-15\nTool: HarmonizerAI v2.3\nPrompt tokens used: 4412\nOutput: melody scaffold for track MBLX-009\n")

# Draft intake form (incomplete, from a different quarter)
with open(os.path.join(BASE, "intake/2024/Q3/intake_form_draft.txt"), "w") as f:
    f.write("Asset: VIS-2024-003\nStatus: DRAFT - do not process\nAuthor: Unknown\nNote: awaiting final approvals from legal\n")

# Archived visual pack note
with open(os.path.join(BASE, "archive/drafts/visual_pack_v11_notes.txt"), "w") as f:
    f.write("V11 was rejected due to unresolved third-party sample question.\nDo not distribute.\nSee admin/contracts for context.\n")

# Pending review note
with open(os.path.join(BASE, "distribution/pending_review/hold_notice.txt"), "w") as f:
    f.write("Assets on hold pending creator sign-off: MBLX-009, VIS-2025-001\nDeadline for response: 2025-02-01\n")

# Admin correspondence distractor
with open(os.path.join(BASE, "admin/correspondence/platform_inquiry_2025.txt"), "w") as f:
    f.write("From: partnerops@platformX.example\nRe: Missing attribution metadata on recent uploads\n"
            "Several assets uploaded in Jan 2025 are missing creator credit information.\n"
            "Please resubmit with complete provenance declarations.\n")

# --- THE ACTUAL MESSY INTAKE FORMS (the agent's real input) ---
# These are raw, unstructured, inconsistent intake submissions for 3 assets
# that need to be turned into proper ABC records

intake_asset_1 = """
=== INTAKE FORM - MEDIABLOX INTERNAL ===
Submitted: January 18, 2025, 14:32 EST
Submitted by: Jasper Kline (producer)

Asset internal code: MBLX-2025-011
Asset type: Audio track (electronic/ambient)

Who made it?
  - Jasper Kline (primary composer, all stems from scratch)
  - No collaborators. No AI tools used. 100% human work.

License info:
  Use only for sync licensing. Territory: North America only.
  Duration: 2 years from finalization (expires Jan 2027).
  Source/ref: License template on file as LIC-SYNC-NA-2YR

How should we credit it?
  Public credit: "Composed by Jasper Kline | MediaBlox 2025"
  YouTube descriptions only - no character limit issues expected.

Extra notes:
  This is version 1.0, no prior revisions.
  I finalized this track on January 18, 2025 at 14:00 EST.

File hash I calculated myself: a3f8c2d1e4b09f76a3f8c2d1e4b09f76a3f8c2d1e4b09f76a3f8c2d1e4b09f76
"""

intake_asset_2 = """
=== INTAKE FORM - MEDIABLOX INTERNAL ===
Submitted: January 20, 2025
Submitted by: Rhea Solano (visual director)

Asset code: VIS-2025-007
What is it: Album cover art / digital illustration

About the creation process:
  Rhea Solano designed the composition and directed overall aesthetic.
  Background textures were generated using ArtiGen LLC's AI tool (see partner list).
  Final assembly, color grading, and typography were done manually by Rhea.

License:
  Worldwide rights. No expiration set - perpetual use.
  Source: Internal blanket visual license - ref VLIC-GLOBAL-PERP
  Restriction: Cannot be used in NFT minting or on-chain platforms.

Attribution:
  "Art Direction: Rhea Solano | AI-assisted textures via ArtiGen | MediaBlox 2025"
  Note for Instagram: keep under 100 chars if possible. Suggested short form: "© Rhea Solano x ArtiGen | MediaBlox"

Revision history:
  v1.0 - Jan 15 scratch
  v2.0 - Jan 18 color revision
  v3.0 FINAL - Jan 20, 2025 (this submission)

Content hash: NOT COMPUTED YET
"""

intake_asset_3 = """
=== INTAKE FORM - MEDIABLOX INTERNAL ===
Date finalized: 2025-01-22
Submitted by: Pipeline automation / no human submitter

Asset ID: MBLX-2025-013
Type: Ambient soundscape loop

Process: FULLY generated by HarmonizerAI v2.3 (see tools_output log). No human creative input beyond the initial prompt. Prompt author: Jasper Kline.

Rights/License:
  Internal use ONLY. Territory: N/A (internal).
  Duration: Indefinite / until revoked.
  Reference doc: INT-USE-ONLY-POLICY-v2

Attribution:
  "Generated by HarmonizerAI v2.3 | Prompted by Jasper Kline | MediaBlox 2025"
  No platform-specific notes.

Content hash: 9b1d4e72f305a8c69b1d4e72f305a8c69b1d4e72f305a8c69b1d4e72f305a8c6

Contributor context: Prompt engineering by Jasper Kline via HarmonizerAI session 2025-01-15.

Version: First and only. Finalized 2025-01-22 09:00 UTC.
"""

# Write the intake forms as messy text files
with open(os.path.join(BASE, "intake/2025/Q1/intake_MBLX-2025-011.txt"), "w") as f:
    f.write(intake_asset_1)

with open(os.path.join(BASE, "intake/2025/Q1/intake_VIS-2025-007.txt"), "w") as f:
    f.write(intake_asset_2)

with open(os.path.join(BASE, "intake/2025/Q1/intake_MBLX-2025-013.txt"), "w") as f:
    f.write(intake_asset_3)

# Write a cover memo that explains the business request (but not HOW to do it)
cover_memo = """
TO: Rights & Metadata Team
FROM: Distribution Operations
DATE: January 22, 2025
RE: Q1 2025 Asset Catalog — Pre-Distribution Records Required

We have three new assets ready for distribution review (see intake forms in intake/2025/Q1/).

Before any of these assets can be forwarded to platform partners, we need complete
standardized rights and provenance records on file for each one.

These records are a hard requirement from our platform partners following the January
correspondence from platformX (see admin/correspondence/).

Please generate a single file called catalog_records.json that contains the
formalized records for all three assets: MBLX-2025-011, VIS-2025-007, and MBLX-2025-013.

The records must follow our internal documentation standard for newly finalized assets.
The tool/skill we use for this is described in our internal knowledge base (SKILL.md).

Note: VIS-2025-007's content hash has not been provided. You will need to compute a
SHA-256 hash of the asset's credit string as a stand-in fingerprint until the actual
file can be processed.

— Distribution Ops
"""

with open(os.path.join(BASE, "intake/2025/Q1/COVER_MEMO.txt"), "w") as f:
    f.write(cover_memo)

print("Workspace generated successfully.")