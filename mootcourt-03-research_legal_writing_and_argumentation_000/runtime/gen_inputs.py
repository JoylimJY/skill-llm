import os
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create a realistic moot court team directory structure with distractor files

dirs = [
    "team_materials/research_notes",
    "team_materials/prior_memorials",
    "team_materials/case_law",
    "team_materials/treaty_texts",
    "team_materials/team_correspondence",
    "competition_docs/rules",
    "competition_docs/problem",
    "drafts/applicant",
    "drafts/respondent",
    "drafts/old_versions",
    "references/textbooks",
    "references/icj_summaries",
    "references/un_docs",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

(workspace / "team_materials/research_notes/general_notes.txt").write_text(
    """General research session - October 2024
Discussed Nicaragua case broadly.
Possible angles: state sovereignty, non-intervention.
Need to look into VCLT Art 31-33 for treaty interpretation.
Note: Check ILC 2018 Conclusions on CIL identification.
""", encoding="utf-8")

(workspace / "team_materials/research_notes/sanctions_overview.txt").write_text(
    """Economic Sanctions Research
- Targeted sanctions vs. comprehensive embargo
- See UN Charter Art 2(1) on sovereign equality
- US v. Nicaragua 1986 ICJ - economic coercion angle
- What % of trade cutoff triggers intervention?
- Look at Corfu Channel case for due diligence
- Some scholars say 30% cutoff = significant economic impact
""", encoding="utf-8")

(workspace / "team_materials/prior_memorials/jessup2022_fragment.md").write_text(
    """# Prior Memorial Fragment - 2022 Jessup (Sample)

## Issue I: Whether State X violated customary international law

### Rules
Customary international law requires two elements under Article 38(1)(b) of the ICJ Statute:
1. State practice
2. Opinio juris

[NOTE: This is incomplete - only one rule cited, no explanation - BAD EXAMPLE]

### Application
State X did things that were bad.

### Conclusion
Therefore State X violated CIL.
""", encoding="utf-8")

(workspace / "team_materials/prior_memorials/structure_template_bad.txt").write_text(
    """OLD BAD TEMPLATE - DO NOT USE
Issue: State question here
Rule: Copy-paste treaty article
Application: Facts happened
Conclusion: Done

Problems with this template:
- Only one rule
- No roadmap
- No case linkage analysis
- Passive voice throughout
- Facts section states conclusions directly
""", encoding="utf-8")

(workspace / "team_materials/case_law/nicaragua_notes.txt").write_text(
    """Nicaragua v. United States of America (Merits) 1986 ICJ Rep 14

Key holdings:
- Court found US violated customary international law on non-intervention
- Economic embargo: Court noted US cut ALL trade with Nicaragua
- Specific: US terminated sugar import quota, embargo on Nicaraguan imports
- ICJ: non-intervention principle prohibits coercive acts re: sovereign choices
- BUT: ICJ also found US violated bilateral FCN Treaty (friendship, commerce, navigation)
- Separate issue: use of force via mining harbors - clearly unlawful

Counter-arguments the US made:
- Nicaragua was helping El Salvador rebels
- Collective self-defense
- US argued trade cutoff was mere political statement, not coercion

Linkage notes:
- Our case: State A cut ~30% of R's commodity exports (not total embargo)
- A will try to distinguish: "we didn't cut ALL trade like USA did"
- We need to argue coercion is about EFFECT not PERCENTAGE
- Also: both cases have a bilateral economic cooperation treaty
""", encoding="utf-8")

(workspace / "team_materials/case_law/corfu_channel_notes.txt").write_text(
    """Corfu Channel Case (United Kingdom v. Albania) 1949 ICJ

Relevant for: Due diligence, notification obligations
Albania knew about mines but didn't warn UK ships
Court: states must not allow territory to be used for acts contrary to others' rights

Less relevant for sanctions issue but useful for due diligence angle.
""", encoding="utf-8")

(workspace / "team_materials/treaty_texts/vclt_art31.txt").write_text(
    """Vienna Convention on the Law of Treaties (1969)

Article 31 - General rule of interpretation
1. A treaty shall be interpreted in good faith in accordance with the ordinary meaning 
   to be given to the terms of the treaty in their context and in the light of its 
   object and purpose.
2. The context for the purpose of the interpretation of a treaty shall comprise...
3. There shall be taken into account, together with the context:
   (a) any subsequent agreement between the parties...
   (b) any subsequent practice in the application of the treaty...
   (c) any relevant rules of international law applicable in the relations between the parties.

Article 32 - Supplementary means of interpretation
Recourse may be had to supplementary means of interpretation, including the preparatory 
work of the treaty and the circumstances of its conclusion...
""", encoding="utf-8")

(workspace / "team_materials/treaty_texts/un_charter_excerpts.txt").write_text(
    """UN Charter Relevant Excerpts

Article 2(1): The Organization is based on the principle of the sovereign equality of all its Members.
Article 2(4): All Members shall refrain in their international relations from the threat or use of force...
Article 2(7): Nothing contained in the present Charter shall authorize the United Nations to intervene 
in matters which are essentially within the domestic jurisdiction of any state...

Note: Art 2(4) covers force, not economic coercion directly.
Non-intervention in economic matters derives from CIL, not explicitly UN Charter.
""", encoding="utf-8")

(workspace / "team_materials/team_correspondence/email_thread.txt").write_text(
    """From: TeamLead@university.edu
To: ResearchTeam@university.edu
Subject: Memorial Section Assignment

Hi team,

As discussed, we need the R (Applicant) memorial section arguing that State A's 
economic sanctions violate international law. 

Key facts reminder:
- State A imposed targeted sanctions cutting ~30% of State R's bauxite exports
- There is a bilateral Treaty of Friendship, Commerce and Navigation between A and R (2005)
- State A claims sanctions are a legitimate political response to R's domestic policies
- State R argues this is unlawful coercion and violates both CIL and the bilateral treaty

Please make sure whoever writes this doesn't just paste treaty text. We got dinged on 
that last year. The judges want to see actual legal reasoning.

Coach
""", encoding="utf-8")

(workspace / "competition_docs/problem/moot_problem_summary.txt").write_text(
    """MOOT COURT PROBLEM SUMMARY - CONFIDENTIAL

State of Aravia (A) and Republic of Ruthenland (R)

FACTS:
1. In 2021, State A imposed "targeted economic measures" against State R, 
   restricting the import of bauxite (R's primary export commodity) by approximately 
   30% of total export volume.
2. A publicly stated these measures were in response to R's amendment of its 
   domestic media regulation laws, which A considered suppressive of press freedom.
3. In 2005, A and R concluded a Treaty of Friendship, Commerce and Navigation (FCN Treaty), 
   which provides in Article 7: "Neither Party shall impose measures that materially 
   impair the commercial activities of nationals or enterprises of the other Party."
4. R's economy is highly dependent on bauxite exports; the 30% restriction caused 
   a 12% contraction in R's GDP over two years.
5. No UN Security Council authorization existed for these measures.
6. A did not consult R before imposing sanctions nor provide advance notice.

LEGAL QUESTIONS FOR R (APPLICANT):
(a) Whether State A's economic sanctions violate the customary international law 
    principle of non-intervention.
(b) Whether State A's sanctions breach the bilateral FCN Treaty.

YOUR ASSIGNMENT:
Write the memorial section for State R arguing Question (a): CIL non-intervention.
You may reference Question (b) where relevant to case distinctions.
""", encoding="utf-8")

(workspace / "competition_docs/rules/competition_guidelines.txt").write_text(
    """Competition Guidelines (Excerpt)

Memorials should:
- Follow standard memorial structure
- Cite authoritative sources
- Present arguments in a logical, well-organized manner
- Use formal legal English

Word limit: Not specified for this exercise.
""", encoding="utf-8")

(workspace / "drafts/applicant/placeholder.txt").write_text(
    "This directory is for the applicant memorial drafts.\n", encoding="utf-8")

(workspace / "drafts/respondent/placeholder.txt").write_text(
    "This directory is for the respondent memorial drafts.\n", encoding="utf-8")

(workspace / "drafts/old_versions/draft_v0_incomplete.md").write_text(
    """# DRAFT v0 - INCOMPLETE - DO NOT SUBMIT

State A violated international law.

The sanctions are bad.

[TODO: add actual arguments]
[TODO: cite Nicaragua case]
[TODO: add roadmap]
""", encoding="utf-8")

(workspace / "references/textbooks/shaw_notes.txt").write_text(
    """Notes from Malcolm N Shaw, International Law (9th edn, CUP 2021)

Chapter 3 - Sources of International Law:
- Art 38(1) ICJ Statute: treaties, custom, general principles, judicial decisions
- Custom = state practice + opinio juris (legal conviction)
- State practice: diplomatic acts, legislation, judicial decisions, military manuals
- Opinio juris: belief that practice is legally required (not merely habitual)

Chapter on Non-Intervention:
- Non-intervention is a core principle of CIL
- Coercion: the key element - dictating sovereign choices through pressure
- Economic coercion can violate non-intervention if it compels sovereign decisions
- Nicaragua case: ICJ confirmed economic coercion can breach non-intervention
""", encoding="utf-8")

(workspace / "references/icj_summaries/nicaragua_summary.txt").write_text(
    """ICJ Case Summary: Nicaragua v. United States (Merits) [1986] ICJ Rep 14

Court found:
1. US violated CIL principle of non-intervention by:
   - Arming and training contra rebels
   - Imposing trade embargo (terminated sugar quota + full embargo)
2. US violated bilateral FCN Treaty (1956) by trade embargo
3. Court distinguished "intervention" requiring coercion from mere diplomatic pressure

Key paragraph 205: "the principle of non-intervention involves the right of every 
sovereign State to conduct its affairs without outside interference; though examples 
of trespass against this principle are not infrequent, the Court considers that it 
is part and parcel of customary international law."

Key paragraph 245: US embargo = violation of FCN Treaty because it "materially 
impaired" Nicaraguan commercial activities - ALL trade was cut.

Note for our case: A will argue their 30% cut ≠ total embargo. We need to argue 
coercion is about EFFECT and INTENT, not just degree.
""", encoding="utf-8")

(workspace / "references/un_docs/ilc_cil_conclusions.txt").write_text(
    """ILC, Draft Conclusions on Identification of Customary International Law (2018)

Conclusion 2: Two elements - state practice (usus) + accepted as law (opinio juris)
Conclusion 4: State practice = conduct of the State in its various capacities
  - includes acts and omissions; physical and verbal acts
  - diplomatic acts and correspondence, legislation, judicial decisions, 
    conduct in international organizations
Conclusion 6: To have "general" practice, "widespread and representative" required
  - Includes states whose interests are "specially affected"
Conclusion 9: Opinio juris = acceptance as law
  - public statements, official publications, government legal opinions,
    diplomatic correspondence, decisions of national courts, treaty provisions,
    conduct in connection with resolutions adopted by international organizations
Conclusion 10: Resolutions of international organizations/conferences
  - UN General Assembly resolutions may provide evidence of opinio juris
""", encoding="utf-8")

(workspace / "references/un_docs/declaration_1970.txt").write_text(
    """UN General Assembly Resolution 2625 (XXV) - 1970
Declaration on Principles of International Law concerning Friendly Relations

Principle on Non-Intervention:
"No State may use or encourage the use of economic, political or any other type 
of measures to coerce another State in order to obtain from it the subordination 
of the exercise of its sovereign rights and to secure from it advantages of any kind."

This resolution is widely cited as evidence of opinio juris for the CIL 
non-intervention principle extending to economic coercion.
""", encoding="utf-8")

print("Workspace created successfully with all distractor and reference files.")
print(f"Total files created: {len(list(workspace.rglob('*.*')))}")