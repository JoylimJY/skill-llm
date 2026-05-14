import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "scripts",
    "docs/onboarding",
    "docs/processes",
    "archive/2022",
    "archive/2023/q1",
    "archive/2023/q4",
    "team-resources/templates",
    "team-resources/retros",
    "internal-tools/scripts",
    "internal-tools/configs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/onboarding/new-hire-checklist.md": "# New Hire Checklist\n- Setup laptop\n- Meet team\n- Read handbook",
    "docs/onboarding/engineering-values.md": "# Engineering Values\n1. Move fast\n2. Own your work\n3. Communicate clearly",
    "docs/processes/incident-process.md": "# Incident Process\nSeverity 1: page on-call immediately.\nSeverity 2: create ticket.",
    "docs/processes/code-review-guidelines.md": "# Code Review Guidelines\n- Be constructive\n- Review within 24h",
    "archive/2022/team-retro-notes.txt": "Q4 2022 retro notes: team morale low, delivery strong. Action items: more 1-on-1s.",
    "archive/2023/q1/planning-notes.md": "Q1 2023 Planning\nFocus: reliability improvements, reduce P1 incidents by 30%",
    "archive/2023/q4/annual-review-template.md": "# Annual Review Template\nStrengths:\nGrowth areas:\nGoals for next year:",
    "team-resources/templates/promotion-doc-template.md": "# Promotion Document\nCandidate:\nLevel applying for:\nEvidence:",
    "team-resources/retros/sprint-42-retro.md": "Sprint 42 Retro\nWent well: fast deployment\nImprove: test coverage\nAction: add integration tests",
    "team-resources/retros/sprint-43-retro.md": "Sprint 43 Retro\nWent well: zero incidents\nImprove: documentation\nAction: doc day next sprint",
    "internal-tools/configs/eslint.json": '{"extends": "eslint:recommended", "env": {"node": true}}',
    "internal-tools/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\nnpm run build && npm run deploy",
    "CHANGELOG.md": "# Changelog\n## v1.2.0\n- Added stakeholder prompts\n## v1.1.0\n- Added incident retro prompts",
}
for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- Create the main leadership prompts script ---
script_content = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const PROMPTS_FILE = path.join(__dirname, '..', 'prompts.json');

function loadPrompts() {
  const raw = fs.readFileSync(PROMPTS_FILE, 'utf8');
  return JSON.parse(raw);
}

const [,, command, ...args] = process.argv;

