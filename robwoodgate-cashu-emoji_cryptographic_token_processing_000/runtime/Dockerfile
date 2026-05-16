FROM debian:12-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create cashu-emoji tool as a local script
RUN mkdir -p /opt/cashu-emoji/bin

RUN cat > /opt/cashu-emoji/bin/cashu-emoji.js << 'EOF'
#!/usr/bin/env node
/**
 * cashu-emoji: encode/decode Cashu tokens hidden inside emoji
 * Uses Unicode variation selectors (VS1-VS16, U+FE00..U+FE0F) and
 * supplementary variation selectors (U+E0100..U+E01EF) to embed bits.
 * Encoding scheme: each byte of the UTF-8 payload is encoded as 8 bits
 * using zero-width variation selector codepoints appended after a base emoji.
 *
 * Simpler approach: encode each character of the token string as a sequence
 * of invisible Unicode tags (U+E0000 block) appended to the base emoji.
 */

const args = process.argv.slice(2);
const command = args[0];

function encodeToEmoji(baseEmoji, token) {
  // Use Unicode tag characters (U+E0000..U+E007F) to encode each ASCII char
  // U+E0000 is the base, U+E0041 = 'A', etc. (offset by 0xE0000)
  // We'll use U+E0001 as start marker and U+E007F as end marker
  let hidden = '';
  for (let i = 0; i < token.length; i++) {
    const code = token.charCodeAt(i);
    hidden += String.fromCodePoint(0xE0000 + code);
  }
  return baseEmoji + hidden;
}

function decodeFromEmoji(encodedEmoji) {
  // Extract the base emoji (skip to tag characters)
  const codePoints = [...encodedEmoji].map(c => c.codePointAt(0));
  let token = '';
  for (const cp of codePoints) {
    if (cp >= 0xE0000 && cp <= 0xE007F) {
      const charCode = cp - 0xE0000;
      if (charCode > 0) {
        token += String.fromCharCode(charCode);
      }
    }
  }
  return token;
}

if (command === 'encode') {
  const emoji = args[1];
  const token = args[2];
  if (!emoji || !token) {
    console.error('Usage: cashu-emoji encode <emoji> <token>');
    process.exit(1);
  }
  const result = encodeToEmoji(emoji, token);
  process.stdout.write(result + '\n');
} else if (command === 'decode') {
  const encodedEmoji = args[1];
  if (!encodedEmoji) {
    console.error('Usage: cashu-emoji decode <encoded-emoji>');
    process.exit(1);
  }
  const token = decodeFromEmoji(encodedEmoji);
  console.log(token);
} else if (command === '--version' || command === '-v') {
  console.log('cashu-emoji 1.0.0 (local)');
} else if (command === '--help' || command === '-h' || !command) {
  console.log('cashu-emoji - encode/decode Cashu tokens in emoji');
  console.log('');
  console.log('Commands:');
  console.log('  encode <emoji> <token>   Encode a token into an emoji');
  console.log('  decode <encoded-emoji>   Decode a token from an emoji');
} else {
  console.error('Unknown command: ' + command);
  process.exit(1);
}
EOF

RUN chmod +x /opt/cashu-emoji/bin/cashu-emoji.js

# Make CLI accessible globally
RUN ln -sf /opt/cashu-emoji/bin/cashu-emoji.js /usr/local/bin/cashu-emoji

WORKDIR /workspace