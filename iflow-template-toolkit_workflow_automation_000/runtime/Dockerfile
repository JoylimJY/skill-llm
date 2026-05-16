FROM python:3.10-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pytest

# Install the iflow-template-toolkit skill
RUN mkdir -p /skills
WORKDIR /skills
RUN git clone https://github.com/iflowfor8hours/iflow-template-toolkit.git || true

# Fallback: manually scaffold the toolkit if clone fails
RUN mkdir -p /skills/iflow-template-toolkit/src/i18n/langs && \
    mkdir -p /skills/iflow-template-toolkit/src/templates

# Write the toolkit source inline so the container is self-contained
RUN printf '%s\n' \
'import os, json' \
'base = "/skills/iflow-template-toolkit/src"' \
'te = open(os.path.join(base, "template_engine.py"), "w")' \
'te.write("""' \
'import re' \
'import os' \
'' \
'class TemplateEngine:' \
'    def __init__(self, template_dir="."):' \
'        self.template_dir = template_dir' \
'' \
'    def render_file(self, filename, context):' \
'        path = os.path.join(self.template_dir, filename)' \
'        with open(path, "r", encoding="utf-8") as f:' \
'            template = f.read()' \
'        return self._render(template, context)' \
'' \
'    def render(self, template, context):' \
'        return self._render(template, context)' \
'' \
'    def _render(self, template, context):' \
'        result = self._process_blocks(template, context)' \
'        result = self._substitute_vars(result, context)' \
'        return result' \
'' \
'    def _substitute_vars(self, text, context):' \
'        def replacer(m):' \
'            key = m.group(1).strip()' \
'            return str(context.get(key, ""))' \
'        return re.sub(r"\\\\{\\\\{(.*?)\\\\}\\\\}", replacer, text)' \
'' \
'    def _process_blocks(self, text, context):' \
'        text = self._process_for_blocks(text, context)' \
'        text = self._process_if_blocks(text, context)' \
'        return text' \
'' \
'    def _process_for_blocks(self, text, context):' \
'        pattern = re.compile(' \
'            r"\\\\{%\\\\s*for\\\\s+(\\\\w+)\\\\s+in\\\\s+(\\\\w+)\\\\s*%\\\\}(.*?)\\\\{%\\\\s*endfor\\\\s*%\\\\}",' \
'            re.DOTALL' \
'        )' \
'        def expand(m):' \
'            var_name = m.group(1)' \
'            list_name = m.group(2)' \
'            body = m.group(3)' \
'            items = context.get(list_name, [])' \
'            out = []' \
'            total = len(items)' \
'            for i, item in enumerate(items):' \
'                loop_ctx = dict(context)' \
'                loop_ctx[var_name] = item' \
'                loop_ctx["index"] = i' \
'                loop_ctx["index1"] = i + 1' \
'                loop_ctx["first"] = (i == 0)' \
'                loop_ctx["last"] = (i == total - 1)' \
'                rendered = self._render(body, loop_ctx)' \
'                out.append(rendered)' \
'            return "".join(out)' \
'        return pattern.sub(expand, text)' \
'' \
'    def _process_if_blocks(self, text, context):' \
'        pattern = re.compile(' \
'            r"\\\\{%\\\\s*if\\\\s+(.*?)\\\\s*%\\\\}(.*?)\\\\{%\\\\s*endif\\\\s*%\\\\}",' \
'            re.DOTALL' \
'        )' \
'        def evaluate(m):' \
'            condition_block = m.group(0)' \
'            return self._evaluate_if_chain(condition_block, context)' \
'        return pattern.sub(evaluate, text)' \
'' \
'    def _evaluate_if_chain(self, block, context):' \
'        parts = re.split(r"\\\\{%\\\\s*(?:elif|else).*?%\\\\}", block)' \
'        headers = re.findall(r"\\\\{%\\\\s*(if|elif|else)(.*?)%\\\\}", block)' \
'        branches = []' \
'        for i, part in enumerate(parts):' \
'            part = re.sub(r"^\\\\{%.*?%\\\\}", "", part).rstrip()' \
'            part = re.sub(r"\\\\{%\\\\s*endif\\\\s*%\\\\}$", "", part).strip()' \
'            if i < len(headers):' \
'                tag, cond = headers[i]' \
'                branches.append((tag.strip(), cond.strip(), part))' \
'        for tag, cond, body in branches:' \
'            if tag == "else":' \
'                return self._render(body, context)' \
'            if self._eval_condition(cond, context):' \
'                return self._render(body, context)' \
'        return ""' \
'' \
'    def _eval_condition(self, cond, context):' \
'        not_in_m = re.match(r"(\\\\w+)\\\\s+not in\\\\s+(\\\\w+)", cond)' \
'        in_m = re.match(r"(\\\\w+)\\\\s+in\\\\s+(\\\\w+)", cond)' \
'        eq_m = re.match(r"(\\\\w+)\\\\s*==\\\\s*\\"(.*?)\\"", cond)' \
'        neq_m = re.match(r"(\\\\w+)\\\\s*!=\\\\s*\\"(.*?)\\"", cond)' \
'        if not_in_m:' \
'            val = context.get(not_in_m.group(1))' \
'            lst = context.get(not_in_m.group(2), [])' \
'            return val not in lst' \
'        if in_m:' \
'            val = context.get(in_m.group(1))' \
'            lst = context.get(in_m.group(2), [])' \
'            return val in lst' \
'        if eq_m:' \
'            return str(context.get(eq_m.group(1), "")) == eq_m.group(2)' \
'        if neq_m:' \
'            return str(context.get(neq_m.group(1), "")) != neq_m.group(2)' \
'        return False' \
'' \
'' \
'def render_template(template_str, context):' \
'    engine = TemplateEngine()' \
'    return engine.render(template_str, context)' \
'""")' \
'te.close()' \
> /scaffold_toolkit.py && python3 /scaffold_toolkit.py || true

