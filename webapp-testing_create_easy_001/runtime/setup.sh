# No extra tools needed beyond Docker image
# Just set strict permissions for playwright cache
mkdir -p ~/.cache/ms-playwright
chmod -R 777 ~/.cache/ms-playwright