switch (command) {
  case 'list': {
    const prompts = loadPrompts();
    const categories = {};
    for (const p of prompts) {
      if (!categories[p.category]) categories[p.category] = 0;
      categories[p.category]++;
    }
    console.log('Categories:');
    for (const [cat, count] of Object.entries(categories)) {
      console.log(`  ${cat} (${count})`);
    }
    break;
  }
  case 'random': {
    const prompts = loadPrompts();
    const p = prompts[Math.floor(Math.random() * prompts.length)];
    console.log(`[${p.id}] ${p.title}`);
    console.log(`Category: ${p.category}`);
    console.log(`\nPrompt:\n${p.prompt}`);
    console.log(`\nContext: ${p.context}`);
    console.log(`\nOutput Format: ${p.output_format}`);
    break;
  }
  case 'search': {
    const keyword = args.join(' ').toLowerCase();
    const prompts = loadPrompts();
    const results = prompts.filter(p =>
      p.title.toLowerCase().includes(keyword) ||
      p.prompt.toLowerCase().includes(keyword) ||
      p.category.toLowerCase().includes(keyword) ||
      (p.context && p.context.toLowerCase().includes(keyword))
    );
    if (results.length === 0) {
      console.log('No prompts found.');
    } else {
      for (const p of results) {
        console.log(`[${p.id}] ${p.title} (${p.category})`);
      }
    }
    break;
  }
  case 'show': {
    const id = args[0];
    const prompts = loadPrompts();
    const p = prompts.find(pp => pp.id === id);
    if (!p) {
      console.log(`Prompt not found: ${id}`);
      process.exit(1);
    }
    console.log(`[${p.id}] ${p.title}`);
    console.log(`Category: ${p.category}`);
    console.log(`\nPrompt:\n${p.prompt}`);
    console.log(`\nContext: ${p.context}`);
    console.log(`\nOutput Format: ${p.output_format}`);
    console.log(`\nExample:\n${p.example}`);
    break;
  }
  case 'category': {
    const cat = args.join(' ');
    const prompts = loadPrompts();
    const results = prompts.filter(p => p.category.toLowerCase() === cat.toLowerCase());
    if (results.length === 0) {
      console.log(`No prompts in category: ${cat}`);
    } else {
      for (const p of results) {
        console.log(`[${p.id}] ${p.title}`);
      }
    }
    break;
  }
  default:
    console.log('Usage: leadership-prompts.js <list|random|search|show|category> [args]');
}
"""
with open(os.path.join(workspace, "scripts/leadership-prompts.js"), "w") as f:
    f.write(script_content)

# --- Create the core prompts.json with existing prompts ---
existing_prompts = [
    {
        "id": "one-on-one-underperformer",
        "category": "1-on-1 Prep",
        "title": "Preparing for a 1-on-1 with an Underperformer",
        "prompt": "I'm preparing for a 1-on-1 with a direct report who has been underperforming for the past {timeframe}. Their role is {role} and the specific gaps are {performance_gaps}. Help me structure this conversation using the SBI (Situation-Behavior-Impact) framework. Include how to open the conversation, what questions to ask, how to handle a defensive reaction, and when to escalate to HR.",
        "context": "Use before a difficult performance conversation. Best used when you've already had informal check-ins and need to make the concern formal.",
        "output_format": "A structured conversation guide with: opening statement, 3-5 probing questions, responses to likely pushback, and a clear next-steps template.",
        "example": "I'm preparing for a 1-on-1 with a direct report who has been underperforming for the past 6 weeks. Their role is senior backend engineer and the specific gaps are: missing sprint commitments 3 sprints in a row and not communicating blockers proactively."
    },
    {
        "id": "one-on-one-star-retention",
        "category": "1-on-1 Prep",
        "title": "Retention 1-on-1 for a Star Performer",
        "prompt": "I have a high performer {name_or_role} who I'm worried might be at flight risk. They've been with the team for {tenure} and recently {recent_signal}. Help me plan a retention-focused 1-on-1 that feels genuine, not corporate. Include how to surface their real motivations, what I can realistically offer, and what I should avoid saying.",
        "context": "Use when you sense a top performer is disengaged, interviewing elsewhere, or has just received an external offer.",
        "output_format": "A conversation plan with: 3 genuine opening questions, a motivation-mapping framework, realistic retention levers you can pull, and 2-3 phrases to avoid.",
        "example": "I have a high performer (Staff Engineer, Sarah) who I'm worried might be at flight risk. She's been with the team for 3 years and recently seemed disengaged in team meetings and stopped volunteering for new projects."
    },
    {
        "id": "one-on-one-skip-level",
        "category": "1-on-1 Prep",
        "title": "Skip-Level 1-on-1 Questions",
        "prompt": "I'm running skip-level 1-on-1s with {number} engineers who report to {manager_name}. I want to assess team health, surface issues my manager might be shielding me from, and build trust without undermining {manager_name}'s authority. Give me a structured question bank and ground rules for the conversation.",
        "context": "Use quarterly or when you suspect there are team health issues being filtered by the middle layer.",
        "output_format": "15 questions organized by theme (team dynamics, manager effectiveness, career growth, work environment), plus a set of ground rules to share at the start of each conversation.",
        "example": "I'm running skip-level 1-on-1s with 6 engineers who report to James. I want to assess team health, surface issues my manager might be shielding me from, and build trust without undermining James's authority."
    },
    {
        "id": "one-on-one-career-goals",
        "category": "1-on-1 Prep",
        "title": "Career Goals Alignment 1-on-1",
        "prompt": "I want to have a meaningful career conversation with {name_or_role} who is at {current_level} and has expressed interest in {career_goal}. I want to help them build a realistic path without overpromising. Help me structure the conversation to align their goals with what's actually available on the team and in the org.",
        "context": "Use during performance cycles, after a promotion decision, or when an engineer brings up career growth concerns.",
        "output_format": "A conversation outline with: goal-clarification questions, a skills gap assessment framework, a realistic timeline discussion guide, and a commitment template both parties can agree to.",
        "example": "I want to have a meaningful career conversation with Alex who is at senior engineer level and has expressed interest in becoming a tech lead. I want to help them build a realistic path without overpromising."
    },
    {
        "id": "team-health-conflict",
        "category": "Team Health",
        "title": "Diagnosing and Resolving Team Conflict",
        "prompt": "There's visible tension between {person_a} and {person_b} on my team. It's affecting {impact_area}. I don't have full context on what started it. Help me: diagnose what type of conflict this is, plan separate 1-on-1s to gather information neutrally, and design a path to resolution that doesn't require me to pick sides.",
        "context": "Use when interpersonal conflict is affecting team output, meeting dynamics, or retention risk.",
        "output_format": "A conflict resolution playbook with: conflict type diagnosis questions, a neutral information-gathering interview guide, a mediation session structure, and escalation criteria.",
        "example": "There's visible tension between the two senior engineers on my team. It's affecting code review quality and sprint planning. I don't have full context on what started it."
    },
    {
        "id": "team-health-post-layoff",
        "category": "Team Health",
        "title": "Rebuilding Team Morale After Layoffs",
        "prompt": "My team just went through a round of layoffs. We lost {number} people including {roles_lost}. The remaining team is {team_size} people. Morale is visibly low and I'm seeing {symptoms}. Help me design a 30-day plan to rebuild trust, address the survivor guilt, and re-establish team identity without gaslighting people about what happened.",
        "context": "Use within 1 week of a layoff announcement affecting your direct team.",
        "output_format": "A 30-day communication and culture plan with: week-by-week actions, specific things to say and not say, a team ritual to restart, and a morale indicator to watch.",
        "example": "My team just went through a round of layoffs. We lost 3 people including our senior engineer and QA lead. The remaining team is 6 people. Morale is visibly low and I'm seeing people going quiet in standups and shipping less."
    },
    {
        "id": "team-health-remote-disconnect",
        "category": "Team Health",
        "title": "Fixing Remote Team Disconnection",
        "prompt": "My remote team is showing signs of disconnection: {specific_signals}. We're spread across {timezones} and have been fully remote for {duration}. Help me design a low-overhead connection strategy that engineers won't roll their eyes at. Focus on async-first approaches with optional sync touchpoints.",
        "context": "Use when async communication is breaking down, you're seeing social isolation, or team identity is weakening in a distributed team.",
        "output_format": "A connection strategy with: 3 async rituals, 1 optional sync format, a communication norms document outline, and a 60-day check-in plan.",
        "example": "My remote team is showing signs of disconnection: people are going days without talking to each other, PRs are getting merged with no comments, and the team Slack channel is dead. We're spread across 4 timezones and have been fully remote for 18 months."
    },
    {
        "id": "team-health-rough-quarter",
        "category": "Team Health",
        "title": "Team Reset After a Rough Quarter",
        "prompt": "We just had a rough quarter: {what_went_wrong}. The team is {emotional_state}. I want to acknowledge what happened honestly, extract the learning, and create forward momentum without toxic positivity or blame. Help me design a team reset session.",
        "context": "Use after a failed launch, missed OKRs, sustained crunch, or a public incident.",
        "output_format": "A 90-minute team session agenda with: an honest opening, a structured retrospective format, a lessons-captured template, and a forward-focus activity that builds momentum.",
        "example": "We just had a rough quarter: we missed our reliability OKR by a wide margin and had 3 P1 incidents. The team is demoralized and starting to point fingers. I want to acknowledge what happened honestly."
    },
    {
        "id": "incident-retro-blameless",
        "category": "Incident Retrospectives",
        "title": "Running a Blameless Incident Retrospective",
        "prompt": "We had an incident: {incident_description}. It lasted {duration} and impacted {impact}. I need to run a blameless retro within 48 hours. Help me design the session, write the facilitation guide, and produce a shareable post-mortem document that satisfies both engineering and executive audiences.",
        "context": "Use within 24-48 hours of resolving a significant incident.",
        "output_format": "A retro facilitation guide (timeline reconstruction, 5-whys template, action items matrix) plus a post-mortem document template with an executive summary section.",
        "example": "We had an incident: our payment processing service was down for 47 minutes due to a misconfigured deployment. It lasted 47 minutes and impacted approximately 2,400 customers during peak hours."
    },
    {
        "id": "incident-retro-repeat",
        "category": "Incident Retrospectives",
        "title": "Addressing a Repeat Incident Pattern",
        "prompt": "We've had {number} incidents of type {incident_type} in the past {timeframe}. Each one has had a retro, but the pattern persists. Something systemic is being missed. Help me design a cross-incident analysis session that gets below the surface symptoms to the root organizational or architectural cause.",
        "context": "Use when you've run retros on individual incidents but the same category of failure keeps recurring.",
        "output_format": "A cross-incident analysis framework with: pattern identification questions, a systemic root cause taxonomy, an organizational vs. technical blame-split analysis, and a proposal template for structural fixes.",
        "example": "We've had 4 incidents of type 'database connection pool exhaustion' in the past 3 months. Each one has had a retro, but the pattern persists."
    },
    {
        "id": "incident-retro-exec-comms",
        "category": "Incident Retrospectives",
        "title": "Executive Communication After a Major Incident",
        "prompt": "We just had a major incident: {incident_summary}. My CTO/VP has asked for a briefing. I need to communicate: what happened, why it happened, what we're doing about it, and why this won't happen again — without making my team look incompetent or triggering a witch hunt. Help me write the briefing.",
        "context": "Use when you need to brief executives or a board within 24-72 hours of a major incident.",
        "output_format": "An executive briefing document with: 1-paragraph plain English summary, timeline of events, root cause (technical and process), 3-5 concrete action items with owners and due dates, and a confidence statement.",
        "example": "We just had a major incident: a database migration script ran against production instead of staging, causing 2 hours of downtime for all customers. My CTO has asked for a briefing."
    },
    {
        "id": "tech-strategy-build-vs-buy",
        "category": "Technical Strategy",
        "title": "Build vs. Buy Decision Framework",
        "prompt": "We're evaluating whether to {build_or_buy_description}. The options on the table are: {options}. Our constraints are: {constraints}. Help me structure a build-vs-buy analysis that covers TCO, strategic fit, team capability, and vendor risk — and produces a recommendation I can defend to the CTO.",
        "context": "Use before committing to any significant new infrastructure, tooling, or platform component.",
        "output_format": "A decision framework document with: evaluation criteria matrix (weighted), TCO calculation template, risk register, and a recommendation section with confidence level.",
        "example": "We're evaluating whether to build our own feature flag service or buy a vendor solution. The options are: build in-house, use LaunchDarkly, or use Unleash self-hosted. Our constraints are: <$50k/year budget, must support 50+ feature flags, team has no dedicated platform engineer."
    },
    {
        "id": "tech-strategy-quarterly-review",
        "category": "Technical Strategy",
        "title": "Quarterly Technical Strategy Review",
        "prompt": "It's time for our quarterly technical strategy review. Our team is {team_description}. In the last quarter we {last_quarter_highlights}. Our product roadmap for next quarter includes {upcoming_features}. Help me structure a 2-hour technical strategy session that covers debt, architecture evolution, and team capability development.",
        "context": "Use at the start of each quarter to align technical direction with product plans.",
        "output_format": "A session agenda with: a tech debt triage exercise, an architecture evolution discussion guide, a skills gap analysis, and a quarterly technical OKR template.",
        "example": "Our team is 8 engineers building a B2B SaaS product. In the last quarter we shipped a new reporting module and migrated to Kubernetes. Our product roadmap for next quarter includes a new API gateway and a customer-facing analytics dashboard."
    },
    {
        "id": "tech-strategy-architecture-review",
        "category": "Technical Strategy",
        "title": "Architecture Review for a New System",
        "prompt": "We're designing {system_name}, a new system that needs to {system_requirements}. The team proposing it is {proposing_team}. I need to run an architecture review that's rigorous but not a rubber stamp — it should surface real risks without demoralizing the team or slowing delivery unnecessarily.",
        "context": "Use before any significant new system or major refactor gets greenlit for development.",
        "output_format": "An architecture review checklist covering: scalability assumptions, failure modes, operational readiness, security surface, and a structured Q&A guide for the review session.",
        "example": "We're designing a new async notification system that needs to handle 10k events/second with sub-100ms delivery SLAs. The team proposing it is the platform team of 3 engineers."
    },
    {
        "id": "tech-strategy-tech-debt",
        "category": "Technical Strategy",
        "title": "Making the Case for Tech Debt Investment",
        "prompt": "My team is carrying significant tech debt in {area}. It's causing {business_impact}. I need to make the case to product leadership to invest {time_investment} in debt reduction. Help me frame this in business terms, quantify the cost of inaction, and propose a roadmap that product will actually approve.",
        "context": "Use during roadmap planning when you need to negotiate time for technical investment against feature pressure.",
        "output_format": "A business case document with: a plain-English problem statement, a cost-of-inaction analysis (velocity lost, incident risk, hiring impact), a proposed investment plan, and success metrics.",
        "example": "My team is carrying significant tech debt in our authentication service. It's causing slow feature development (every auth change takes 3x longer than it should) and is our most common source of security vulnerabilities."
    },
    {
        "id": "hiring-job-description",
        "category": "Hiring & Interviews",
        "title": "Writing a Senior Engineer Job Description That Attracts the Right Candidates",
        "prompt": "I'm hiring for a {role} on my team. The team is {team_description}. The real challenges this person will face are {real_challenges}. Help me write a job description that attracts strong candidates and filters out the wrong ones — without the usual corporate boilerplate. Be honest about the hard parts.",
        "context": "Use when opening a new role or when a previous job description isn't attracting quality candidates.",
        "output_format": "A job description with: a compelling 2-paragraph team/role intro, 5-7 specific responsibilities (not generic), 4-5 must-have qualifications (not laundry lists), an honest 'hard parts' section, and a culture signal paragraph.",
        "example": "I'm hiring for a senior backend engineer on my team. The team is 5 engineers building a high-throughput data pipeline. The real challenges are: legacy Python 2 codebase we're migrating, on-call rotation 1 week in 5, and a product team that moves very fast."
    },
    {
        "id": "hiring-interview-debrief",
        "category": "Hiring & Interviews",
        "title": "Running a Structured Interview Debrief",
        "prompt": "We just interviewed {candidate_name} for {role}. The interviewers are {interviewers}. I need to run a debrief that reaches a genuine, bias-minimized decision — not a consensus-by-loudest-voice outcome. Help me design the debrief structure and give me the facilitation guide.",
        "context": "Use immediately after the final interview before any informal votes or opinions are shared.",
        "output_format": "A debrief facilitation guide with: written feedback collection format, a signal-vs-noise discussion framework, a structured vote mechanism, and criteria for a 'strong yes', 'yes', 'no', 'strong no' decision.",
        "example": "We just interviewed Jordan for a Staff Engineer role. The interviewers are 4 engineers plus myself. I need to run a debrief that reaches a genuine, bias-minimized decision."
    },
    {
        "id": "hiring-closing-candidate",
        "category": "Hiring & Interviews",
        "title": "Closing a Strong Candidate Who Has Competing Offers",
        "prompt": "I want to hire {candidate_name} for {role}. They have a competing offer from {competitor}. Our offer is {our_offer}. Their hesitation seems to be around {candidate_hesitation}. Help me plan the closing conversation — what to say, what to offer, and how to be compelling without being desperate.",
        "context": "Use when a strong candidate is on the fence or has indicated they have a competing offer.",
        "output_format": "A closing conversation guide with: an opening that acknowledges their position, 3-5 genuine differentiators to highlight, responses to likely objections, and a clear call-to-action.",
        "example": "I want to hire Priya for a Staff Engineer role. She has a competing offer from a FAANG company. Our offer is competitive on salary but lower on RSUs. Her hesitation seems to be around long-term growth opportunities."
    },
    {
        "id": "career-dev-promotion",
        "category": "Career Development",
        "title": "Building a Promotion Case for a Direct Report",
        "prompt": "I want to promote {name} from {current_level} to {target_level}. The promotion cycle is in {timeframe}. I need to build a compelling promotion case that will survive committee scrutiny. Help me gather the right evidence, structure the document, and prepare for the likely objections.",
        "context": "Use 6-8 weeks before a promotion cycle to build a strong evidence-based case.",
        "output_format": "A promotion case template with: impact evidence matrix (projects, scope, influence), level-specific bar criteria checklist, objection prep guide, and a narrative summary template.",
        "example": "I want to promote Sarah from Senior Engineer to Staff Engineer. The promotion cycle is in 8 weeks. I need to build a compelling promotion case that will survive committee scrutiny."
    },
    {
        "id": "career-dev-feedback",
        "category": "Career Development",
        "title": "Delivering Hard Feedback That Sticks",
        "prompt": "I need to give {name} feedback about {feedback_topic}. Previous attempts to address this have {previous_attempts}. The behavior is having {impact}. I want this feedback to actually change behavior, not just make them feel bad. Help me plan the conversation using the SBI framework and give me exact language to use.",
        "context": "Use when informal feedback hasn't worked and you need a more intentional, structured approach.",
        "output_format": "A feedback script with: opening statement, SBI-structured observation, impact statement, space for their response, and a clear behavioral ask with success criteria.",
        "example": "I need to give Marcus feedback about his communication style in cross-team meetings. Previous attempts were informal mentions in 1-on-1s. The behavior is making other teams reluctant to collaborate with us."
    },
    {
        "id": "career-dev-pip",
        "category": "Career Development",
        "title": "Designing a Performance Improvement Plan That's Actually Fair",
        "prompt": "I need to put {name} on a PIP. Their role is {role}. The performance gaps are {gaps}. I want this to be a genuine opportunity for improvement, not just legal cover for termination. Help me design a 30-60 day PIP with clear success criteria, regular check-ins, and support mechanisms.",
        "context": "Use when performance issues have been documented and informal coaching hasn't produced improvement.",
        "output_format": "A PIP document with: specific measurable success criteria, weekly check-in structure, support resources to provide, and a clear statement of what happens at the end of the period.",
        "example": "I need to put David on a PIP. His role is backend engineer. The performance gaps are: consistent failure to estimate accurately, blocking PRs for days without explanation, and missing sprint commitments without proactive communication."
    },
    {
        "id": "career-dev-ic-to-lead",
        "category": "Career Development",
        "title": "Supporting an IC Transitioning to Tech Lead",
        "prompt": "I'm promoting {name} from senior IC to their first tech lead role on {project_or_team}. They're strong technically but {transition_challenge}. Help me design a 90-day transition plan that builds their leadership muscles without throwing them in the deep end alone.",
        "context": "Use when promoting a strong IC into their first leadership role.",
        "output_format": "A 90-day transition plan with: weekly focus areas, specific leadership scenarios to practice, metrics to watch for early warning signs, and a gradual responsibility hand-off timeline.",
        "example": "I'm promoting Kai from senior IC to their first tech lead role on the new payments team. They're strong technically but have never had to drive alignment across stakeholders or deliver hard news to product."
    },
    {
        "id": "stakeholder-exec-update",
        "category": "Stakeholder Communication",
        "title": "Writing an Exec Update That Gets Read",
        "prompt": "I need to write an exec update for {project_or_initiative}. The audience is {audience}. Current status is {status}. Key risks are {risks}. Most execs skim or ignore these. Help me write one they'll actually read and that protects me if things go wrong.",
        "context": "Use weekly or bi-weekly for any high-visibility project or when you need to manage upward expectations.",
        "output_format": "An exec update template with: a 3-sentence BLUF summary, RAG status indicator, key decisions needed (if any), risks with mitigation, and a 'what's next' section.",
        "example": "I need to write an exec update for our platform migration project. The audience is the CTO and two VPs. Current status is yellow — we're on track for scope but 2 weeks behind on timeline. Key risks are a third-party API dependency we can't control."
    },
    {
        "id": "stakeholder-saying-no",
        "category": "Stakeholder Communication",
        "title": "Saying No to Stakeholders Without Burning Bridges",
        "prompt": "A stakeholder {stakeholder_name_or_role} is asking my team to {request}. We can't do this because {reason}. But I can't just say no — I need to preserve the relationship, offer something useful, and close the loop. Help me plan this conversation and write the follow-up message.",
        "context": "Use when you need to decline a request from a cross-functional partner, product manager, or executive.",
        "output_format": "A conversation guide plus a follow-up message template with: acknowledgment of the request, clear reason for the 'no', an alternative offer, and a relationship-preservation close.",
        "example": "A stakeholder (Head of Sales) is asking my team to build a custom integration for a single enterprise customer in Q3. We can't do this because it would derail our platform migration and we have no spare capacity."
    },
    {
        "id": "stakeholder-reorg-comms",
        "category": "Stakeholder Communication",
        "title": "Communicating a Reorg to Your Team",
        "prompt": "I'm about to communicate a reorg to my team. The changes are: {changes}. Some people will be happy, some won't. I've been told {what_i_can_say} and there are things I cannot say yet ({what_i_cannot_say}). Help me plan the announcement, anticipate questions, and manage the emotional fallout.",
        "context": "Use when you've received reorg news and need to cascade it to your team within 24-48 hours.",
        "output_format": "An announcement script, a Q&A prep document (with 'I don't know yet' answers for sensitive questions), a 1-week follow-up plan, and a guide for handling 1-on-1 reactions.",
        "example": "I'm about to communicate that two teams are being merged and the other team's manager will be leaving the company. Some people will be happy, some won't. I can share the new structure but cannot share why the other manager is leaving."
    },
    {
        "id": "stakeholder-cross-functional",
        "category": "Stakeholder Communication",
        "title": "Aligning Cross-Functional Stakeholders on a Technical Decision",
        "prompt": "I need to get alignment from {stakeholders} on {technical_decision}. Each stakeholder has different concerns: {concerns_per_stakeholder}. Previous attempts to align have {previous_attempts}. Help me design a 1-hour alignment session that actually produces a decision, not just more discussion.",
        "context": "Use before any significant technical decision that requires buy-in from non-engineering stakeholders.",
        "output_format": "An alignment session agenda with: a pre-read document template, a structured discussion format (options, tradeoffs, constraints), a decision-making protocol (RACI or consent-based), and a follow-up communication template.",
        "example": "I need to get alignment from Product, Security, and Legal on our decision to move customer PII to a new data store. Each stakeholder has different concerns: Product wants speed, Security wants audit trails, Legal wants data residency compliance."
    }
]

with open(os.path.join(workspace, "prompts.json"), "w") as f:
    json.dump(existing_prompts, f, indent=2)

# --- Create a SKILL.md file ---
skill_md_content = """---
name: leadership-prompts
description: >
  Curated collection of 25+ battle-tested prompts for engineering leaders — 1-on-1 prep, team health,
  incident retros, technical strategy, hiring, career development, and stakeholder communication.
  Built from 13+ years of engineering management experience.
