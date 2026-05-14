FROM node:18-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install openclaw CLI globally via npm
RUN npm install -g openclaw 2>/dev/null || true

# Create the skills directory structure for the markdown-validator skill
RUN mkdir -p /skills/markdown-validator

# Write the markdown-validator index.js skill
RUN cat > /skills/markdown-validator/index.js << 'SKILLEOF'
const fs = require('fs');
const path = require('path');

function findMarkdownFiles(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const stat = fs.statSync(dir);
  if (stat.isFile()) {
    if (dir.endsWith('.md')) return [dir];
    return [];
  }
  const list = fs.readdirSync(dir);
  for (const file of list) {
    const fullPath = path.join(dir, file);
    const fileStat = fs.statSync(fullPath);
    if (fileStat.isDirectory()) {
      results = results.concat(findMarkdownFiles(fullPath));
    } else if (file.endsWith('.md')) {
      results.push(fullPath);
    }
  }
  return results;
}

function extractLinks(content) {
  const linkRegex = /\[([^\]]*)\]\(([^)]+)\)/g;
  const links = [];
  let match;
  const lines = content.split('\n');
  let lineIndex = 0;
  let charCount = 0;
  while ((match = linkRegex.exec(content)) !== null) {
    const pos = match.index;
    while (lineIndex < lines.length - 1 && charCount + lines[lineIndex].length + 1 <= pos) {
      charCount += lines[lineIndex].length + 1;
      lineIndex++;
    }
    links.push({ text: match[1], url: match[2], line: lineIndex + 1 });
  }
  return links;
}

function validateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const links = extractLinks(content);
  const brokenLinks = [];
  const dir = path.dirname(filePath);

  for (const link of links) {
    const url = link.url;
    // Ignore external URLs
    if (url.startsWith('http://') || url.startsWith('https://')) continue;
    // Ignore same-file anchors
    if (url.startsWith('#')) continue;
    // Resolve relative path
    const resolved = path.resolve(dir, url.split('#')[0]);
    if (!fs.existsSync(resolved)) {
      brokenLinks.push({ text: link.text, url: link.url, line: link.line });
    }
  }

  return {
    file: filePath,
    valid: brokenLinks.length === 0,
    brokenLinks
  };
}

const target = process.argv[2] || '.';
const files = findMarkdownFiles(path.resolve(target));
const report = files.map(validateFile);
console.log(JSON.stringify(report, null, 2));
SKILLEOF

# Create a wrapper for openclaw if not installed, that simulates "openclaw exec node <script> <args>"
RUN which openclaw || (cat > /usr/local/bin/openclaw << 'CLAWEOF'
#!/bin/bash
if [ "$1" = "exec" ]; then
  shift
  exec "$@"
fi
exec "$@"
CLAWEOF
chmod +x /usr/local/bin/openclaw)

WORKDIR /workspace