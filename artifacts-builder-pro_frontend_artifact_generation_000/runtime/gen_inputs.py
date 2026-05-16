import os
import stat
import textwrap

workspace = "/workspace"

# ─── 1. Create the skill scripts directory ───────────────────────────────────
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# ── init-artifact.sh ──────────────────────────────────────────────────────────
init_script = r"""#!/usr/bin/env bash
set -e

PROJECT_NAME="${1:?Usage: init-artifact.sh <project-name>}"
echo "🚀 Initializing artifact project: $PROJECT_NAME"

# Detect Node version and pick compatible Vite
NODE_MAJOR=$(node -e "console.log(process.versions.node.split('.')[0])")
if [ "$NODE_MAJOR" -ge 18 ]; then
  VITE_VERSION="@latest"
else
  VITE_VERSION="@4"
fi

npm create vite@latest "$PROJECT_NAME" -- --template react-ts --yes 2>/dev/null || \
  npx --yes create-vite@latest "$PROJECT_NAME" --template react-ts

cd "$PROJECT_NAME"

# Install Tailwind CSS 3.4.1 (pinned)
npm install -D tailwindcss@3.4.1 postcss autoprefixer

# Initialize Tailwind
npx tailwindcss init -p

# Configure tailwind.config.js
cat > tailwind.config.js << 'TWEOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
TWEOF

# Install shadcn/ui dependencies
npm install class-variance-authority clsx tailwind-merge lucide-react tailwindcss-animate
npm install @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-tabs \
  @radix-ui/react-label @radix-ui/react-select @radix-ui/react-separator \
  @radix-ui/react-popover @radix-ui/react-toast @radix-ui/react-tooltip \
  @radix-ui/react-accordion @radix-ui/react-alert-dialog @radix-ui/react-avatar \
  @radix-ui/react-checkbox @radix-ui/react-collapsible @radix-ui/react-context-menu \
  @radix-ui/react-dropdown-menu @radix-ui/react-hover-card @radix-ui/react-menubar \
  @radix-ui/react-navigation-menu @radix-ui/react-progress @radix-ui/react-radio-group \
  @radix-ui/react-scroll-area @radix-ui/react-slider @radix-ui/react-switch \
  @radix-ui/react-toggle @radix-ui/react-toggle-group

# Configure path aliases in tsconfig.json
node -e "
const fs = require('fs');
const tsconfig = JSON.parse(fs.readFileSync('tsconfig.json','utf8'));
tsconfig.compilerOptions = tsconfig.compilerOptions || {};
tsconfig.compilerOptions.baseUrl = '.';
tsconfig.compilerOptions.paths = { '@/*': ['./src/*'] };
fs.writeFileSync('tsconfig.json', JSON.stringify(tsconfig, null, 2));
"

# Configure vite.config.ts for path alias
cat > vite.config.ts << 'VEOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
VEOF

npm install -D @types/node

# Create src/lib/utils.ts
mkdir -p src/lib
cat > src/lib/utils.ts << 'UEOF'
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
UEOF

# Create src/index.css with CSS variables
cat > src/index.css << 'CSSEOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }
}

@layer base {
  * { @apply border-border; }
  body { @apply bg-background text-foreground; }
}
CSSEOF

# Create shadcn/ui Button component
mkdir -p src/components/ui
cat > src/components/ui/button.tsx << 'BEOF'
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
BEOF

# Create shadcn/ui Card component
cat > src/components/ui/card.tsx << 'CEOF'
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />
  )
)
CardTitle.displayName = "CardTitle"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
)
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardContent }
CEOF

# Create shadcn/ui Tabs component
cat > src/components/ui/tabs.tsx << 'TEOF'
import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"
import { cn } from "@/lib/utils"

const Tabs = TabsPrimitive.Root
const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn("inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground", className)}
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn("inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm", className)}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn("mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2", className)}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
TEOF

# Create shadcn/ui Badge component
cat > src/components/ui/badge.tsx << 'BGEOF'
import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
BGEOF

# Create .parcelrc
cat > .parcelrc << 'PEOF'
{
  "extends": "@parcel/config-default",
  "resolvers": ["parcel-resolver-tspaths", "..."]
}
PEOF

echo "✅ Project '$PROJECT_NAME' initialized successfully!"
echo "   cd $PROJECT_NAME && start developing"
"""

bundle_script = r"""#!/usr/bin/env bash
set -e

PROJECT_DIR="$(pwd)"

echo "📦 Bundling artifact to single HTML file..."

# Check for index.html
if [ ! -f "$PROJECT_DIR/index.html" ]; then
  echo "❌ Error: index.html not found in $PROJECT_DIR"
  exit 1
fi

# Install bundling dependencies
npm install -D parcel@2 @parcel/config-default parcel-resolver-tspaths
npm install -g html-inline 2>/dev/null || npx html-inline --version 2>/dev/null || npm install html-inline

# Ensure .parcelrc exists
if [ ! -f ".parcelrc" ]; then
cat > .parcelrc << 'PEOF'
{
  "extends": "@parcel/config-default",
  "resolvers": ["parcel-resolver-tspaths", "..."]
}
PEOF
fi

# Clean previous build
rm -rf dist .parcel-cache

# Build with Parcel (no source maps)
npx parcel build index.html --no-source-maps --dist-dir dist

# Inline all assets into single HTML
if command -v html-inline &>/dev/null; then
  html-inline dist/index.html > bundle.html
else
  npx html-inline dist/index.html > bundle.html
fi

echo "✅ bundle.html created successfully!"
echo "   Share bundle.html in Claude conversation as artifact."
"""

with open(os.path.join(scripts_dir, "init-artifact.sh"), "w") as f:
    f.write(init_script)

