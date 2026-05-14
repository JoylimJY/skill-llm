import os
import random

random.seed(42)

# Create deep, realistic fintech project structure
dirs = [
    "workspace/src/payments",
    "workspace/src/auth",
    "workspace/src/orders",
    "workspace/src/reporting",
    "workspace/src/lib",
    "workspace/src/components",
    "workspace/src/hooks",
    "workspace/tests/unit",
    "workspace/tests/integration",
    "workspace/scripts",
    "workspace/.claude/rules",
    "workspace/docs",
    "workspace/config",
    "workspace/src/payments/processors",
    "workspace/src/auth/providers",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor source files
files = {
    "workspace/src/payments/stripe.ts": "export const processPayment = (amount: number) => { /* Stripe integration */ };",
    "workspace/src/payments/processors/ach.ts": "export const processACH = (routing: string, account: string) => {};",
    "workspace/src/auth/auth.ts": "// CRITICAL: Auth logic. Do not modify externally.\nexport const verifyToken = (token: string) => {};",
    "workspace/src/auth/providers/oauth.ts": "export const oauthCallback = () => {};",
    "workspace/src/orders/orders.ts": "import { vi } from 'vitest';\nexport const getOrders = () => {};",
    "workspace/src/lib/state.ts": "import { create } from 'zustand';\nexport const useStore = create(() => ({}));",
    "workspace/src/components/PaymentForm.tsx": "import clsx from 'clsx';\nexport const PaymentForm = () => <form className={clsx('form')} />;",
    "workspace/src/hooks/usePayment.ts": "export const usePayment = () => {};",
    "workspace/src/reporting/reports.ts": "// PO = Purchase Order (NOT Product Owner)\nexport const generatePOReport = () => {};",
    "workspace/tests/unit/payment.test.ts": "describe('payment', () => { it('processes correctly', () => {}); });",
    "workspace/tests/integration/auth.test.ts": "describe('auth', () => { it('validates tokens', () => {}); });",
    "workspace/scripts/migrate.sh": "#!/bin/bash\necho 'Running migrations...'",
    "workspace/config/jest.config.js": "module.exports = { preset: 'ts-jest' };",
    "workspace/docs/api.md": "# API Documentation\n\n## Endpoints\n\n- POST /payments\n- GET /orders",
    "workspace/package.json": '{"name": "paystream-core", "version": "1.0.0", "scripts": {"test": "jest --coverage", "build": "tsc && next build", "lint": "eslint src/", "dev": "next dev", "typecheck": "tsc --noEmit"}}',
    "workspace/tsconfig.json": '{"compilerOptions": {"strict": true, "target": "ES2020"}}',
}

for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)

# THE MAIN PROBLEM: A bloated, badly structured CLAUDE.md at project root
bloated_claude_md = """\
# PayStream Core - AI Assistant Configuration Guide

Welcome to the PayStream Core project! This document contains comprehensive guidelines for our AI coding assistant.
Please read all sections carefully before making any changes to the codebase.

## About This Project

This is a Next.js-based payment processing platform with Stripe integration. The backend uses Supabase for data storage.
We process payments for enterprise clients. PO means Purchase Order, not Product Owner.
The team uses agile methodology with two-week sprints.

## Programming Best Practices

- Write clean, readable code
- Use meaningful variable names
- Add comments where necessary
- Write unit tests for all new features
- Follow DRY principles
- Keep functions small and focused
- Use TypeScript for type safety
- Handle errors appropriately
- Follow SOLID principles
- Use async/await over promises where possible
- Avoid magic numbers; use constants instead

## Commands

- To run tests: `jest --coverage`
- To build the project: `tsc && next build`
- To run linting: `eslint src/`
- To start dev server: `next dev`
- For type checking: `tsc --noEmit`
- Install dependencies: `pnpm install`

## Code Style

- Use 2-space indentation
- Use 2-space indentation for all files (yes, this is important!)
- Prefer TypeScript over JavaScript
- Use meaningful variable names
- Use `useState` for component state management
- Or alternatively, you can use Zustand for global state
- Use `clsx` for conditional CSS classes
- Follow React best practices
- Use functional components over class components
- Use hooks for side effects

## Architecture Notes

- The auth module is in src/auth/
- NEVER modify src/auth/auth.ts directly - all auth changes go through the auth team's PR process
- Payment processing is in src/payments/
- The reporting module uses PO to mean Purchase Order
- State management uses Zustand (not useState or Context)
- Always use `clsx` for conditional classes

## Git Workflow

- Use feature branches
- Branch names follow the pattern: feature/your-feature-name
- Commit messages should be descriptive
- Use conventional commits format (feat:, fix:, chore:, etc.)
- Always create a PR before merging
- Get at least one approval before merging
- Squash commits when merging

## Testing

- Write unit tests for all functions
- Integration tests live in tests/integration/
- Unit tests live in tests/unit/
- Run tests before committing
- Maintain >80% code coverage

## Security

- NEVER commit .env files
- NEVER commit .env files or secrets (this is critical!)
- Use environment variables for secrets
- Never hardcode API keys
- Follow OWASP guidelines
- Use HTTPS everywhere

## File Structure Rules for Payments Module

- Payment processors are in src/payments/processors/
- Use ACH for bank transfers
- Stripe integration is in src/payments/stripe.ts
- Never bypass payment validation
- Always log payment attempts

## IMPORTANT RULES

- NEVER modify src/auth/auth.ts directly
- NEVER commit .env files
- PO = Purchase Order not Product Owner
- State management: use Zustand, not useState or Context API
- Use clsx for conditional classes
- NEVER modify src/auth/auth.ts directly (repeating for emphasis)
- Always use pnpm, not npm or yarn

## More Style Notes

- Use arrow functions
- Use destructuring where possible
- Prefer const over let
- Avoid var entirely

## Contact

For questions about the payments module, contact the payments team.
For auth issues, contact the auth team.
For reporting issues, contact the reporting team.
"""

with open("workspace/CLAUDE.md", "w") as f:
    f.write(bloated_claude_md)

# Also create a partial CLAUDE.md in the payments subdirectory that has issues
payments_claude = """\
# Payments Module

## Rules for Payments Module

- Write clean code
- NEVER commit .env files
- Payment processors are in src/payments/processors/
- Never bypass payment validation
- Always log payment attempts
- Use meaningful variable names
- State management: use Zustand, not useState or Context API
- NEVER modify src/auth/auth.ts directly
"""

with open("workspace/src/payments/CLAUDE.md", "w") as f:
    f.write(payments_claude)

print("Workspace generated successfully.")
print("Files created:")
for root, subdirs, filenames in os.walk("workspace"):
    for filename in filenames:
        print(f"  {os.path.join(root, filename)}")