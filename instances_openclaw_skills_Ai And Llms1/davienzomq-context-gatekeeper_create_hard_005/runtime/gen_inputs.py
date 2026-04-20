from pathlib import Path

base = Path('.')
context_dir = base / 'context'
context_dir.mkdir(parents=True, exist_ok=True)
skills_dir = base / 'skills' / 'context-gatekeeper' / 'scripts'
skills_dir.mkdir(parents=True, exist_ok=True)

history = """USER: Quero montar um plano para 2026.
ASSISTANT: Você precisa decidir métricas e milestones antes de investir.
USER: Precisamos incluir Itaú no portfólio e revisar as métricas de eficiência.
ASSISTANT: Confirmo que a carteira deve equilibrar liquidez e dividendos; revisar payout e ROY.
USER: Liste o que falta para finalizar a análise.
USER: Como podemos testar essa primeira parte?
ASSISTANT: Para testar o “Context Gatekeeper" agora mesmo, você grava o log e roda o script etc.
USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
USER: Qual nome dos 12 discípulos de Jesus?
USER: Você sabe todas nossas regras?
"""

(context_dir / 'history.txt').write_text(history, encoding='utf-8')

summary = """# Context Gatekeeper
_Gerado: 2026-02-06T13:05:24+00:00_

## Resumo compacto
- Quero montar um plano para 2026.
- Você precisa decidir métricas e milestones antes de investir.
- Precisamos incluir Itaú no portfólio e revisar as métricas de eficiência.
- Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
- Qual nome dos 12 discípulos de Jesus?
- Você sabe todas nossas regras?

## Pendências e próximos passos
- Nenhuma pendência identificada no histórico recente.

## Últimos turnos
- ASSISTANT: Para testar o “Context Gatekeeper" agora mesmo, você grava o log e roda o script etc.
- USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
- USER: Qual nome dos 12 discípulos de Jesus?
- USER: Você sabe todas nossas regras?
"""
(context_dir / 'current-summary.md').write_text(summary, encoding='utf-8')

skill_md = """---
name: context-gatekeeper
description: Keeps the conversation token-friendly by summarizing recent exchanges, surfacing pending actions, and delivering a compact briefing for each turn before calling the model. Trigger this skill whenever you need to prune a bloated thread or keep the next prompt lean.
author: Davi Marques
---

# Context Gatekeeper

## Objetivo
Reduzir o volume de tokens enviados ao modelo preservando apenas o essencial: o resumo das decisões, os próximos passos e os trechos mais recentes da conversa. Este skill roda em paralelo à sua rotina habitual, produzindo o artefato `context/current-summary.md` que serve como contexto de substituição (em vez de reenviar toda a conversa).
"""
(base / 'SKILL.md').write_text(skill_md, encoding='utf-8')