homepage: https://leadingin.tech
license: MIT
metadata:
  clawdis:
    emoji: 🎯
    requires:
      bins: [node]
---

# Leadership Prompts

Battle-tested prompt library for engineering managers, tech leads, VPs of Engineering, and CTOs.

## Quick Start

### Using the CLI

```bash
# List all categories
node scripts/leadership-prompts.js list

# Get a random prompt
node scripts/leadership-prompts.js random

# Search by keyword
node scripts/leadership-prompts.js search "promotion"

# Show a specific prompt by ID
node scripts/leadership-prompts.js show career-dev-promotion

# Get all prompts in a category
node scripts/leadership-prompts.js category "Team Health"
```

## Adding Your Own Prompts

Add entries to `prompts.json` following the existing schema:

```json
{
  "id": "category-short-name",
  "category": "Category Name",
  "title": "Human-readable title",
  "prompt": "The actual prompt text with {variables}",
  "context": "When to use this prompt",
  "output_format": "What the AI should produce",
  "example": "A filled-in example showing real usage"
}
```
"""
with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

# --- Create a task requirements file (the business spec, NOT hints) ---
task_file_content = """# New Prompt Requirements — Q2 Engineering Leadership Toolkit Expansion

Our VP of Engineering has asked us to expand the leadership prompt library with three new entries
that came up repeatedly in last quarter's leadership retrospectives.

The three situations we need prompts for are:

1. **Onboarding a New Engineering Hire**
   Managers struggled with structuring the first 90 days for new engineers.
   Category: "1-on-1 Prep"
   We need a prompt that helps a manager plan the onboarding arc, set early milestones,
   and establish psychological safety in the first 90 days.

2. **Managing Burnout in High-Performers**
   Several managers flagged burnout as a blind spot — they only noticed it after the person resigned.
   Category: "Team Health"
   We need a prompt that helps a manager proactively identify and address burnout signals
   in a high-performing engineer before it becomes a flight risk.

3. **Communicating a Budget Cut to the Team**
   Budget cuts mid-year left managers without language for the conversation.
   Category: "Stakeholder Communication"
   We need a prompt that helps a manager communicate budget-driven headcount or tooling
   cuts honestly without triggering panic or a talent exodus.

All three prompts must be queryable through the existing tooling once added.
The library's current prompt count is 26. After adding these, it should be 29.
"""
with open(os.path.join(workspace, "new-prompt-requirements.md"), "w") as f:
    f.write(task_file_content)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")