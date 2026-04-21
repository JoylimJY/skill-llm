# Setup script to install dependencies

cd multi-route-artifact

# Initialize pnpm project
pnpm install react react-dom react-router-dom react-hook-form zod @hookform/resolvers

# Install dev dependencies compatible with artifacts-builder
pnpm add -D typescript vite tailwindcss@3.4.1 postcss autoprefixer @types/react @types/react-dom

# Initialize tailwindcss configuration (already generated in files)

# Install dummy shadcn/ui dependencies for completeness
pnpm add @radix-ui/react-accordion

# We do NOT run the dev server here as user will build and bundle themselves

# Return to workspace root
echo "Setup complete. You can now run 'pnpm dev' or 'bash scripts/bundle-artifact.sh' inside multi-route-artifact." 
