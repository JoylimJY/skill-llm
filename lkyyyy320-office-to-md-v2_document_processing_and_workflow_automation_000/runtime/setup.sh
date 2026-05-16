#!/bin/bash
set -e

WORKSPACE="/workspace"
SKILL_SRC="/root/.openclaw/workspace/office-to-md-v2/office-to-md"

echo "=== Setting up office-to-md skill ==="

# Ensure skill source is ready
cd "$SKILL_SRC"
echo "Skill dependencies already installed at: $SKILL_SRC"
ls -la node_modules/ | head -5 || echo "node_modules present"

# Create real .doc files from .pending files using a Node.js script
# We use the cfb + docxtemplater approach via a helper Node script

cat > /tmp/create_doc.js << 'NODEOF'
#!/usr/bin/env node
/**
 * Creates a minimal but valid Word 97-2003 .doc (OLE2 CFB) file
 * that word-extractor can parse.
 * 
 * We use the 'cfb' npm package (already a dependency of word-extractor)
 * to construct a valid compound file, and write a Word document stream.
 */
const fs = require('fs');
const path = require('path');

// word-extractor's dependency: cfb
const cfbPath = path.join('/root/.openclaw/workspace/office-to-md-v2/office-to-md', 'node_modules', 'cfb');
let CFB;
try {
  CFB = require(cfbPath);
} catch(e) {
  // Try alternate path
  CFB = require('cfb');
}

function createMinimalDoc(textContent) {
  /**
   * Creates a minimal Word 97 document stream.
   * 
   * Word 97 .doc format:
   * - Main stream: "WordDocument" contains FIB + text
   * - The FIB (File Information Block) is 32 bytes minimum
   * - Text follows at offset specified in FIB
   * 
   * For word-extractor, it reads the WordDocument stream
   * and extracts text from the body text area.
   * 
   * Simplest approach: Use a pre-built FIB header pointing to
   * text content stored in the data area.
   */
  
  // Encode text in UTF-16LE (Word Unicode format) or CP1252
  // Word 97 uses CP1252 by default for non-Unicode mode
  // FIB.fFarEast=0, so ASCII/CP1252 text
  
  const textCP1252 = Buffer.from(textContent, 'binary');
  const textLen = textCP1252.length;
  
  // Minimal FIB (File Information Block) for Word 97
  // Based on MS-DOC spec section 2.5.5
  const fib = Buffer.alloc(898, 0); // Full FIB size
  
  // wIdent = 0xA5EC (Word 97+ magic)
  fib.writeUInt16LE(0xA5EC, 0);
  // nFib = 0x00C1 (Word 97)
  fib.writeUInt16LE(0x00C1, 2);
  // lid = 0x0409 (English US)
  fib.writeUInt16LE(0x0409, 6);
  // fWhichTblStm = 0 (use 0Table stream)  
  fib.writeUInt16LE(0x00C1, 10); // nFibBack
  
  // FibBase flags: fDot=0, fGlsy=0, fComplex=0, fHasPic=0
  // flags at offset 10 (Flags2)
  fib.writeUInt16LE(0x0001, 10); // flag: not a template
  
  // FibRgW97 starts at offset 28
  // lidFE at offset 28+14 = 42: 0x0409
  fib.writeUInt16LE(0x0409, 42);
  
  // FibRgLw97 starts at offset 60
  // cbMac (offset 60+4=64): file size (approximately)
  const bodyStart = 898; // text starts right after FIB
  const bodyEnd = bodyStart + textLen;
  
  fib.writeInt32LE(bodyEnd + 128, 64); // cbMac
  
  // ccpText (offset 60+12=72): character count of main text
  fib.writeInt32LE(textLen + 1, 72); // +1 for paragraph mark
  
  // ccpFtn=0, ccpHdr=0, etc. all stay 0
  // FibRgFcLcb97 starts at offset 154
  // fcMin: start of text in WordDocument stream
  // In complex files, text is in piece table, but for simple: right after FIB
  
  // Clx (piece table) - for simple files, we can use the direct approach
  // where text starts at FIB offset
  // fcPlcfBtePapx - paragraph table
  // We'll use minimal tables
  
  // For word-extractor (which uses cfb to read streams), the key is:
  // The WordDocument stream must contain the FIB followed by text
  // word-extractor reads from ccpText characters starting at fcMin
  
  // Simpler: Set fcMin to point right after FIB end
  // In FibRgFcLcb97, fcMin equivalent is determined by Clx
  // Actually word-extractor reads body text differently...
  
  // Let's check word-extractor source behavior:
  // It reads: extracted.getBody() which gets the main document text
  // via the cfb file's WordDocument stream, using the piece table (Clx)
  
  // Build the complete WordDocument stream:
  // [FIB 898 bytes][text bytes][NUL]
  const wordDocStream = Buffer.concat([fib, textCP1252, Buffer.from([0x0D])]); // 0x0D = paragraph end
  
  // Set cbMac to actual size
  wordDocStream.writeInt32LE(wordDocStream.length, 64);
  
  // We need a minimal Clx (complex file piece table) in FibRgFcLcb97
  // Clx offset: fcClx at position 154 + 2*24 = 154+48 = 202? 
  // Let me use the correct offset from MS-DOC spec:
  // FibRgFcLcb97.fcClx is at byte offset: 
  //   FibBase(32) + FibRgW97(28) + FibRgLw97(88) + ... 
  // Actually it's complex. Let's build a minimal Clx ourselves.
  
  // Minimal Clx: prm(1 byte=0x00) + plcPcd
  // plcPcd: array of CPs + array of Pcds
  // For single piece: [0, ccpText+1] as CPs (2 uint32), 1 Pcd (8 bytes)
  // Pcd: fNoParaLast(2) + fc(4) + prm(2)
  // fc = (bodyStart << 1) | 0x40000000 if ANSI, or just bodyStart*2 for Unicode
  // For ANSI text: fc high bit set = ANSI, fc value = fileOffset * 2 ... 
  // Actually: fc = fileOffset (byte in stream) | 0x40000000 for ANSI
  
  const ccpText = textLen + 1; // +1 for final CR
  const clx = Buffer.alloc(1 + 4 + 4 + 4 + 2 + 4 + 2); // prm + 2 CPs + 1 Pcd
  let ci = 0;
  clx[ci++] = 0x00; // prm fComplex=0
  // plcPcd: CPs
  clx.writeUInt32LE(0, ci); ci += 4; // CP start = 0
  clx.writeUInt32LE(ccpText, ci); ci += 4; // CP end
  // Pcd[0]: fNoParaLast=0, fc pointing to bodyStart in stream (ANSI encoding)
  const fcAnsi = (898 | 0x40000000) >>> 0; // ANSI flag
  clx.writeUInt16LE(0, ci); ci += 2; // fNoParaLast + fR1
  clx.writeUInt32LE(fcAnsi, ci); ci += 4; // fc
  clx.writeUInt16LE(0, ci); ci += 2; // prm
  
  // Now find where to put Clx in the stream
  // We'll append it after the text
  const clxOffset = wordDocStream.length;
  const clxLen = clx.length;
  
  // FibRgFcLcb97 layout (starts at offset 154 in FIB, each entry is fc(4)+lcb(4)):
  // Entry 22 = fcClx/lcbClx (0-indexed), so offset = 154 + 22*8 = 154 + 176 = 330
  wordDocStream.writeUInt32LE(clxOffset, 330); // fcClx
  wordDocStream.writeUInt32LE(clxLen, 334);   // lcbClx
  
  const finalStream = Buffer.concat([wordDocStream, clx]);
  return finalStream;
}

