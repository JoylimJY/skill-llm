import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "ai-meeting-room/references",
    "ai-meeting-room/logs",
    "ai-meeting-room/templates",
    "ai-meeting-room/archive/2024",
    "ai-meeting-room/archive/2023",
    "projects/pb-drink-brand",
    "projects/pb-drink-brand/research",
    "projects/pb-drink-brand/finance",
    "internal/hr",
    "internal/legal",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── agent-roles.md (the canonical reference) ─────────────────────────────────
agent_roles_content = """# Agent Roles Reference

## Fixed Members (Always Present)
- 🦁 리오 (의장) — 스타트업 3곳 창업, 2곳 매각 경험. "자, 핵심이 뭐야?"로 토론 수렴.
- 😈 데빌 (극단적 반대) — 전직 VC 심사역 10년. 100개 피칭 중 95개 탈락.

## Expert Pool (Auto-selected by topic keywords)
### Food/Consumer Goods / F&B / 소비재
  - 🦊 스카우트 (시장분석) — 맥킨지 5년 + 스타트업 리서치 펌 대표
  - 📊 애널 (재무/데이터) — 삼성증권 애널리스트 출신
  - 🐝 카피 (마케팅/고객심리) — 배달의민족 초기 마케팅팀 출신
  - ⚖️ 리걸 (법률/규제) — 로펌 7년 + 스타트업 법률자문
  - 🎯 그로스 (성장전략) — 당근마켓 그로스팀 출신

### Tech / SaaS
  - 🔧 빌더 (기술/제품) — 토스 초기 개발팀 출신
  - 🎨 피카 (UX/디자인) — 쿠팡 UX 리서처 출신
  - 🧠 PM (프로덕트매니저) — 네이버/카카오 PM 8년

### Investment / Finance
  - 💰 투자자 (VC관점) — 시드~시리즈B 투자 50건+

### Growth / HR
  - 👥 HR (조직/채용) — 스타트업 HR 전문
  - 🌍 글로벌 (해외시장) — 실리콘밸리 + 도쿄 + 싱가포르 근무

## Selection Rules
1. Pick 3-5 experts relevant to the topic (excluding fixed members)
2. 😈 데빌 is ALWAYS included — no exceptions
3. 🦁 리오 (의장) always chairs
4. For F&B / consumer goods topics: prefer 스카우트, 애널, 카피, 리걸
"""

with open(os.path.join(WORKSPACE, "ai-meeting-room/references/agent-roles.md"), "w", encoding="utf-8") as f:
    f.write(agent_roles_content)

# ── meeting-templates.md ─────────────────────────────────────────────────────
meeting_templates_content = """# Meeting Templates

## Sprint Mode Template
Quick 30-second read. One debate round + conclusion + one action.

## Full Mode Template
5-7 minute read. Full debate + user speaking rights.
Sections:
1. 자문 정보 (info block)
2. ⚡ 30초 요약
3. 📋 사전 리서치 브리핑
4. 토론 전문 (free dialogue)
5. 핵심 논점 & 합의 (table)
6. 미합의 & 리스크
7. 😈 데빌의 최종
8. 액션 아이템 (decision tree table)
9. 다음 자문 안건

## Deep Mode Template
10+ minute read. 8-12 web searches, extended debate, thought process exposed.
"""

with open(os.path.join(WORKSPACE, "ai-meeting-room/references/meeting-templates.md"), "w", encoding="utf-8") as f:
    f.write(meeting_templates_content)

# ── conflict-patterns.md ─────────────────────────────────────────────────────
conflict_patterns_content = """# Conflict Patterns Reference

## Structural Tensions (defaults, not fixed)
- 스카우트(시장 데이터) ↔ 애널(재무 현실)
- 카피(고객 공감) ↔ 애널(냉정한 숫자)
- 빌더(기술 가능성) ↔ 그로스(시장 타이밍)
- 전원 ↔ 데빌(극단적 반대)

## Key: Data overrides structure
If the data points in one direction, agents may align across structural lines.
Scout can side with Devil if market is bleak.
Analyst can side with Copy if numbers are optimistic.

## Consensus Levels
- 🟢 강한 합의 — all agree including Devil
- 🟡 약한 합의 — majority agree, some conditional
- 🔴 미합의 — split opinion, more data needed
- ⛔ No-Go — majority oppose or fatal risk found
"""

