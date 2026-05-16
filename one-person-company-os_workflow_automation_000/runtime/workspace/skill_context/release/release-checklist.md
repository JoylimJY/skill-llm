# Release Checklist

## Positioning

- keep the primary audience as AI-native solo founders and independent builders
- keep the visible founder mental model as `验证需求 -> MVP -> 小范围上线 -> 收反馈 -> 迭代 -> 增长`
- keep rounds, calibration, and stages as internal control structures rather than the first thing users feel
- avoid reintroducing week-based positioning as the main loop

## Repository

- verify `README.md`, `README.zh-CN.md`, and `SKILL.md` describe the same product
- verify `agents/openai.yaml` matches the current positioning
- run `python3 scripts/preflight_check.py --mode 创建公司`
- run `python3 scripts/ensure_python_runtime.py`
- run `python3 scripts/validate_release.py`
- confirm the Chinese-first workspace scripts still pass
- confirm runtime output reports `installed`, `runnable`, `python_supported`, `workspace_created`, and `persisted`
- confirm `产物/` only contains numbered `.docx` files in generated workspaces
- confirm launch-stage workspaces include deployment and production starter materials
- confirm launch-stage role briefs include `运维保障` and `用户运营`
- confirm generated workspaces include `12-AI时代快循环.md`

## Proof Assets

- include one screenshot of the generated Chinese workspace
- include one screenshot of `00-公司总览.md`
- include one screenshot of `04-当前回合.md`
- include `SAMPLE-OUTPUTS.md` excerpts in the release post

## Post-Launch Loop

- collect founder reactions to the new fast-loop workflow
- collect founder reactions to the new `状态栏 / 保存状态 / 运行状态` output
- watch which first prompt users actually copy
- track whether users understand `总控台` quickly
- tighten the setup draft if users still ask too many clarifying questions
