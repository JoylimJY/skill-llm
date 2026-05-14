import os
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "finpay-app/src/payments",
    "finpay-app/src/auth",
    "finpay-app/src/utils",
    "finpay-app/src/api",
    "finpay-app/tests",
    "finpay-app/config",
    "finpay-app/scripts",
    "finpay-app/docs",
    "finpay-app/migrations",
    "finpay-app/.github/workflows",
    "skill",
    "skill/references",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = """\
name: pr-code-reviewer
description: >
  Revisa automáticamente Pull Requests en Bitbucket detectando errores de
  sintaxis, malas prácticas, vulnerabilidades de seguridad y violaciones
  de estándares de código del equipo. Genera comentarios detallados con
  sugerencias de corrección. Soporta JavaScript, TypeScript, Node.js, PHP y Python.
version: 1.0.0
tags:
  - code-review
  - pull-request
  - quality
  - bitbucket
  - linting
  - nodejs
  - php
---

# PR Code Reviewer

## Rol

Eres un Senior Code Reviewer exigente pero constructivo. Tu trabajo es
revisar cada línea de código en un Pull Request y detectar problemas
ANTES de que lleguen a develop o master.

## Comportamiento General

### Cuando recibas un diff o código de un PR:

1. **Lee TODO el diff completo** antes de emitir cualquier comentario
2. **Entiende el contexto**: qué intenta hacer el PR, no solo línea por línea
3. **Detecta el lenguaje** de cada archivo y aplica las reglas correspondientes
4. **Clasifica cada hallazgo** por severidad:
   - 🔴 **BLOCKER** — No se puede mergear. Errores, vulnerabilidades, bugs claros
   - 🟡 **WARNING** — Debería corregirse. Malas prácticas, code smells
   - 🔵 **SUGGESTION** — Mejora opcional. Estilo, legibilidad, optimización
   - 💡 **NIT** — Detalle menor. Convenciones, formato
5. **Siempre sugiere la corrección**, no solo señales el problema
6. **Agrupa comentarios** por archivo
7. **Da un veredicto final**: ✅ APROBAR, ⚠️ APROBAR CON CAMBIOS, ❌ RECHAZAR

## Detección de Lenguaje

Aplica las reglas del lenguaje según la extensión del archivo:

- .js, .mjs, .cjs → references/javascript-typescript.md + references/nodejs.md
- .ts, .tsx → references/javascript-typescript.md + references/nodejs.md
- .jsx → references/javascript-typescript.md + references/nodejs.md
- .php → references/php.md
- .py → references/python.md
- .css, .scss, .html → references/css-html.md
- Todos los archivos → references/general.md + references/security.md + references/team-conventions.md

## Formato de Respuesta

Siempre responde con este formato exacto:

## 📋 Resumen de Revisión del PR

**Veredicto:** [✅ | ⚠️ | ❌] [APROBAR | APROBAR CON CAMBIOS | RECHAZAR]
**Archivos revisados:** X
**Hallazgos:** X 🔴 | X 🟡 | X 🔵 | X 💡

---

### 📁 ruta/al/archivo.ext

**Línea X-Y:**
[🔴|🟡|🔵|💡] **[Categoría]**: Descripción del problema

❌ Código actual:
(mostrar el código problemático)

✅ Corrección sugerida:
(mostrar el código corregido)

**¿Por qué?** Explicación breve de por qué es un problema.

---

### 🏁 Resumen Final
- Lo bueno: ...
- Lo que debe corregirse antes del merge: ...
- Sugerencias para el futuro: ...

## Reglas

Importar y aplicar TODAS las reglas de:

- references/general.md (siempre)
- references/security.md (siempre)
- references/team-conventions.md (siempre)
- references/javascript-typescript.md (según extensión)
- references/nodejs.md (según extensión)
- references/php.md (según extensión)
- references/python.md (según extensión)
- references/css-html.md (según extensión)
"""
with open(os.path.join(BASE, "skill", "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── Reference files ───────────────────────────────────────────────────────────
refs = {
    "general.md": """\
# General Rules

## DRY (Don't Repeat Yourself)
- No code duplication. If the same logic appears twice, extract a function.

## Error Handling
- Never swallow exceptions silently (bare `except: pass`, empty catch blocks).
- Always log or re-raise.

## Magic Numbers
- No hard-coded numeric literals without named constants.

## Dead Code
- Remove commented-out code blocks before merging.

## Long Functions
- Functions longer than 40 lines should be split.
""",
    "security.md": """\
# Security Rules

## Injection Prevention
- NEVER concatenate user input into SQL queries. Use parameterized queries / ORM.
- NEVER use `eval()` with user-controlled data.

## Hardcoded Secrets
- NEVER hardcode API keys, passwords, tokens, or private keys in source code.
- Use environment variables or a secrets manager.

## Sensitive Data Logging
- NEVER log credit card numbers, passwords, tokens, or PII.

## Input Validation
- All user-supplied inputs MUST be validated before use.
- Numeric IDs must be cast and range-checked.

## Dependency Safety
- Flag imports of known-unsafe or deprecated modules (e.g., Python `pickle` for untrusted data).
""",
    "team-conventions.md": """\
# Team Conventions

## Naming
- Variables and functions: snake_case (Python, PHP) or camelCase (JS/TS).
- Classes: PascalCase in all languages.
- Constants: UPPER_SNAKE_CASE.

## Comments
- Public functions MUST have a docstring/JSDoc comment.
- Inline comments must explain WHY, not WHAT.

## File Header
- Every new file must start with a module-level docstring or block comment describing its purpose.

## Test Coverage
- Every new public function should have at least one unit test referenced.

## TODO/FIXME
- No unresolved TODO or FIXME comments allowed in files targeting develop/master.
""",
    "python.md": """\
# Python-Specific Rules

## Type Hints
- All function signatures MUST include type hints (PEP 484).

## f-strings
- Prefer f-strings over `.format()` or `%` formatting for readability.

## Context Managers
- File and DB connections MUST use `with` statements.

## List Comprehensions
- Prefer list comprehensions over `map()`/`filter()` when readable.

## Exception Specificity
- Catch specific exceptions, not bare `except Exception` or `except:`.

## Imports
- Standard library imports first, then third-party, then local. One import per line.
""",
    "javascript-typescript.md": """\
# JavaScript/TypeScript Rules

## var Forbidden
- NEVER use `var`. Use `const` by default, `let` only when reassignment is needed.

## Strict Equality
- Always use `===` and `!==`. Never `==` or `!=`.

## Async/Await
- Prefer `async/await` over raw `.then()/.catch()` chains for readability.

## Arrow Functions
- Prefer arrow functions for callbacks and short utilities.

## Console Statements
- Remove all `console.log` statements before merging.

## Error Handling
- Every `async` function must have try/catch or return a handled Promise.
""",
    "nodejs.md": """\
# Node.js Rules

## Environment Variables
- Use `process.env` for configuration. Never hardcode hostnames, ports, or credentials.

## Callback Hell
- No deeply nested callbacks. Use Promises or async/await.

## Require vs Import
- Stick to one module system per project. Do not mix `require()` and `import`.

## Unhandled Rejections
- All Promise rejections must be handled. Use `.catch()` or try/catch.

## Input Sanitization
- Sanitize all inputs before passing to DB queries or shell commands.

## Path Traversal
- Validate and sanitize file paths derived from user input.
""",
    "php.md": """\
# PHP Rules

## SQL Injection
- NEVER build SQL with string concatenation. Always use PDO prepared statements.

## Output Escaping
- All user-supplied data rendered to HTML must be escaped with `htmlspecialchars()`.

## Error Display
- `display_errors` must be OFF in production. Use logging instead.

## Password Hashing
- NEVER store plain-text passwords. Use `password_hash()` / `password_verify()`.

## Deprecated Functions
- Do not use `mysql_*` functions (removed in PHP 7). Use PDO or MySQLi.

## Superglobals
- Direct use of `$_GET`, `$_POST`, `$_REQUEST` without sanitization is forbidden.
""",
    "css-html.md": """\
# CSS/HTML Rules

## Semantic HTML
- Use semantic elements (`<main>`, `<section>`, `<article>`, `<nav>`).

## Inline Styles
- No inline `style` attributes. Use CSS classes.

## Accessibility
- All `<img>` elements must have descriptive `alt` attributes.
- Interactive elements must be keyboard-accessible.
""",
}

for fname, content in refs.items():
    with open(os.path.join(BASE, "skill", "references", fname), "w") as f:
        f.write(content)

# ── PR diff file (the input the agent must review) ────────────────────────────
pr_diff = """\
diff --git a/finpay-app/src/payments/charge.py b/finpay-app/src/payments/charge.py
new file mode 100644
--- /dev/null
+++ b/finpay-app/src/payments/charge.py
@@ -0,0 +1,52 @@
+import os
+import pickle
+import logging
+import requests
+
+SECRET_KEY = "sk_live_ABCDEF1234567890"
+DB_PASSWORD = "SuperSecret99!"
+
+def charge_customer(customer_id, amount, card_number):
+    logging.info(f"Charging card {card_number} for customer {customer_id} amount {amount}")
+    conn = get_db_connection()
+    query = "SELECT * FROM customers WHERE id = " + str(customer_id)
+    result = conn.execute(query)
+    try:
+        data = pickle.loads(result.fetchone()["payment_profile"])
+    except:
+        pass
+    r = requests.post("https://payment-gateway.internal/charge",
+                      data={"amount": amount, "card": card_number, "key": SECRET_KEY})
+    return r.json()
+
+def validate_amount(amount):
+    if amount == 0:
+        return False
+    if amount == None:
+        return False
+    return True
+
+def get_db_connection():
+    import sqlite3
+    conn = sqlite3.connect("payments.db")
+    return conn
+
+# TODO: add retry logic
+# TODO: implement refund endpoint
+
+def process_refund(order_id, amount):
+    conn = get_db_connection()
+    query = "DELETE FROM orders WHERE id = " + str(order_id) + " AND amount=" + str(amount)
+    conn.execute(query)
+    conn.commit()
+
+def _helper(x, y, z, a, b, c, d, e, f, g):
+    result = []
+    for i in range(x):
+        for j in range(y):
+            for k in range(z):
+                result.append(i*j*k*a*b*c*d*e*f*g)
+    return result

diff --git a/finpay-app/src/api/webhook.js b/finpay-app/src/api/webhook.js
new file mode 100644
--- /dev/null
+++ b/finpay-app/src/api/webhook.js
@@ -0,0 +1,38 @@
+var express = require('express');
+var router = express.Router();
+var db = require('../db');
+
+const WEBHOOK_SECRET = "wh_secret_XYZ987";
+
+router.post('/webhook', function(req, res) {
+    var payload = req.body;
+    var userId = payload.user_id;
+
+    db.query("SELECT * FROM users WHERE id = " + userId, function(err, rows) {
+        if (err) {
+            console.log("DB error: " + err);
+            res.status(500).send("error");
+        } else {
+            processWebhook(payload, rows).then(result => {
+                res.json(result);
+            })
+        }
+    });
+});
+
+async function processWebhook(payload, userData) {
+    var eventType = payload.event_type;
+    if (eventType == "payment.success") {
+        console.log("Payment succeeded for user: " + payload.user_id);
+        return await handlePaymentSuccess(payload, userData);
+    } else if (eventType == "payment.failed") {
+        return await handlePaymentFailure(payload, userData);
+    }
+}
+
+async function handlePaymentSuccess(payload, userData) {
+    // TODO: send confirmation email
+    return { status: "ok" };
+}
+
+async function handlePaymentFailure(payload, userData) {
+    return { status: "failed" };
+}

diff --git a/finpay-app/src/payments/invoice.php b/finpay-app/src/payments/invoice.php
new file mode 100644
--- /dev/null
+++ b/finpay-app/src/payments/invoice.php
@@ -0,0 +1,30 @@
+<?php
+$host = "localhost";
+$dbUser = "root";
+$dbPass = "rootpass123";
+
+$conn = new mysqli($host, $dbUser, $dbPass, "finpay");
+
+$invoiceId = $_GET['invoice_id'];
+$customerId = $_GET['customer_id'];
+
+$query = "SELECT * FROM invoices WHERE id = '$invoiceId' AND customer_id = '$customerId'";
+$result = $conn->query($query);
+
+$row = $result->fetch_assoc();
+
+echo "<h1>Invoice for: " . $row['customer_name'] . "</h1>";
+echo "<p>Amount: " . $row['amount'] . "</p>";
+
+$passwordHash = md5($_POST['password']);
+$storedHash = $row['password_hash'];
+
+if ($passwordHash == $storedHash) {
+    echo "Access granted";
+} else {
+    echo "Access denied";
+}
+
+// FIXME: this entire auth flow needs rework
+?>
"""

with open(os.path.join(BASE, "finpay-app", "pr_diff.txt"), "w") as f:
    f.write(pr_diff)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "finpay-app/config/database.yml": "host: localhost\nport: 5432\nname: finpay_prod\n",
    "finpay-app/config/logging.conf": "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n",
    "finpay-app/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "finpay-app/migrations/001_init.sql": "CREATE TABLE customers (id INTEGER PRIMARY KEY);\n",
    "finpay-app/migrations/002_invoices.sql": "CREATE TABLE invoices (id INTEGER PRIMARY KEY, amount DECIMAL);\n",
    "finpay-app/tests/test_utils.py": "def test_dummy():\n    assert True\n",
    "finpay-app/src/utils/currency.py": "def format_currency(amount):\n    return f'${amount:.2f}'\n",
    "finpay-app/src/auth/login.py": "def authenticate(user, pwd):\n    return user == 'admin' and pwd == 'admin'\n",
    "finpay-app/.github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "finpay-app/docs/architecture.md": "# Architecture\nMicroservices based fintech platform.\n",
    "finpay-app/src/api/health.js": "module.exports = (req, res) => res.json({ status: 'ok' });\n",
    "finpay-app/src/payments/refund.py": "def refund(order_id):\n    pass\n",
}
for path, content in distractors.items():
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

print("Workspace generated successfully.")