FROM node:20-bullseye-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install python-pptx -i https://pypi.tuna.tsinghua.edu.cn/simple

# Pre-install the skill dependencies in the known source location
RUN mkdir -p /root/.openclaw/workspace/office-to-md-v2/office-to-md

WORKDIR /root/.openclaw/workspace/office-to-md-v2/office-to-md

# Create package.json for the skill
RUN echo '{"name":"office-to-md","version":"2.0.0","description":"Office to Markdown converter","main":"openclaw-skill.js","dependencies":{"pdf-parse":"^1.1.1","mammoth":"^1.6.0","turndown":"^7.1.2","word-extractor":"^1.0.4"}}' > package.json

RUN npm install --registry https://registry.npmmirror.com

# Create the openclaw-skill.js
RUN cat > openclaw-skill.js << 'SKILLEOF'
#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

async function convertPdf(filePath) {
  const pdfParse = require('pdf-parse');
  const buffer = fs.readFileSync(filePath);
  const data = await pdfParse(buffer);
  return data.text;
}

async function convertDocx(filePath) {
  const mammoth = require('mammoth');
  const TurndownService = require('turndown');
  const result = await mammoth.convertToHtml({ path: filePath });
  const turndown = new TurndownService();
  return turndown.turndown(result.value);
}

async function convertDoc(filePath) {
  const WordExtractor = require('word-extractor');
  const extractor = new WordExtractor();
  const extracted = await extractor.extract(filePath);
  return extracted.getBody();
}

async function convertPptx(filePath) {
  const { execSync } = require('child_process');
  const tmpOut = filePath + '.pptx_text.txt';
  const pyScript = `
import sys
from pptx import Presentation
prs = Presentation(sys.argv[1])
lines = []
for slide in prs.slides:
    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip():
            lines.append(shape.text)
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write('\\n'.join(lines))
`;
  const pyFile = '/tmp/_pptx_convert.py';
  fs.writeFileSync(pyFile, pyScript);
  execSync(`python3 ${pyFile} "${filePath}" "${tmpOut}"`);
  const text = fs.readFileSync(tmpOut, 'utf-8');
  fs.unlinkSync(tmpOut);
  return text;
}

async function convertOfficeToMarkdown(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  let markdown = '';
  let fileType = '';

  try {
    if (ext === '.pdf') {
      fileType = 'pdf';
      const text = await convertPdf(filePath);
      markdown = text;
    } else if (ext === '.docx') {
      fileType = 'docx';
      markdown = await convertDocx(filePath);
    } else if (ext === '.doc') {
      fileType = 'doc';
      markdown = await convertDoc(filePath);
    } else if (ext === '.pptx') {
      fileType = 'pptx';
      markdown = await convertPptx(filePath);
    } else {
      return {
        success: false,
        error: `Unsupported file type: ${ext}. Supported: .pdf, .doc, .docx, .pptx`
      };
    }

    const outputPath = filePath.replace(/\.[^/.]+$/, '.md');
    fs.writeFileSync(outputPath, markdown, 'utf-8');

    const lines = markdown.split('\n').length;
    const characters = markdown.length;
    const words = markdown.split(/\s+/).filter(w => w.length > 0).length;

    return {
      success: true,
      outputPath,
      markdown,
      preview: markdown.substring(0, 200),
      fileType,
      message: `Converted to: ${outputPath}`,
      stats: { lines, characters, words }
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      stack: err.stack
    };
  }
}

module.exports = { convertOfficeToMarkdown };

// CLI mode
if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('Usage: node openclaw-skill.js <file>');
    process.exit(1);
  }
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    process.exit(1);
  }
  convertOfficeToMarkdown(path.resolve(filePath)).then(result => {
    if (result.success) {
      console.log(JSON.stringify(result));
      process.exit(0);
    } else {
      console.error(result.error);
      process.exit(1);
    }
  }).catch(err => {
    console.error(err.message);
    process.exit(1);
  });
}
SKILLEOF

WORKDIR /workspace