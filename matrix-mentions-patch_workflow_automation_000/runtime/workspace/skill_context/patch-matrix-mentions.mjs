#!/usr/bin/env node
/**
 * Matrix Mentions Patch - OpenClaw Matrix Channel Plugin
 * 
 * This script patches OpenClaw's Matrix plugin to properly handle @mentions.
 * 
 * What it does:
 * 1. Locates the auth-profiles-*.js file in OpenClaw's dist/
 * 2. Creates a backup (.bak) before modifying
 * 3. Patches buildTextContent() to attach m.mentions to outbound messages
 * 4. Patches applyMatrixFormatting() to wrap mentions in HTML data-mention spans
 * 
 * Re-run after: openclaw update (replaces compiled JS)
 * Restore: cp auth-profiles-*.js.bak auth-profiles-*.js
 */

import { readFileSync, writeFileSync, cpSync } from 'fs';
import { execSync } from 'child_process';

function findOpenClawDist() {
  const candidates = [
    '/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist',
    execSync('npm root -g').toString().trim() + '/openclaw/dist'
  ];

  for (const dir of candidates) {
    try {
      const files = execSync(`ls ${dir}/auth-profiles-*.js 2>/dev/null`, { encoding: 'utf8' }).trim().split('\n');
      if (files.length > 0 && files[0]) {
        return files[0];
      }
    } catch (e) {
      // continue searching
    }
  }
  throw new Error('Could not find auth-profiles-*.js in OpenClaw dist/');
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|\\]/g, (c) => '\\' + c);
}

function patchFile(filePath) {
  let content = readFileSync(filePath, 'utf8');
  const originalContent = content;

  if (content.includes('extractMentionsFromText')) {
    console.log('Already patched');
    return;
  }

  const helper = `
function extractMentionsFromText(text) {
  const mentions = [];
  const mentionRegex = /@(?:([a-zA-Z0-9._=-]+):([a-zA-Z0-9.-]+)|([a-zA-Z0-9._-]+))/g;
  let match;
  while ((match = mentionRegex.exec(text)) !== null) {
    if (match[1] && match[2]) {
      mentions.push('@' + match[1] + ':' + match[2]);
    } else if (match[3]) {
      mentions.push('@' + match[3]);
    }
  }
  return [...new Set(mentions)];
}`;

  content = content.replace(
    /(function buildTextContent\([^)]*\)\s*\{)/,
    helper + '\n\n$1'
  );

  // Patch buildTextContent to add m.mentions
  const oldBuildText = 'function buildTextContent(text, formatted, opts) { const body = formatted ? formatted.body : text; const formattedBody = formatted ? formatted.formatted_body : null; return { msgtype: \'m.text\', body: formatted ? body : text, formatted_body: formattedBody, format: formatted ? \'org.matrix.custom.html\' : undefined';

  const newBuildText = 'function buildTextContent(text, formatted, opts) { const mentions = extractMentionsFromText(text); const body = formatted ? formatted.body : text; const formattedBody = formatted ? formatted.formatted_body : null; const result = { msgtype: \'m.text\', body: formatted ? body : text, formatted_body: formattedBody, format: formatted ? \'org.matrix.custom.html\' : undefined';

  content = content.replace(oldBuildText, newBuildText);

  // Add m.mentions before return
  if (!content.includes('m.mentions')) {
    content = content.replace(
      /(format: formatted \? 'org\.matrix\.custom\.html' : undefined,?)/,
      '$1\n    mentions: mentions.length > 0 ? { user_ids: mentions } : undefined'
    );
  }

  // Patch applyMatrixFormatting
  const oldApply = "function applyMatrixFormatting(text) { if (!text) return null; let formatted = text; const mentionRegex = /@(?:([a-zA-Z0-9._=-]+):([a-zA-Z0-9.-]+)|([a-zA-Z0-9._-]+))/g; let match; while ((match = mentionRegex.exec(text)) !== null) { const userId = match[1] && match[2] ? '@' + match[1] + ':' + match[2] : '@' + match[3]; formatted = formatted.replace(userId, '<span data-mention=\"user\" data-user-id=\"' + userId + '\">' + userId + '</span>'); } return { body: text, formatted_body: formatted }; }";

  const newApply = `function applyMatrixFormatting(text) {
  if (!text) return null;
  const mentions = extractMentionsFromText(text);
  let formatted = text;
  mentions.forEach(m => {
    const escaped = escapeRegex(m);
    const regex = new RegExp(escaped, 'g');
    formatted = formatted.replace(regex, '<span data-mention="user" data-user-id="' + m + '">' + m + '</span>');
  });
  return { body: text, formatted_body: formatted };
}`;

  content = content.replace(oldApply, newApply);

  if (content === originalContent) {
    console.log('Could not find expected patterns - file may have changed');
    return;
  }

  const bakPath = filePath + '.bak';
  cpSync(filePath, bakPath);
  console.log('Backup created: ' + bakPath);

  writeFileSync(filePath, content);
  console.log('Patched: ' + filePath);
}

try {
  console.log('Matrix Mentions Patch\n');
  const filePath = findOpenClawDist();
  console.log('Found:', filePath);
  patchFile(filePath);
  console.log('\nPatch applied! Restart: openclaw gateway restart');
} catch (e) {
  console.error('Error:', e.message);
  process.exit(1);
}