# No input files needed - task is to create from scratch
# But we create a marker file to confirm setup
import os
os.makedirs('workspace', exist_ok=True)
with open('workspace/task_ready.txt', 'w') as f:
    f.write('Task: Create climate_change.pptx using PptxGenJS\n')
print('Setup complete.')
