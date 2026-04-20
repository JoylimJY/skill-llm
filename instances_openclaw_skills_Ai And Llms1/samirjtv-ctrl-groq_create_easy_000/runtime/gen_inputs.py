from pathlib import Path

# Deterministic input file with a marker the evaluator can verify.
Path('input_message.txt').write_text('MARKER: groq-completion-easy-task\nWrite a short greeting for a user named Alex.\n', encoding='utf-8')
