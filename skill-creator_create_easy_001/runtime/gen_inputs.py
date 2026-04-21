#!/usr/bin/env python3
import os

# Create example markdown content for the skill to reference
with open('sample_doc.md', 'w') as f:
    f.write('''# Sample Document

## Introduction

This is a sample markdown document.

### Subsection

- Item 1
- Item 2

## Conclusion

End of document.
''')

print('Generated input files successfully')