#!/bin/bash
set -e

# Install dependencies globally if missing
command -v pnpm >/dev/null 2>&1 || npm install -g pnpm

# Install utilities needed for build and evaluation
pnpm add -D parcel @parcel/config-default parcel-resolver-tspaths html-inline react react-dom react-router-dom react-hook-form zod tailwindcss@3.4.1 postcss autoprefixer next-themes react-resizable-panels @radix-ui/react-accordion sonner lucide-react class-variance-authority clsx tailwind-merge date-fns react-day-picker

# This environment is ready to run the init and bundle scripts
