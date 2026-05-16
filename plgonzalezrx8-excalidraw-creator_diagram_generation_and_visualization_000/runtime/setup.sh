#!/bin/bash
set -e

# Setup the excalidraw skill directory
SKILL_DIR="/opt/excalidraw-creator"
mkdir -p "$SKILL_DIR/scripts"

# Install Node.js dependencies for the renderer
cd "$SKILL_DIR/scripts"

cat > package.json << 'PKGJSON'
{
  "name": "excalidraw-renderer",
  "version": "1.0.0",
  "description": "Excalidraw renderer for diagram generation",
  "main": "render.js",
  "dependencies": {
    "canvas": "^2.11.2",
    "roughjs": "^4.6.6"
  }
}
PKGJSON

npm install --prefer-offline 2>/dev/null || npm install

# Write the render.js script that parses the excalidraw JSON and renders to PNG
cat > render.js << 'RENDERJS'
#!/usr/bin/env node
/**
 * Excalidraw JSON to PNG renderer
 * Usage: node render.js input.excalidraw output.png
 */

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');
const rough = require('roughjs');

const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile || !outputFile) {
  console.error('Usage: node render.js <input.excalidraw> <output.png>');
  process.exit(1);
}

// Read the excalidraw JSON
let data;
try {
  const raw = fs.readFileSync(inputFile, 'utf-8');
  data = JSON.parse(raw);
} catch (e) {
  console.error('Failed to read/parse input file:', e.message);
  process.exit(1);
}

const elements = data.elements || [];

// Validate: must have at least one element
if (elements.length === 0) {
  console.error('No elements found in excalidraw file');
  process.exit(1);
}

// Validate required fields
const validTypes = ['rectangle', 'ellipse', 'diamond', 'arrow', 'line', 'text'];
let hasInvalidType = false;
let hasArrowWithCoords = false;
let missingIds = false;

const elementMap = {};
for (const el of elements) {
  if (!el.id) {
    missingIds = true;
  }
  if (el.id) elementMap[el.id] = el;
  if (el.type && !validTypes.includes(el.type)) {
    hasInvalidType = true;
    console.warn(`Warning: unknown element type '${el.type}'`);
  }
}

// Process arrow bindings: resolve from/to references
for (const el of elements) {
  if (el.type === 'arrow') {
    if (el.from && el.to) {
      const src = elementMap[el.from];
      const dst = elementMap[el.to];
      if (!src) console.warn(`Arrow ${el.id}: source '${el.from}' not found`);
      if (!dst) console.warn(`Arrow ${el.id}: target '${el.to}' not found`);
      
      if (src && dst && !el.absolutePoints) {
        // Auto-calculate edge intersection (simplified: center-to-center)
        const srcCx = src.x + (src.width || 0) / 2;
        const srcCy = src.y + (src.height || 0) / 2;
        const dstCx = dst.x + (dst.width || 0) / 2;
        const dstCy = dst.y + (dst.height || 0) / 2;
        el._resolvedPoints = [[srcCx, srcCy], [dstCx, dstCy]];
      } else if (el.absolutePoints && el.points) {
        el._resolvedPoints = el.points;
      }
    }
  }
}

// Determine canvas bounds
let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
for (const el of elements) {
  if (el.type === 'text' || el.type === 'arrow') continue;
  if (el.x !== undefined) {
    minX = Math.min(minX, el.x);
    minY = Math.min(minY, el.y);
    maxX = Math.max(maxX, el.x + (el.width || 100));
    maxY = Math.max(maxY, el.y + (el.height || 60));
  }
}
if (!isFinite(minX)) { minX = 0; minY = 0; maxX = 800; maxY = 600; }

const PADDING = 60;
const canvasWidth = Math.max(800, maxX - minX + PADDING * 2);
const canvasHeight = Math.max(600, maxY - minY + PADDING * 2);
const offsetX = -minX + PADDING;
const offsetY = -minY + PADDING;

const canvas = createCanvas(canvasWidth, canvasHeight);
const ctx = canvas.getContext('2d');

// White background
ctx.fillStyle = '#ffffff';
ctx.fillRect(0, 0, canvasWidth, canvasHeight);

// Setup rough.js
const rc = rough.canvas(canvas);

