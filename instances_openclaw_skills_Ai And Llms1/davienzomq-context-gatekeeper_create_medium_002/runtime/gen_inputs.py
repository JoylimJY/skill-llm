from pathlib import Path


def main():
    context_dir = Path('context')
    context_dir.mkdir(parents=True, exist_ok=True)

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
    (Path('context') / 'history.txt').write_text(history, encoding='utf-8')

    marker = "MARKER:CTX-GATEKEEPER-2026-02-06"
    notes = """# Notes
- Marker: MARKER:CTX-GATEKEEPER-2026-02-06
- Expected output: context/current-summary.md
"""
    (Path('context') / 'input-notes.md').write_text(notes, encoding='utf-8')


if __name__ == '__main__':
    main()