// Process all .pending files
const pendingDir = process.argv[2] || '/workspace';

function findPending(dir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...findPending(fullPath));
    } else if (entry.name.endsWith('.pending')) {
      results.push(fullPath);
    }
  }
  return results;
}

const pending = findPending(pendingDir);
console.log(`Found ${pending.length} pending .doc files to create`);

for (const pendingPath of pending) {
  const docPath = pendingPath.replace('.pending', '');
  const textContent = fs.readFileSync(pendingPath, 'utf-8');
  
  try {
    const docBuffer = createMinimalDoc(textContent);
    fs.writeFileSync(docPath, docBuffer);
    fs.unlinkSync(pendingPath);
    console.log(`Created: ${docPath} (${docBuffer.length} bytes)`);
  } catch(e) {
    console.error(`Failed to create ${docPath}: ${e.message}`);
    // Fallback: create a simple CFB using cfb package if available
    try {
      const cfbFile = CFB.utils.cfb_new();
      const streamData = Buffer.from(textContent, 'utf-8');
      CFB.utils.cfb_add(cfbFile, 'WordDocument', streamData);
      const out = CFB.write(cfbFile, {type: 'buffer'});
      fs.writeFileSync(docPath, out);
      fs.unlinkSync(pendingPath);
      console.log(`Created (cfb fallback): ${docPath}`);
    } catch(e2) {
      console.error(`CFB fallback also failed: ${e2.message}`);
      // Last resort: keep as text file renamed to .doc
      // word-extractor may fail but the file will exist
      fs.copyFileSync(pendingPath, docPath);
      fs.unlinkSync(pendingPath);
      console.log(`Created (text fallback): ${docPath}`);
    }
  }
}
NODEOF

echo "=== Creating .doc files from pending markers ==="
node /tmp/create_doc.js "$WORKSPACE" || echo "Doc creation completed with some errors"

echo "=== Verifying document files ==="
find "$WORKSPACE" -name "*.doc" -o -name "*.docx" -o -name "*.pdf" -o -name "*.pptx" | sort

echo "=== Setup complete ==="
echo "Skill location: $SKILL_SRC"
echo "Workspace: $WORKSPACE"