RUN python3 - <<'PYEOF'
import os

base = '/skills/iflow-template-toolkit/src'

te_code = '''import re\nimport os\n\nclass TemplateEngine:\n    def __init__(self, template_dir="."):\n        self.template_dir = template_dir\n\n    def render_file(self, filename, context):\n        path = os.path.join(self.template_dir, filename)\n        with open(path, "r", encoding="utf-8") as f:\n            template = f.read()\n        return self._render(template, context)\n\n    def render(self, template, context):\n        return self._render(template, context)\n\n    def _render(self, template, context):\n        result = self._process_blocks(template, context)\n        result = self._substitute_vars(result, context)\n        return result\n\n    def _substitute_vars(self, text, context):\n        def replacer(m):\n            key = m.group(1).strip()\n            return str(context.get(key, ""))\n        return re.sub(r"\\{\\{(.*?)\\}\\}", replacer, text)\n\n    def _process_blocks(self, text, context):\n        text = self._process_for_blocks(text, context)\n        text = self._process_if_blocks(text, context)\n        return text\n\n    def _process_for_blocks(self, text, context):\n        pattern = re.compile(\n            r"\\{%\\s*for\\s+(\\w+)\\s+in\\s+(\\w+)\\s*%\\}(.*?)\\{%\\s*endfor\\s*%\\}",\n            re.DOTALL\n        )\n        def expand(m):\n            var_name = m.group(1)\n            list_name = m.group(2)\n            body = m.group(3)\n            items = context.get(list_name, [])\n            out = []\n            total = len(items)\n            for i, item in enumerate(items):\n                loop_ctx = dict(context)\n                loop_ctx[var_name] = item\n                loop_ctx["index"] = i\n                loop_ctx["index1"] = i + 1\n                loop_ctx["first"] = (i == 0)\n                loop_ctx["last"] = (i == total - 1)\n                rendered = self._render(body, loop_ctx)\n                out.append(rendered)\n            return "".join(out)\n        return pattern.sub(expand, text)\n\n    def _process_if_blocks(self, text, context):\n        pattern = re.compile(\n            r"\\{%\\s*if\\s+(.*?)\\s*%\\}(.*?)\\{%\\s*endif\\s*%\\}",\n            re.DOTALL\n        )\n        def evaluate(m):\n            condition_block = m.group(0)\n            return self._evaluate_if_chain(condition_block, context)\n        return pattern.sub(evaluate, text)\n\n    def _evaluate_if_chain(self, block, context):\n        parts = re.split(r"\\{%\\s*(?:elif|else).*?%\\}", block)\n        headers = re.findall(r"\\{%\\s*(if|elif|else)(.*?)%\\}", block)\n        branches = []\n        for i, part in enumerate(parts):\n            part = re.sub(r"^\\{%.*?%\\}", "", part).rstrip()\n            part = re.sub(r"\\{%\\s*endif\\s*%\\}$", "", part).strip()\n            if i < len(headers):\n                tag, cond = headers[i]\n                branches.append((tag.strip(), cond.strip(), part))\n        for tag, cond, body in branches:\n            if tag == "else":\n                return self._render(body, context)\n            if self._eval_condition(cond, context):\n                return self._render(body, context)\n        return ""\n\n    def _eval_condition(self, cond, context):\n        not_in_m = re.match(r"(\\w+)\\s+not in\\s+(\\w+)", cond)\n        in_m = re.match(r"(\\w+)\\s+in\\s+(\\w+)", cond)\n        eq_m = re.match(r\'(\\w+)\\s*==\\s*"(.*?)"\', cond)\n        neq_m = re.match(r\'(\\w+)\\s*!=\\s*"(.*?)"\', cond)\n        if not_in_m:\n            val = context.get(not_in_m.group(1))\n            lst = context.get(not_in_m.group(2), [])\n            return val not in lst\n        if in_m:\n            val = context.get(in_m.group(1))\n            lst = context.get(in_m.group(2), [])\n            return val in lst\n        if eq_m:\n            return str(context.get(eq_m.group(1), "")) == eq_m.group(2)\n        if neq_m:\n            return str(context.get(neq_m.group(1), "")) != neq_m.group(2)\n        return False\n\n\ndef render_template(template_str, context):\n    engine = TemplateEngine()\n    return engine.render(template_str, context)\n'''

