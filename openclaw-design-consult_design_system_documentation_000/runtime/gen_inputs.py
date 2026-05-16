import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- README.md (product context) ---
(workspace / "README.md").write_text("""# RiskLens Pro

RiskLens Pro is a real-time portfolio risk analytics dashboard for institutional investors and hedge fund managers.

## What it does
- Aggregates multi-asset portfolio positions (equities, FX, derivatives)
- Computes VaR, CVaR, drawdown, and factor exposure in real-time
- Provides compliance breach alerting and regulatory reporting export
- Supports multi-currency, multi-custodian portfolio reconciliation

## Target Users
- Portfolio managers at mid-to-large asset management firms
- Risk officers and compliance teams
- Quantitative analysts

## Tech Stack
- Frontend: React + TypeScript
- Charts: D3.js + custom canvas rendering
- Backend: FastAPI (Python)
- Data: WebSocket streaming from prime broker feeds

## Status
Early beta. Currently onboarding first 3 institutional clients.
""")

# --- package.json ---
(workspace / "package.json").write_text(json.dumps({
    "name": "risklens-pro",
    "version": "0.3.1",
    "description": "Institutional portfolio risk analytics dashboard",
    "scripts": {
        "dev": "next dev",
        "build": "next build",
        "start": "next start"
    },
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "next": "^14.0.0",
        "d3": "^7.8.5",
        "typescript": "^5.2.0",
        "@tanstack/react-query": "^5.0.0",
        "recharts": "^2.8.0",
        "zustand": "^4.4.0",
        "tailwindcss": "^3.3.0"
    },
    "devDependencies": {
        "@types/react": "^18.2.0",
        "@types/d3": "^7.4.0"
    }
}, indent=2))

