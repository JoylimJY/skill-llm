from pathlib import Path
from textwrap import dedent

base = Path('.')
context = base / 'context'
context.mkdir(exist_ok=True)

history = dedent('''
USER: Quero montar um plano para 2026.
ASSISTANT: Você precisa decidir métricas e milestones antes de investir.
USER: Precisamos incluir Itaú no portfólio e revisar as métricas de eficiência.
ASSISTANT: Confirmo que a carteira deve equilibrar liquidez e dividendos; revisar payout e ROY.
USER: Liste o que falta para finalizar a análise.
USER: Como podemos testar essa primeira parte?
ASSISTANT: Para testar o “Context Gatekeeper" agora mesmo, você grava o log e roda o script etc.
USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
USER: Qual nome dos 12 discípulos de Jesus?
USER: Você sabe todas nossas regras?
''').lstrip()

summary = dedent('''
# Context Gatekeeper
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
- ASSISTANT: Para testar o “Context Gatekeeper" agora mesmo, you grava o log e roda o script etc.
- USER: Sim faça isso e ai vamos testar deixe tudo de maneira automática então Antes de cada resposta dele tudo roda e ele so usa os tokens necessárias sem perder a memória me avise quando terminar e vamos testar
- USER: Qual nome dos 12 discípulos de Jesus?
- USER: Você sabe todas nossas regras?
''').lstrip()

(context / 'history.txt').write_text(history, encoding='utf-8')
(context / 'current-summary.md').write_text(summary, encoding='utf-8')

# Deterministic marker file for verification
(base / 'marker.txt').write_text('CTX-GATEKEEPER-MARKER-2026\n', encoding='utf-8')