with open(os.path.join(base, 'template_engine.py'), 'w') as f:
    f.write(te_code)

tr_code = '''import re\n\n_translator = None\n\nclass Translator:\n    def __init__(self, translations, default_lang="en"):\n        self.translations = translations\n        self.default_lang = default_lang\n\n    def translate(self, key, lang=None, **kwargs):\n        lang = lang or self.default_lang\n        lang_dict = self.translations.get(lang, {})\n        text = lang_dict.get(key)\n        if text is None:\n            lang_dict = self.translations.get(self.default_lang, {})\n            text = lang_dict.get(key, key)\n        if kwargs:\n            for k, v in kwargs.items():\n                text = text.replace("{" + k + "}", str(v))\n        return text\n\n\ndef init_translator(translations, default_lang="en"):\n    global _translator\n    _translator = Translator(translations, default_lang)\n\n\ndef t(key, lang=None, **kwargs):\n    if _translator is None:\n        return key\n    return _translator.translate(key, lang=lang, **kwargs)\n'''

with open(os.path.join(base, 'i18n', 'translator.py'), 'w') as f:
    f.write(tr_code)

with open(os.path.join(base, 'i18n', '__init__.py'), 'w') as f:
    f.write('from .translator import Translator, init_translator, t\n')

with open(os.path.join(base, '__init__.py'), 'w') as f:
    f.write('from .template_engine import TemplateEngine, render_template\nfrom .i18n import Translator, init_translator, t\n')

with open('/skills/iflow-template-toolkit/__init__.py', 'w') as f:
    f.write('from src import TemplateEngine, render_template, Translator, init_translator, t\n')

print('Toolkit scaffolded.')
PYEOF

WORKDIR /workspace
ENV PYTHONPATH="/skills/iflow-template-toolkit"