# --- Directory structure ---
dirs = [
    "src/components/charts",
    "src/components/tables",
    "src/components/alerts",
    "src/pages/dashboard",
    "src/pages/positions",
    "src/pages/reports",
    "src/hooks",
    "src/utils",
    "src/types",
    "src/styles",
    "src/api",
    "app/layout",
    "app/dashboard",
    "public/icons",
    "docs",
    ".context",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor source files ---
(workspace / "src/components/charts/VaRChart.tsx").write_text("""import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export const VaRChart = ({ data }: { data: any[] }) => (
  <LineChart width={800} height={300} data={data}>
    <Line type="monotone" dataKey="var95" stroke="#2563eb" />
    <Line type="monotone" dataKey="var99" stroke="#dc2626" />
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
  </LineChart>
);
""")

(workspace / "src/components/tables/PositionsTable.tsx").write_text("""import React from 'react';

interface Position {
  ticker: string;
  quantity: number;
  price: number;
  pnl: number;
  currency: string;
}

export const PositionsTable = ({ positions }: { positions: Position[] }) => {
  return (
    <table className="w-full text-sm font-mono">
      <thead>
        <tr>
          <th>Ticker</th><th>Qty</th><th>Price</th><th>P&L</th><th>CCY</th>
        </tr>
      </thead>
      <tbody>
        {positions.map(p => (
          <tr key={p.ticker}>
            <td>{p.ticker}</td><td>{p.quantity}</td>
            <td>{p.price.toFixed(4)}</td><td>{p.pnl.toFixed(2)}</td>
            <td>{p.currency}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
""")

(workspace / "src/components/alerts/BreachAlert.tsx").write_text("""import React from 'react';

type Severity = 'critical' | 'warning' | 'info';

export const BreachAlert = ({ message, severity }: { message: string; severity: Severity }) => {
  const colors = {
    critical: 'bg-red-900 border-red-500',
    warning: 'bg-amber-900 border-amber-400',
    info: 'bg-blue-900 border-blue-400'
  };
  return (
    <div className={`border-l-4 p-3 font-mono text-xs ${colors[severity]}`}>
      {message}
    </div>
  );
};
""")

(workspace / "src/pages/dashboard/index.tsx").write_text("""export { default } from './Dashboard';
""")

(workspace / "src/hooks/usePortfolioData.ts").write_text("""import { useQuery } from '@tanstack/react-query';

export function usePortfolioData(portfolioId: string) {
  return useQuery({
    queryKey: ['portfolio', portfolioId],
    queryFn: async () => {
      const res = await fetch(\`/api/portfolio/\${portfolioId}\`);
      return res.json();
    },
    refetchInterval: 5000,
  });
}
""")

(workspace / "src/utils/formatCurrency.ts").write_text("""export function formatCurrency(value: number, currency = 'USD', decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}
""")

(workspace / "src/types/portfolio.ts").write_text("""export interface Portfolio {
  id: string;
  name: string;
  baseCurrency: string;
  totalNav: number;
  var95: number;
  var99: number;
  positions: Position[];
}

export interface Position {
  id: string;
  ticker: string;
  assetClass: 'equity' | 'fx' | 'derivative' | 'fixed_income';
  quantity: number;
  marketValue: number;
  pnlDaily: number;
  pnlMtd: number;
  currency: string;
}
""")

(workspace / "src/styles/globals.css").write_text("""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #1e3a5f;
  --color-accent: #00d4aa;
  --font-mono: 'JetBrains Mono', monospace;
}
""")

(workspace / "src/api/portfolioService.ts").write_text("""const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchPortfolio(id: string) {
  const response = await fetch(\`\${BASE_URL}/portfolio/\${id}\`);
  if (!response.ok) throw new Error('Failed to fetch portfolio');
  return response.json();
}

export async function fetchVaRHistory(id: string, days = 30) {
  const response = await fetch(\`\${BASE_URL}/portfolio/\${id}/var?days=\${days}\`);
  return response.json();
}
""")

(workspace / "docs/architecture.md").write_text("""# RiskLens Architecture

## Data Flow
WebSocket Feed → Normalization Layer → Risk Engine → React Dashboard

## Risk Calculations
- VaR computed using Historical Simulation (1-day, 95%/99% confidence)
- CVaR = Expected Shortfall beyond VaR threshold
- Factor exposures: Barra-style 4-factor model

## Compliance
SOC 2 Type II in progress. GDPR compliant data handling.
""")

(workspace / "docs/api-spec.md").write_text("""# API Specification

## Endpoints
GET /portfolio/{id} — full portfolio snapshot
GET /portfolio/{id}/var — VaR time series
POST /portfolio/{id}/rebalance — trigger rebalance simulation
WS /stream/{id} — real-time position stream
""")

(workspace / "app/layout/RootLayout.tsx").write_text("""import React from 'react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
""")

(workspace / "public/icons/.gitkeep").write_text("")

# --- CLAUDE.md already exists with some content but NO design section ---
(workspace / "CLAUDE.md").write_text("""# CLAUDE.md — RiskLens Pro Development Guide

## Project Overview
RiskLens Pro is a B2B institutional fintech product. Always prioritize data accuracy and performance.

## Coding Standards
- TypeScript strict mode enabled. No `any` types.
- All async operations must handle errors explicitly.
- Use `zustand` for global state, `react-query` for server state.
- Component files: PascalCase. Utility files: camelCase.

## Testing
- Unit tests: Vitest
- E2E tests: Playwright
- Coverage threshold: 80%

## Performance
- Bundle size budget: 300kb gzipped
- Core Web Vitals targets: LCP < 2.5s, FID < 100ms, CLS < 0.1

## Data Handling
- Never log PII or portfolio identifiers in client-side code.
- All monetary values stored as integers (basis points or cents).
""")

# Intentionally NO DESIGN.md exists — agent must create it
print("Workspace setup complete.")
print(f"Files created in: {workspace}")
print("No DESIGN.md present — agent must generate it.")
print("CLAUDE.md exists without design section — agent must append to it.")