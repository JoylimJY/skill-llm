import os

# This task requires no input files initially because the input is "run init script + develop artifact"
# But generate marker README.md so evaluation can find project root
readme_content = """
# Artifact Builder Task Input

This directory will contain the React project initialized by init-artifact.sh.
After running init-artifact.sh task-artifact, the user should develop the React app using @/components/ui components,
then run bundle-artifact.sh to produce bundle.html.
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)