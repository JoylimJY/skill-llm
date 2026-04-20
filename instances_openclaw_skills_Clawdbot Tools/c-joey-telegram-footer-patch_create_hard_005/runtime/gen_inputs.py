from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'dist').mkdir(exist_ok=True)
(root / 'scripts').mkdir(exist_ok=True)

# Primary bundle with marker-friendly structure.
main_js = """(function(){
  const version = 'openclaw-2026.3.22';
  function formatTokens(tokens){
    return tokens.join(' ');
  }
  function sendReply(chat, text){
    return { chat, text, meta: formatTokens(['ok']) };
  }
  module.exports = { version, sendReply };
})();
"""

# Alternate bundle that should not be patched unless discovery needs it.
alt_js = """export function replyMessage(chat, text) {
  const base = text.trim();
  return base;
}
"""

# Bundle with a marker hint and a comment to aid fuzzy discovery.
hint_js = """// candidate reply bundle for telegram footer patch
function handlePrivateChat(message) {
  const reply = message.content;
  return reply;
}
"""

files = {
    'dist/agent-runner.runtime-BWpOtdxK.js': main_js,
    'dist/reply-mini-X7a9.js': alt_js,
    'dist/compact-pi-embedded-Q9m2.js': hint_js,
}
for rel, content in files.items():
    (root / rel).write_text(content, encoding='utf-8')

metadata = {
    'bundle_candidates': list(files.keys()),
    'known_marker': '🧠 Model + 💭 Think + 📊 Context',
    'expected_primary': 'dist/agent-runner.runtime-BWpOtdxK.js',
}
(root / 'fixture_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

# Deterministic prompt hints for the task implementation.
(root / 'scripts' / 'placeholder.txt').write_text('patch utility workspace fixture', encoding='utf-8')
