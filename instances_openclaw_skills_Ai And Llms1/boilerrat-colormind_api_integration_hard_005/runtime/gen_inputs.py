import os
import json

# Create the colormind scripts directory structure
os.makedirs('scripts', exist_ok=True)

# Write list_models.mjs
list_models = '''import https from 'https';
import http from 'http';

const options = {
  hostname: 'colormind.io',
  path: '/list/',
  method: 'GET'
};

http.get('http://colormind.io/list/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    try {
      const parsed = JSON.parse(data);
      console.log(JSON.stringify(parsed));
    } catch(e) {
      console.error('Parse error:', e.message);
      process.exit(1);
    }
  });
}).on('error', (e) => {
  console.error('Request error:', e.message);
  process.exit(1);
});
''';

with open('scripts/list_models.mjs', 'w') as f:
    f.write(list_models)

# Write generate_palette.mjs
generate_palette = '''import http from 'http';

const args = process.argv.slice(2);
let model = 'default';
let inputColors = null;
let pretty = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--model' && args[i+1]) model = args[++i];
  else if (args[i] === '--input') {
    inputColors = [];
    i++;
    while (i < args.length && !args[i].startsWith('--')) {
      const val = args[i];
      if (val === 'N') {
        inputColors.push('N');
      } else {
        const parts = val.split(',').map(Number);
        if (parts.length === 3 && parts.every(n => !isNaN(n))) {
          inputColors.push(parts);
        } else {
          console.error('Invalid color:', val);
          process.exit(1);
        }
      }
      i++;
    }
    i--;
  } else if (args[i] === '--pretty') pretty = true;
}

const body = { model };
if (inputColors) body.input = inputColors;

const postData = JSON.stringify(body);

const options = {
  hostname: 'colormind.io',
  path: '/api/',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    try {
      const parsed = JSON.parse(data);
      console.log(JSON.stringify(parsed));
      if (pretty && parsed.result) {
        process.stderr.write("\n## Palette\n");
        parsed.result.forEach((color, i) => {
          const hex = color.map(c => c.toString(16).padStart(2,'0')).join('');
          process.stderr.write(`- Slot ${i+1}: #${hex} | rgb(${color.join(', ')})\n`);
        });
      }
    } catch(e) {
      console.error('Parse error:', e.message);
      process.exit(1);
    }
  });
});

req.on('error', (e) => {
  console.error('Request error:', e.message);
  process.exit(1);
});

req.write(postData);
req.end();
''';

with open('scripts/generate_palette.mjs', 'w') as f:
    f.write(generate_palette)

# Write a marker file so eval can confirm scripts were present
with open('scripts/.marker', 'w') as f:
    f.write('MARKER:colormind_scripts_ready:v1')

print('Input files created: scripts/list_models.mjs, scripts/generate_palette.mjs')
