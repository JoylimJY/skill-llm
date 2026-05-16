import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested project structure
dirs = [
    "src/finance/validators",
    "src/finance/models",
    "src/finance/utils",
    "src/finance/parsers",
    "src/reporting",
    "src/reporting/templates",
    "tests/unit",
    "tests/integration",
    "config",
    "docs/api",
    "scripts",
    "logs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but unrelated to the task
distractor_files = {
    "src/finance/models/__init__.py": "# Finance models package\n",
    "src/finance/models/transaction.py": textwrap.dedent("""\
        class Transaction:
            def __init__(self, amount, currency, timestamp):
                self.amount = amount
                self.currency = currency
                self.timestamp = timestamp
        """),
    "src/finance/parsers/__init__.py": "# Parsers package\n",
    "src/finance/parsers/csv_parser.py": textwrap.dedent("""\
        import csv
        def parse_csv(filepath):
            with open(filepath) as f:
                return list(csv.DictReader(f))
        """),
    "src/finance/utils/__init__.py": "# Utils package\n",
    "src/finance/utils/date_utils.py": textwrap.dedent("""\
        from datetime import datetime
        def parse_date(date_str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        """),
    "src/finance/validators/__init__.py": "# Validators package\n",
    "src/reporting/__init__.py": "# Reporting package\n",
    "src/reporting/templates/summary.html": "<html><body>{{ content }}</body></html>\n",
    "tests/unit/__init__.py": "",
    "tests/integration/__init__.py": "",
    "tests/unit/test_transaction.py": textwrap.dedent("""\
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
        from finance.models.transaction import Transaction
        def test_transaction_creation():
            t = Transaction(100.0, 'USD', '2024-01-01')
            assert t.amount == 100.0
            assert t.currency == 'USD'
        """),
    "config/settings.yaml": textwrap.dedent("""\
        app:
          name: FinanceValidator
          version: 1.2.0
          debug: false
        supported_currencies:
          - USD
          - EUR
          - GBP
          - JPY
          - CNY
        rate_limits:
          min: 0.0001
          max: 10000.0
        """),
    "config/logging.conf": textwrap.dedent("""\
        [loggers]
        keys=root,finance
        [handlers]
        keys=consoleHandler
        [formatters]
        keys=simpleFormatter
        """),
    "scripts/run_tests.sh": "#!/bin/bash\npytest tests/ -v\n",
    "logs/.gitkeep": "",
    "docs/api/overview.md": "# API Overview\nThis service validates currency exchange rates.\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a messy/incomplete requirements file that hints at what's needed
with open(os.path.join(workspace, "REQUIREMENTS.txt"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""\
        # Task: Implement currency exchange rate validator
        # Target file: src/finance/validators/exchange_rate_validator.py
        #
        # The validator must:
        # 1. Function: validate_rate(base_currency, quote_currency, rate)
        #    - Returns True if rate is a positive float within [0.0001, 10000.0]
        #    - Returns False otherwise
        #    - base_currency and quote_currency must be non-empty strings
        # 2. Function: validate_currency_code(code)
        #    - Returns True if code is a 3-letter uppercase string (e.g. 'USD', 'EUR')
        #    - Returns False otherwise
        # 3. Function: batch_validate(records)
        #    - Accepts a list of dicts: [{'base': str, 'quote': str, 'rate': float}, ...]
        #    - Returns a list of bools corresponding to each record's validity
        #
        # NOTE: This file is intentionally left incomplete. Use the team automation
        # workflow tools to implement and track the work properly.
    """))

# Create a broken/stub version of the validator to show it's missing implementation
with open(os.path.join(workspace, "src/finance/validators/exchange_rate_validator.py"), "w", encoding="utf-8") as f:
    f.write(textwrap.dedent("""\
        # STUB - NOT IMPLEMENTED
        # TODO: implement validate_rate, validate_currency_code, batch_validate
        raise NotImplementedError("This module has not been implemented yet")
    """))

# Create a git repo (some workflows expect it)
os.system(f"cd {workspace} && git init -q && git config user.email 'agent@test.com' && git config user.name 'Agent'")
os.system(f"cd {workspace} && git add -A && git commit -q -m 'initial stub'")

print("Workspace generated successfully.")