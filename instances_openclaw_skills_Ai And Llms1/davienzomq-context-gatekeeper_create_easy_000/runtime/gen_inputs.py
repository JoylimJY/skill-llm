import os
from pathlib import Path

base = Path('.')
context = base / 'context'
context.mkdir(exist_ok=True)

history = """USER: Quero montar um plano para 2026.
ASSISTANT: Você precisa decidir métricas e milestones antes de investir.
USER: Precisamos incluir Itaú no portfólio e revisar as métricas de eficiência.
ASSISTANT: Confirmo que a carteira deve equilibrar liquidez e dividendos; revisar payout e ROY.
USER: Liste o que falta para finalizar a análise.
USER: Como podemos testar essa primeira parte?
ASSISTANT: Para testar o Context Gatekeeper agora mesmo, você grava o log e roda o script etc.
USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
USER: Qual nome dos 12 discípulos de Jesus?
USER: Você sabe todas nossas regras?
"""

(context / 'history.txt').write_text(history, encoding='utf-8')

summary = """# Context Gatekeeper
_Gerado: 2026-02-06T13:05:24+00:00_

## Resumo compacto
- Quer montar um plano para 2026.
- É preciso decidir métricas e milestones antes de investir.
- Incluir Itaú no portfólio e revisar métricas de eficiência.

## Pendências e próximos passos
- Liste o que falta para finalizar a análise.
- Testar a primeira parte e automatizar o fluxo antes de cada resposta.

## Últimos turnos
- USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
- USER: Qual nome dos 12 discípulos de Jesus?
- USER: Você sabe todas nossas regras?
"""

(context / 'current-summary.md').write_text(summary, encoding='utf-8')
