set -e

# Make sure the shadcn-components.tar.gz is in the workspace root
if [ ! -f shadcn-components.tar.gz ]; then
  echo "Error: shadcn-components.tar.gz not found in workspace root"
  exit 1
fi

# Initialize the artifact project using the official init script
bash scripts/init-artifact.sh my-artifact

cd my-artifact

# Bundle the artifact to single HTML
bash ../scripts/bundle-artifact.sh

cd ..

# Move the generated bundle.html to workspace root for evaluation
mv my-artifact/bundle.html ./bundle.html