with open(os.path.join(scripts_dir, "bundle-artifact.sh"), "w") as f:
    f.write(bundle_script)

os.chmod(os.path.join(scripts_dir, "init-artifact.sh"), 0o755)
os.chmod(os.path.join(scripts_dir, "bundle-artifact.sh"), 0o755)

# ─── 2. Create distractor files ──────────────────────────────────────────────
# Simulate a messy monorepo with unrelated projects and old artifacts

distractor_dirs = [
    "old-projects/vessel-tracker-v1/src",
    "old-projects/vessel-tracker-v1/dist",
    "old-projects/cargo-monitor-legacy/components",
    "old-projects/cargo-monitor-legacy/styles",
    "archives/2022-dashboards/port-alpha",
    "archives/2022-dashboards/port-beta/assets",
    "shared-assets/icons",
    "shared-assets/fonts",
    "docs/api-specs",
    "ci-configs",
    "database/migrations",
    "database/seeds",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "old-projects/vessel-tracker-v1/src/index.js": "// Legacy vessel tracker\nconsole.log('old tracker');",
    "old-projects/vessel-tracker-v1/src/styles.css": "body { font-family: Inter, sans-serif; background: linear-gradient(135deg, #7c3aed, #a855f7); }",
    "old-projects/vessel-tracker-v1/dist/bundle.js": "!function(){console.log('old bundle')}();",
    "old-projects/vessel-tracker-v1/package.json": '{"name":"vessel-tracker-v1","version":"0.1.0","dependencies":{"react":"17.0.2"}}',
    "old-projects/cargo-monitor-legacy/components/Table.jsx": "export default function Table() { return <table><tr><td>Cargo</td></tr></table>; }",
    "old-projects/cargo-monitor-legacy/styles/main.css": ".container { display: flex; justify-content: center; background: #7c3aed; border-radius: 12px; }",
    "old-projects/cargo-monitor-legacy/package.json": '{"name":"cargo-monitor-legacy","version":"0.0.5"}',
    "archives/2022-dashboards/port-alpha/index.html": "<html><body><h1>Port Alpha Dashboard</h1></body></html>",
    "archives/2022-dashboards/port-beta/assets/logo.txt": "PORT BETA LOGO PLACEHOLDER",
    "archives/2022-dashboards/port-beta/webpack.config.js": "module.exports = { entry: './src/index.js', output: { filename: 'bundle.js' } };",
    "shared-assets/icons/anchor.svg": "<svg viewBox='0 0 24 24'><path d='M12 2a4 4 0 0 1 4 4'/></svg>",
    "shared-assets/fonts/maritime-mono.txt": "Font placeholder - not a real font file",
    "docs/api-specs/vessel-api-v2.yaml": "openapi: 3.0.0\ninfo:\n  title: Vessel API\n  version: 2.0.0\npaths:\n  /vessels:\n    get:\n      summary: List vessels",
    "docs/api-specs/cargo-api-v1.json": '{"openapi":"3.0.0","info":{"title":"Cargo API","version":"1.0.0"}}',
    "ci-configs/.gitlab-ci.yml": "stages:\n  - build\n  - test\nbuild:\n  script:\n    - npm run build",
    "ci-configs/Makefile": "build:\n\tnpm run build\ntest:\n\tnpm test",
    "database/migrations/001_create_vessels.sql": "CREATE TABLE vessels (id SERIAL PRIMARY KEY, name VARCHAR(255), status VARCHAR(50));",
    "database/migrations/002_create_cargo.sql": "CREATE TABLE cargo (id SERIAL PRIMARY KEY, vessel_id INT, weight DECIMAL, destination VARCHAR(255));",
    "database/seeds/seed_vessels.json": '[{"name":"MV Atlantic Star","status":"docked"},{"name":"SS Pacific Crown","status":"at-sea"}]',
    "CHANGELOG.md": "# Changelog\n## v2.1.0\n- Added new vessel tracking features\n## v2.0.0\n- Complete rewrite",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ─── 3. Create the business requirements spec ─────────────────────────────────
requirements = """# Port Operations Dashboard — Product Requirements

## Project Code Name: harbor-ops

## Business Context
Our port operations team needs a real-time cargo dashboard to replace the old spreadsheet-based
system. The dashboard will be used by port controllers on desktop monitors.

## Required Features

### 1. Summary Statistics Bar
At the top, show four KPI cards:
- Total Vessels in Port: 12
- Cargo Awaiting Clearance: 847 TEUs
- Vessels Departed Today: 5
- Average Dwell Time: 3.2 days

### 2. Vessel Status Table (filterable by tabs)
Three tabs: ALL | IN PORT | DEPARTED

Table columns: Vessel Name | Flag | Cargo Type | TEUs | Berth | Status | ETA/ETD

Hardcode at least 6 sample vessels with mixed statuses.
Use colored status badges (green=In Port, yellow=Clearing, red=Delayed, gray=Departed).

### 3. Cargo Manifest Panel
A separate section showing a simplified cargo breakdown by category:
- Containers, Bulk, Liquid, Vehicles
Show counts and a visual indicator (e.g. a progress bar or colored bar)

## Design Notes
- Must look professional, suitable for a control room environment
- Dark-themed or neutral — NOT a consumer app aesthetic
- Absolutely no purple color scheme
- Should feel data-dense, not spacious/airy
"""

with open(os.path.join(workspace, "harbor-ops-requirements.md"), "w") as f:
    f.write(requirements)

print("✅ Workspace generated successfully.")
print(f"   Distractor files: {len(distractor_files)}")
print(f"   Scripts: scripts/init-artifact.sh, scripts/bundle-artifact.sh")