# One Person Company OS Plain-English Guide

The most accurate way to think about this skill is as a control tower for a solo company.

It is not a startup chat prompt. It is a system for actually running an AI-native solo company.

## One-Line Mental Model

The old pattern was:

- write a lot of documents
- then do weekly reviews

The better pattern is:

- narrow one pain and one user first
- validate demand quickly
- ship the smallest useful MVP
- launch narrowly and collect feedback
- improve before scaling growth

The system still keeps internal structures like current round, stage, calibration, and stage transition, but the founder-facing experience should feel like the fast loop above.

## How To Use It

The simplest first prompt is:

```text
I want to build a solo company. Use one-person-company-os.
Do not make me fill a lot of fields first. Ask me for the idea in one sentence, or give me 3 to 4 directions to choose from.
```

The system first gives you a company setup draft that includes:

- direction guidance from the one-line idea
- a few startup directions if you are still undecided
- a one-line product definition
- company-name options
- the suggested bottleneck stage
- a minimal org structure
- the first active roles
- the workspace structure
- the first executable round

Only after you confirm will it create the workspace, role briefs, and process files.
After creation, start with `10-创始人启动卡.md`, `11-交付目录总览.md`, and `12-AI时代快循环.md`.

## How It Differs From A Generic Startup Assistant

A generic startup assistant usually works like "you ask one question, it answers one question."

This skill behaves like an execution system. It keeps:

- one current round
- one clear blocker
- one shortest next action
- calibration only when necessary
- a three-layer navigation bar on every important output
- separate user-navigation and audit views
- numbered DOCX deliverables with real evidence
- a path reminder on every meaningful reply so you know what to open next

## Why Weekly Reviews Are Not The Main Rhythm

In the AI era, a week is often too slow.

A more effective rhythm is:

- fast-loop execution as the founder-facing model
- rounds as 2-to-3-hour execution units
- trigger-based calibration
- stage transitions only when the bottleneck changes

That means you stop asking "what should I write in this week's review?"
and start asking:

- what is the current round
- what is still missing
- why are we blocked
- should we switch owner or stage

## Internal Structure

The system has five core layers:

- `SKILL.md`
- `references/`
- `agents/roles/*.json`
- `orchestration/*.json`
- `scripts/*.py`

## Six Moves To Remember

- name the pain
- validate the demand
- ship the smallest MVP
- launch narrowly
- improve from feedback
- scale only after value is real

If you only want occasional ideation, this skill may feel heavy.
If you actually want a solo company to keep moving, it becomes useful very quickly.
