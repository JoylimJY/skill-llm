import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor directory structure ---
distractor_dirs = [
    "src/api/handlers",
    "src/api/middleware",
    "src/components/ui",
    "src/components/charts",
    "src/utils",
    "src/types",
    "tests/unit",
    "tests/integration",
    "docs/internal",
    "docs/public",
    "scripts",
    "assets/icons",
    "assets/fonts",
    ".github/workflows",
    "snippets/auth",
    "snippets/data",
    "snippets/hooks",
    "snippets/utils",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/api/handlers/userHandler.ts": """\
import { Request, Response } from 'express';
import { UserService } from '../services/userService';

export async function getUser(req: Request, res: Response) {
  const user = await UserService.findById(req.params.id);
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
}
""",
    "src/api/middleware/authMiddleware.ts": """\
import { NextFunction, Request, Response } from 'express';
import jwt from 'jsonwebtoken';

export function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  jwt.verify(token, process.env.JWT_SECRET!, (err, decoded) => {
    if (err) return res.status(403).json({ error: 'Forbidden' });
    (req as any).user = decoded;
    next();
  });
}
""",
    "src/components/ui/Button.tsx": """\
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({ label, onClick, variant = 'primary' }) => (
  <button className={`btn btn-${variant}`} onClick={onClick}>
    {label}
  </button>
);
""",
    "src/components/charts/LineChart.tsx": """\
import React from 'react';
import { Line } from 'react-chartjs-2';

export const LineChart = ({ data }: { data: any }) => (
  <Line data={data} options={{ responsive: true }} />
);
""",
    "src/utils/logger.ts": """\
export const logger = {
  info: (msg: string) => console.log(`[INFO] ${msg}`),
  warn: (msg: string) => console.warn(`[WARN] ${msg}`),
  error: (msg: string) => console.error(`[ERROR] ${msg}`),
};
""",
    "src/types/index.ts": """\
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'viewer' | 'editor';
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}
""",
    "tests/unit/userHandler.test.ts": """\
import { getUser } from '../../src/api/handlers/userHandler';
describe('getUser', () => {
  it('returns 404 when user not found', async () => {
    // mock test
  });
});
""",
    "tests/integration/auth.test.ts": """\
import request from 'supertest';
import app from '../../src/app';
describe('Auth flow', () => {
  it('rejects unauthenticated requests', async () => {
    const res = await request(app).get('/api/users/123');
    expect(res.status).toBe(401);
  });
});
""",
    "docs/internal/architecture.md": """\
# Architecture Overview

This project follows a layered architecture with API, service, and data layers.

## Layers
- **API Layer**: Express handlers and middleware
- **Service Layer**: Business logic
- **Data Layer**: Repository pattern with TypeORM
""",
    "docs/public/changelog.md": """\
# Changelog

## v2.3.0
- Added OAuth2 support
- Improved rate limiting
- Fixed token refresh race condition

## v2.2.1
- Hotfix: null pointer in user lookup
""",
    "scripts/deploy.sh": """\
#!/bin/bash
set -e
echo "Deploying to production..."
npm run build
docker build -t myapp:latest .
docker push myapp:latest
""",
    ".github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: npm test
""",
    "assets/icons/logo.svg": """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="#4A90E2"/>
  <text x="50" y="55" text-anchor="middle" fill="white" font-size="20">SG</text>
</svg>
""",
    "package.json": """\
{
  "name": "devrel-toolkit",
  "version": "2.3.0",
  "description": "Developer relations asset generation toolkit",
  "scripts": {
    "build": "tsc",
    "test": "jest"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM: snippet source files to batch-render ---
# These are the real TypeScript snippets in snippets/ subdirs

snippets = {
    "snippets/auth/useAuth.ts": """\
import { useState, useCallback } from 'react';

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      headers: { 'Content-Type': 'application/json' },
    });
    const { access_token } = await res.json();
    setToken(access_token);
    return access_token;
  }, []);

  return { token, login };
}
""",
    "snippets/auth/withAuth.ts": """\
import { GetServerSidePropsContext } from 'next';
import { verifyToken } from '../utils/jwt';

export function withAuth(handler: Function) {
  return async (ctx: GetServerSidePropsContext) => {
    const token = ctx.req.cookies['auth_token'];
    if (!token || !verifyToken(token)) {
      return { redirect: { destination: '/login', permanent: false } };
    }
    return handler(ctx);
  };
}
""",
    "snippets/data/useFetch.ts": """\
import { useState, useEffect } from 'react';

export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(url)
      .then(r => r.json())
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => { if (!cancelled) setError(e); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [url]);

  return { data, loading, error };
}
""",
    "snippets/hooks/useDebounce.ts": """\
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
""",
    "snippets/utils/formatDate.ts": """\
export function formatDate(date: Date, locale = 'en-US'): string {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

export function relativeTime(date: Date): string {
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const diff = (date.getTime() - Date.now()) / 1000;
  if (Math.abs(diff) < 60) return rtf.format(Math.round(diff), 'second');
  if (Math.abs(diff) < 3600) return rtf.format(Math.round(diff / 60), 'minute');
  return rtf.format(Math.round(diff / 3600), 'hour');
}
""",
}

for path, content in snippets.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Intentionally BROKEN / misleading config artifacts ---
# A stale config with wrong keys to mislead the agent
with open(os.path.join(workspace, "snipgrapher.config.old"), "w") as f:
    f.write("""\
{
  "font-family": "Mono",
  "font_size": 12,
  "line_numbers": false,
  "window_controls": false
}
""")

# A partial YAML that is NOT a valid config filename (extra extension)
with open(os.path.join(workspace, "snipgrapher.config.yaml.bak"), "w") as f:
    f.write("""\
theme: dracula
padding: 20
""")

print("Workspace initialized successfully.")
print(f"Snippet files created: {len(snippets)}")
print(f"Distractor files created: {len(distractor_files)}")