function hexToRgba(hex, alpha) {
  if (!hex || hex === 'transparent' || hex === 'none') return null;
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha||1})`;
}

function getRoughOptions(el) {
  return {
    stroke: el.strokeColor || '#1e1e1e',
    strokeWidth: el.strokeWidth || 2,
    roughness: el.roughness !== undefined ? el.roughness : 1,
    fill: (el.backgroundColor && el.backgroundColor !== 'transparent') ? el.backgroundColor : undefined,
    fillStyle: el.fillStyle || 'hachure',
    strokeLineDash: el.strokeStyle === 'dashed' ? [8, 4] : undefined,
  };
}

// Draw elements
for (const el of elements) {
  const x = (el.x || 0) + offsetX;
  const y = (el.y || 0) + offsetY;
  const w = el.width || 160;
  const h = el.height || 60;
  const opts = getRoughOptions(el);

  switch (el.type) {
    case 'rectangle':
      rc.rectangle(x, y, w, h, opts);
      break;
    case 'ellipse':
      rc.ellipse(x + w/2, y + h/2, w, h, opts);
      break;
    case 'diamond': {
      const cx = x + w/2, cy = y + h/2;
      rc.polygon([[cx, y], [x+w, cy], [cx, y+h], [x, cy]], opts);
      break;
    }
    case 'arrow':
    case 'line': {
      const pts = el._resolvedPoints || el.points;
      if (pts && pts.length >= 2) {
        // Draw path
        const lineOpts = { ...opts, fill: undefined };
        for (let i = 0; i < pts.length - 1; i++) {
          const ax = pts[i][0] + (el.absolutePoints ? offsetX : 0);
          const ay = pts[i][1] + (el.absolutePoints ? offsetY : 0);
          const bx = pts[i+1][0] + (el.absolutePoints ? offsetX : 0);
          const by = pts[i+1][1] + (el.absolutePoints ? offsetY : 0);
          rc.line(ax, ay, bx, by, lineOpts);
        }
        // Arrowhead at end
        if (el.type === 'arrow') {
          const last = pts[pts.length - 1];
          const prev = pts[pts.length - 2];
          const lx = last[0] + (el.absolutePoints ? offsetX : 0);
          const ly = last[1] + (el.absolutePoints ? offsetY : 0);
          const px = prev[0] + (el.absolutePoints ? offsetX : 0);
          const py = prev[1] + (el.absolutePoints ? offsetY : 0);
          const angle = Math.atan2(ly - py, lx - px);
          const headLen = 12;
          ctx.beginPath();
          ctx.strokeStyle = el.strokeColor || '#1e1e1e';
          ctx.lineWidth = el.strokeWidth || 2;
          ctx.moveTo(lx, ly);
          ctx.lineTo(lx - headLen * Math.cos(angle - 0.4), ly - headLen * Math.sin(angle - 0.4));
          ctx.moveTo(lx, ly);
          ctx.lineTo(lx - headLen * Math.cos(angle + 0.4), ly - headLen * Math.sin(angle + 0.4));
          ctx.stroke();
        }
      } else if (el.type === 'arrow' && el._resolvedPoints) {
        // Already handled
      }
      break;
    }
    case 'text': {
      const fontSize = el.fontSize || 16;
      const families = {1: 'serif', 2: 'sans-serif', 3: 'monospace'};
      const family = families[el.fontFamily] || 'serif';
      ctx.font = `${fontSize}px ${family}`;
      ctx.fillStyle = el.strokeColor || '#1e1e1e';
      ctx.textAlign = el.textAlign || 'left';
      const lines = (el.text || '').split('\n');
      lines.forEach((line, i) => {
        ctx.fillText(line, x, y + fontSize + i * (fontSize + 4));
      });
      break;
    }
  }
}

// Write PNG
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync(outputFile, buffer);
console.log(`Rendered to ${outputFile} (${canvasWidth}x${canvasHeight})`);

// Validate and report
const issues = [];
if (missingIds) issues.push('WARNING: Some elements are missing id fields');
if (hasInvalidType) issues.push('WARNING: Some unknown element types found');

if (issues.length > 0) {
  console.warn(issues.join('\n'));
}
RENDERJS

chmod +x /opt/excalidraw-creator/scripts/render.js

# Export SKILL_DIR for the agent
echo "export SKILL_DIR=/opt/excalidraw-creator" >> /etc/environment
echo "SKILL_DIR=/opt/excalidraw-creator" >> /etc/profile.d/skill.sh
chmod +x /etc/profile.d/skill.sh

# Also set for current session
export SKILL_DIR=/opt/excalidraw-creator

echo "Setup complete. Skill directory: $SKILL_DIR"
echo "Renderer available at: $SKILL_DIR/scripts/render.js"
echo "Test: node $SKILL_DIR/scripts/render.js --help 2>/dev/null || echo 'Renderer ready'"