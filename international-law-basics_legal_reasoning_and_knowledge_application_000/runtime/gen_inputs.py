import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "case_files/preliminary_objections",
    "case_files/merits",
    "case_files/jurisdiction",
    "research/treaties",
    "research/custom_law",
    "research/domestic_law",
    "team_notes/applicant",
    "team_notes/respondent",
    "competition_rules/jessup_2024",
    "competition_rules/jessup_2023",
    "references/icj_statute",
    "references/vclt",
    "drafts/memorials",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "case_files/preliminary_objections/timeline.txt": (
        "2019-03-01: Ruritania signs the Seabed Resources Convention\n"
        "2020-06-15: Arcadia ratifies the Seabed Resources Convention\n"
        "2021-09-10: Ruritania completes domestic ratification\n"
        "2022-01-01: Seabed Resources Convention enters into force for both parties\n"
        "2023-04-22: Arcadia begins deep-seabed extraction activities\n"
        "2023-07-14: Ruritania protests Arcadia's extraction activities\n"
        "2023-11-05: Ruritania notifies Arcadia of intent to terminate the Convention\n"
        "2024-02-20: Ruritania files ICJ Application\n"
    ),
    "case_files/merits/facts_summary.txt": (
        "FACTS SUMMARY - Ruritania v. Arcadia\n\n"
        "1. The Seabed Resources Convention (SRC) was negotiated over three years and opened for signature in 2019.\n"
        "2. Both Ruritania and Arcadia signed the SRC in 2019.\n"
        "3. Arcadia ratified the SRC in June 2020; Ruritania ratified in September 2021.\n"
        "4. Between signing (2019) and its own ratification (2021), Ruritania conducted a series of exploratory drilling operations in disputed seabed areas.\n"
        "5. Arcadia claims these drilling operations violated obligations created at signature.\n"
        "6. After full ratification, Arcadia began large-scale commercial extraction.\n"
        "7. Ruritania protests the extraction as a material breach of Article 7 of the SRC.\n"
        "8. Ruritania unilaterally declared the SRC 'terminated' via a press release by its Foreign Ministry in November 2023.\n"
        "9. Ruritania did not follow any formal notification process before issuing the press release.\n"
        "10. Arcadia denies breach and argues the SRC remains in force.\n"
    ),
    "case_files/jurisdiction/compromissory_clause.txt": (
        "Article 22 of the Seabed Resources Convention:\n"
        "'Any dispute between States Parties concerning the interpretation or application of this Convention "
        "that cannot be settled by negotiation shall, at the request of either party, be submitted to the "
        "International Court of Justice.'\n"
    ),
    "research/treaties/seabed_resources_convention_excerpts.txt": (
        "Seabed Resources Convention (SRC) - Key Provisions\n\n"
        "Article 3: States Parties shall not conduct commercial extraction of seabed mineral resources "
        "within 200 nautical miles of another State Party's coastline without prior notification.\n\n"
        "Article 7: States Parties undertake to refrain from unilateral exploratory drilling in disputed "
        "zones pending joint assessment under Article 9.\n\n"
        "Article 9: A Joint Technical Commission shall assess disputed zone boundaries within 18 months "
        "of a formal dispute notification.\n\n"
        "Article 14: No reservations may be made to this Convention.\n\n"
        "Article 22: [Compromissory clause - see separate file]\n"
    ),
    "research/custom_law/state_practice_notes.txt": (
        "RESEARCHER NOTES: State Practice on Seabed Drilling Moratoriums\n\n"
        "- 47 of 52 surveyed states impose moratoriums on disputed seabed drilling pending boundary resolution\n"
        "- 3 states (Gondoria, Pacifica, Norstland) have consistently refused to accept moratorium obligations "
        "since the 1990s, filing formal objections at every relevant international forum\n"
        "- State Dept. cables from 15 states explicitly state drilling moratoriums reflect 'legal obligation'\n"
        "- 2 states practice moratoriums but describe them as 'courtesy' in official statements\n"
        "- Duration of practice: consistent since at least 1985\n"
        "- Gondoria, Pacifica, and Norstland have objected AT EVERY STAGE of rule formation\n"
    ),
    "research/domestic_law/arcadia_mining_statute.txt": (
        "ARCADIA SEABED RESOURCES ACT (2018)\n"
        "Section 4: Commercial extraction operations in international seabed areas shall be conducted "
        "in compliance with applicable international agreements.\n"
        "Section 7: The Ministry of Resources shall obtain Foreign Ministry clearance before commencing "
        "any extraction within disputed maritime zones.\n"
    ),
    "team_notes/applicant/argument_skeleton.txt": (
        "APPLICANT (RURITANIA) ARGUMENT SKELETON - PRELIMINARY\n\n"
        "Issue 1: Was Ruritania bound by the SRC before its ratification was complete?\n"
        "Issue 2: Did Arcadia commit material breach of Article 7 SRC?\n"
        "Issue 3: Is the SRC validly terminated?\n"
        "Issue 4: Does the drilling moratorium rule bind Arcadia as a matter of general international law?\n"
        "Issue 5: Does the moratorium rule bind Gondoria, Pacifica, and Norstland?\n"
    ),
    "team_notes/respondent/counterargument_notes.txt": (
        "RESPONDENT (ARCADIA) INITIAL NOTES\n\n"
        "- Ruritania's pre-ratification drilling: argue no binding obligations existed yet\n"
        "- Our extraction: argue Article 7 only covers 'disputed zones' - ours is not disputed\n"
        "- Treaty termination: Ruritania's press release is procedurally defective\n"
        "- Customary law: our practice is consistent, we accept moratorium rule\n"
        "- Third-party states: whether the moratorium rule binds objecting states is separate question\n"
    ),
    "competition_rules/jessup_2024/scoring_criteria.txt": (
        "Jessup 2024 Scoring Criteria (excerpt)\n"
        "- Legal argument quality: 40 points\n"
        "- Use of authorities: 25 points\n"
        "- Responsiveness to questions: 20 points\n"
        "- Presentation and organization: 15 points\n"
    ),
    "competition_rules/jessup_2023/past_problem_themes.txt": (
        "Jessup 2023 Problem Themes:\n"
        "- State responsibility\n"
        "- Diplomatic protection\n"
        "- Environmental obligations\n"
        "- Countermeasures\n"
    ),
    "references/icj_statute/article_38_text.txt": (
        "Article 38, Statute of the International Court of Justice\n\n"
        "1. The Court, whose function is to decide in accordance with international law such disputes "
        "as are submitted to it, shall apply:\n"
        "a. international conventions, whether general or particular, establishing rules expressly "
        "recognized by the contesting states;\n"
        "b. international custom, as evidence of a general practice accepted as law;\n"
        "c. the general principles of law recognized by civilized nations;\n"
        "d. subject to the provisions of Article 59, judicial decisions and the teachings of the most "
        "highly qualified publicists of the various nations, as a subsidiary means for the determination "
        "of rules of law.\n"
    ),
    "references/vclt/vclt_full_title.txt": (
        "Vienna Convention on the Law of Treaties\n"
        "Done at Vienna, 23 May 1969\n"
        "Entered into force: 27 January 1980\n"
        "Depositary: United Nations Secretary-General\n"
    ),
    "drafts/memorials/outline_v1.txt": (
        "MEMORIAL OUTLINE v1 - INCOMPLETE\n\n"
        "I. Jurisdiction and Admissibility\n"
        "   A. Jurisdiction under Art. 22 SRC\n"
        "   B. ...\n"
        "II. Merits\n"
        "   A. Pre-ratification obligations\n"
        "   B. ...\n"
        "[REST TO BE COMPLETED]\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUT: The scenario briefing document ---
scenario = {
    "competition": "Jessup International Law Moot Court",
    "case_title": "Ruritania v. Arcadia",
    "year": 2024,
    "parties": {
        "applicant": "Ruritania",
        "respondent": "Arcadia"
    },
    "treaties_signed_and_ratified_by_both_parties": [
        "Seabed Resources Convention (SRC)",
        "Vienna Convention on the Law of Treaties (VCLT)"
    ],
    "legal_issues": [
        {
            "issue_id": "ISSUE_1",
            "label": "Pre-ratification obligations",
            "description": (
                "Between the date both states SIGNED the SRC and the date Ruritania RATIFIED it, "
                "Ruritania conducted exploratory drilling in disputed seabed zones contrary to SRC Article 7. "
                "Arcadia argues Ruritania was already bound by an obligation not to frustrate the treaty's "
                "object and purpose. Ruritania argues it had no binding treaty obligations before ratification."
            )
        },
        {
            "issue_id": "ISSUE_2",
            "label": "Material breach and treaty termination",
            "description": (
                "Ruritania claims Arcadia's commercial extraction activities constitute a material breach "
                "of Article 7 SRC. Ruritania then issued a press release declaring the SRC 'terminated.' "
                "Arcadia argues: (a) no material breach occurred, and (b) even if it did, Ruritania's "
                "termination declaration is legally ineffective."
            )
        },
        {
            "issue_id": "ISSUE_3",
            "label": "Customary international law - drilling moratorium",
            "description": (
                "Even if the SRC is terminated, Ruritania argues that a customary international law rule "
                "requiring a moratorium on disputed seabed drilling exists independently. Arcadia does not "
                "dispute the existence of this rule. However, the question arises whether this rule also "
                "binds Gondoria, Pacifica, and Norstland, which have objected to this rule at every stage "
                "of its development."
            )
        },
        {
            "issue_id": "ISSUE_4",
            "label": "Treaty interpretation - scope of Article 7 SRC",
            "description": (
                "Arcadia argues that its extraction site is not in a 'disputed zone' within the meaning of "
                "Article 7 SRC. Ruritania argues that 'disputed zone' should be interpreted broadly. "
                "The treaty text is ambiguous; preparatory works (travaux préparatoires) show the drafters "
                "intended a broad interpretation, but subsequent state practice has been inconsistent."
            )
        }
    ],
    "key_facts": {
        "gondoria_pacifica_norstland_objection_timing": (
            "Gondoria, Pacifica, and Norstland began formally objecting to any seabed drilling moratorium "
            "rule in international forums starting in 1992, consistently maintained through 2024."
        ),
        "ruritania_termination_method": (
            "Ruritania's Foreign Minister issued a press release on 5 November 2023 declaring the SRC "
            "'null and void' due to Arcadia's alleged material breach. No formal written notification was "
            "sent to Arcadia or deposited with any treaty depository."
        ),
        "state_practice_uniformity": (
            "47 of 52 states surveyed observe drilling moratoriums; 3 (Gondoria, Pacifica, Norstland) "
            "persistently object; 2 observe the practice but state it is not legally required."
        )
    }
}

with open(os.path.join(workspace, "case_files/jessup_scenario_2024.json"), "w") as f:
    json.dump(scenario, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} files across {len(dirs)} directories.")