with open(os.path.join(WORKSPACE, "ai-meeting-room/references/conflict-patterns.md"), "w", encoding="utf-8") as f:
    f.write(conflict_patterns_content)

# ── distractor files ─────────────────────────────────────────────────────────

# Old meeting log (archive)
with open(os.path.join(WORKSPACE, "ai-meeting-room/archive/2024/meeting_001.md"), "w", encoding="utf-8") as f:
    f.write("""# AI 자문단 — 1차 (2024-03-15)
주제: 반려동물 구독 박스 서비스
결론: 조건부 Go
액션: 네이버 스마트스토어 파일럿 2주 진행
""")

with open(os.path.join(WORKSPACE, "ai-meeting-room/archive/2023/meeting_legacy.md"), "w", encoding="utf-8") as f:
    f.write("""# 구형 회의록 — 2023
주제: NFT 마케팅 플랫폼
결론: No-Go (시장 붕괴)
""")

# Research files (distractor - raw, incomplete)
with open(os.path.join(WORKSPACE, "projects/pb-drink-brand/research/market_notes_raw.txt"), "w", encoding="utf-8") as f:
    f.write("""편의점 RTD 음료 시장 메모 (미완성)
- 시장규모 어딘가에서 봤는데 기억안남
- 단백질 음료 트렌드는 확실히 있음
- 경쟁사: 밀크단백, 셀렉스 뭔가?
- 편의점 입점 조건 모름
- TODO: 통계청 확인 필요
""")

with open(os.path.join(WORKSPACE, "projects/pb-drink-brand/research/competitor_draft.csv"), "w", encoding="utf-8") as f:
    f.write("""brand,price,channel
셀렉스,2500,convenience
밀크단백,1800,online
빙그레 단백질,2200,convenience
[INCOMPLETE DATA]
""")

# Finance notes (distractor)
with open(os.path.join(WORKSPACE, "projects/pb-drink-brand/finance/cost_estimate_v1.txt"), "w", encoding="utf-8") as f:
    f.write("""원가 추정 (v1 - 검토 전)
OEM 생산비: 불명확
편의점 수수료: 30-35% 추정
마진: ??
""")

# Internal HR / Legal distractors
with open(os.path.join(WORKSPACE, "internal/hr/team_structure.txt"), "w", encoding="utf-8") as f:
    f.write("팀 구성: 대표 1, 마케터 1, 재무 1 (파트타임)\n")

with open(os.path.join(WORKSPACE, "internal/legal/food_license_checklist.txt"), "w", encoding="utf-8") as f:
    f.write("""식품 관련 인허가 체크리스트 (미완성)
- 식품위생법 ???
- 건강기능식품법 ???
- 영양성분 표시 의무 ???
""")

# Templates dir placeholder
with open(os.path.join(WORKSPACE, "ai-meeting-room/templates/sprint_example.txt"), "w", encoding="utf-8") as f:
    f.write("스프린트 모드 예시 템플릿 (실제 사용 아님)\n")

# Logs dir placeholder
with open(os.path.join(WORKSPACE, "ai-meeting-room/logs/.gitkeep"), "w") as f:
    f.write("")

# Another distractor
with open(os.path.join(WORKSPACE, "projects/pb-drink-brand/BRAINSTORM_DUMP.txt"), "w", encoding="utf-8") as f:
    f.write("""아이디어 덤프 (정리 안됨)
- 편의점 PB 단백질 음료: GS25나 CU에 OEM으로 납품?
- 타겟: 20-30대 남성 헬스인구? 아니면 다이어트 여성?
- 가격: 1500-2000원대?
- 차별화: 뭐로?
""")

print("Workspace generated successfully.")
print(f"Files in workspace:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for file in files:
        filepath = os.path.join(root, file)
        print(f"  {filepath}")