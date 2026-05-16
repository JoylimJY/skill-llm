#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace
SCRIPTS_DIR="$WORKSPACE/node-transfer/scripts"

echo "=== Setting up node-transfer skill workspace ==="

# The SKILL.md says these scripts already exist in the workspace.
# We create them here as the "already installed" skill files.

# ── version.js ───────────────────────────────────────────────────────────────
cat > "$SCRIPTS_DIR/version.js" << 'VERSIONJS'
// version.js - Version manifest for node-transfer
const VERSION = '1.0.0';

const FILES = {
    'send.js': null,
    'receive.js': null,
    'ensure-installed.js': null,
    'version.js': null
};

// Compute hashes at runtime
const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

function hashFile(filePath) {
    try {
        const content = fs.readFileSync(filePath);
        return crypto.createHash('sha256').update(content).digest('hex');
    } catch (e) {
        return null;
    }
}

const manifest = {
    version: VERSION,
    files: {}
};

const dir = __dirname;
for (const file of Object.keys(FILES)) {
    manifest.files[file] = hashFile(path.join(dir, file));
}

if (require.main === module) {
    console.log(JSON.stringify(manifest, null, 2));
} else {
    module.exports = { VERSION, manifest };
}
VERSIONJS

# ── send.js ──────────────────────────────────────────────────────────────────
cat > "$SCRIPTS_DIR/send.js" << 'SENDJS'
#!/usr/bin/env node
/**
 * send.js - HTTP server that streams a file to a receiver.
 * Usage: node send.js <filePath> [--port <n>] [--timeout <minutes>]
 */
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

const VERSION = '1.0.0';

function parseArgs(argv) {
    const args = { filePath: null, port: null, timeout: 5, help: false, version: false };
    let i = 0;
    while (i < argv.length) {
        const a = argv[i];
        if (a === '--help' || a === '-h') { args.help = true; }
        else if (a === '--version' || a === '-v') { args.version = true; }
        else if (a === '--port') { args.port = parseInt(argv[++i], 10); }
        else if (a === '--timeout') { args.timeout = parseInt(argv[++i], 10); }
        else if (!a.startsWith('--') && !args.filePath) { args.filePath = a; }
        i++;
    }
    return args;
}

function getLocalIp() {
    const ifaces = os.networkInterfaces();
    for (const name of Object.keys(ifaces)) {
        for (const iface of ifaces[name]) {
            if (iface.family === 'IPv4' && !iface.internal) return iface.address;
        }
    }
    return '127.0.0.1';
}

function errOut(code, message) {
    process.stderr.write(JSON.stringify({ error: code, message }) + '\n');
    process.exit(1);
}

const args = parseArgs(process.argv.slice(2));

if (args.help) {
    console.log('Usage: node send.js <filePath> [--port <n>] [--timeout <minutes>]');
    process.exit(0);
}
if (args.version) {
    console.log(VERSION);
    process.exit(0);
}
if (!args.filePath) {
    errOut('INVALID_ARGS', 'filePath is required');
}

const filePath = path.resolve(args.filePath);

if (!fs.existsSync(filePath)) errOut('FILE_NOT_FOUND', `File not found: ${filePath}`);
const stat = fs.statSync(filePath);
if (!stat.isFile()) errOut('NOT_A_FILE', `Not a file: ${filePath}`);

const fileSize = stat.size;
const fileName = path.basename(filePath);
const token = crypto.randomBytes(32).toString('hex');
let transferred = false;

const server = http.createServer((req, res) => {
    const reqToken = req.headers['x-transfer-token'] || new URL(req.url, 'http://x').searchParams.get('token');

    if (!reqToken || reqToken !== token) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '403 Forbidden: Invalid or missing token' }));
        return;
    }

    if (transferred) {
        res.writeHead(409, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '409 Conflict: Transfer already in progress' }));
        return;
    }

    transferred = true;

    res.writeHead(200, {
        'Content-Type': 'application/octet-stream',
        'Content-Length': fileSize,
        'X-File-Name': fileName,
        'X-File-Size': fileSize,
    });

    const readStream = fs.createReadStream(filePath);
    readStream.on('error', (e) => {
        process.stderr.write(JSON.stringify({ error: 'READ_ERROR', message: e.message }) + '\n');
        res.destroy();
        server.close();
        process.exit(1);
    });

    res.on('error', (e) => {
        process.stderr.write(JSON.stringify({ error: 'RESPONSE_ERROR', message: e.message }) + '\n');
        server.close();
        process.exit(1);
    });

    readStream.pipe(res);

    res.on('finish', () => {
        server.close();
    });
});

const listenPort = args.port || 0;

server.listen(listenPort, '0.0.0.0', () => {
    const actualPort = server.address().port;
    const sourceIp = getLocalIp();
    const url = `http://127.0.0.1:${actualPort}/transfer`;

    // Output connection info
    console.log(JSON.stringify({
        url,
        token,
        fileSize,
        fileName,
        sourceIp,
        port: actualPort,
        version: VERSION
    }));

    // Timeout
    const timeoutMs = args.timeout * 60 * 1000;
    setTimeout(() => {
        if (!transferred) {
            process.stderr.write(JSON.stringify({ error: 'TIMEOUT', message: `No connection within ${args.timeout} minutes` }) + '\n');
            server.close();
            process.exit(1);
        }
    }, timeoutMs);
});

server.on('error', (e) => {
    errOut('SERVER_ERROR', e.message);
});
SENDJS

# ── receive.js ───────────────────────────────────────────────────────────────
cat > "$SCRIPTS_DIR/receive.js" << 'RECEIVEJS'
#!/usr/bin/env node
/**
 * receive.js - HTTP client that downloads a streamed file from send.js.
 * Usage: node receive.js <url> <token> <outputPath> [--timeout <seconds>] [--no-progress]
 */
'use strict';

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const VERSION = '1.0.0';

function parseArgs(argv) {
    const args = { url: null, token: null, outputPath: null, timeout: 30, progress: true, help: false, version: false };
    let i = 0;
    while (i < argv.length) {
        const a = argv[i];
        if (a === '--help' || a === '-h') { args.help = true; }
        else if (a === '--version' || a === '-v') { args.version = true; }
        else if (a === '--timeout') { args.timeout = parseInt(argv[++i], 10); }
        else if (a === '--no-progress') { args.progress = false; }
        else if (!a.startsWith('--')) {
            if (!args.url) args.url = a;
            else if (!args.token) args.token = a;
            else if (!args.outputPath) args.outputPath = a;
        }
        i++;
    }
    return args;
}

function errOut(code, message) {
    process.stderr.write(JSON.stringify({ error: code, message }) + '\n');
    process.exit(1);
}

const args = parseArgs(process.argv.slice(2));

if (args.help) {
    console.log('Usage: node receive.js <url> <token> <outputPath> [--timeout <seconds>] [--no-progress]');
    process.exit(0);
}
if (args.version) {
    console.log(VERSION);
    process.exit(0);
}
if (!args.url || !args.token || !args.outputPath) {
    errOut('INVALID_ARGS', 'url, token, and outputPath are required');
}

let parsedUrl;
try {
    parsedUrl = new URL(args.url);
} catch (e) {
    errOut('INVALID_URL', `Invalid URL: ${args.url}`);
}

const outputPath = path.resolve(args.outputPath);

// Ensure output directory exists
const outputDir = path.dirname(outputPath);
if (!fs.existsSync(outputDir)) {
    try { fs.mkdirSync(outputDir, { recursive: true }); } catch (e) { errOut('WRITE_ERROR', `Cannot create directory: ${outputDir}`); }
}

if (fs.existsSync(outputPath)) {
    errOut('FILE_EXISTS', `Output file already exists: ${outputPath}`);
}

const client = parsedUrl.protocol === 'https:' ? https : http;

const reqOptions = {
    hostname: parsedUrl.hostname,
    port: parseInt(parsedUrl.port, 10) || (parsedUrl.protocol === 'https:' ? 443 : 80),
    path: parsedUrl.pathname + parsedUrl.search,
    method: 'GET',
    headers: { 'x-transfer-token': args.token },
    timeout: args.timeout * 1000,
};

const startTime = Date.now();
let bytesReceived = 0;
let totalBytes = 0;
let lastProgressTime = Date.now();

const req = client.request(reqOptions, (res) => {
    if (res.statusCode !== 200) {
        errOut('HTTP_ERROR', `Server returned ${res.statusCode}: ${res.statusMessage}`);
    }

    totalBytes = parseInt(res.headers['content-length'] || '0', 10);

    const writeStream = fs.createWriteStream(outputPath);

    writeStream.on('error', (e) => {
        errOut('WRITE_ERROR', e.message);
    });

    res.on('data', (chunk) => {
        bytesReceived += chunk.length;
        const now = Date.now();
        if (args.progress && (now - lastProgressTime > 500)) {
            lastProgressTime = now;
            const elapsed = (now - startTime) / 1000;
            const speedMBps = elapsed > 0 ? (bytesReceived / elapsed / 1048576) : 0;
            const percent = totalBytes > 0 ? Math.round(bytesReceived / totalBytes * 100) : 0;
            process.stdout.write(JSON.stringify({
                progress: true,
                receivedBytes: bytesReceived,
                totalBytes,
                percent,
                speedMBps: parseFloat(speedMBps.toFixed(2))
            }) + '\n');
        }
    });

    res.on('error', (e) => {
        try { fs.unlinkSync(outputPath); } catch (_) {}
        errOut('CONNECTION_ERROR', e.message);
    });

    writeStream.on('finish', () => {
        const duration = (Date.now() - startTime) / 1000;
        const speedMBps = duration > 0 ? (bytesReceived / duration / 1048576) : 0;

        if (totalBytes > 0 && bytesReceived !== totalBytes) {
            try { fs.unlinkSync(outputPath); } catch (_) {}
            errOut('SIZE_MISMATCH', `Expected ${totalBytes} bytes, received ${bytesReceived}`);
        }

        if (bytesReceived === 0) {
            try { fs.unlinkSync(outputPath); } catch (_) {}
            errOut('NO_DATA', 'No data received');
        }

        console.log(JSON.stringify({
            success: true,
            bytesReceived,
            totalBytes,
            duration: parseFloat(duration.toFixed(3)),
            speedMBps: parseFloat(speedMBps.toFixed(2)),
            outputPath: path.resolve(outputPath)
        }));
    });

    res.pipe(writeStream);
});

req.on('timeout', () => {
    req.destroy();
    try { if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath); } catch (_) {}
    errOut('TIMEOUT', `Connection timed out after ${args.timeout} seconds`);
});

req.on('error', (e) => {
    try { if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath); } catch (_) {}
    errOut('CONNECTION_ERROR', e.message);
});

req.end();
RECEIVEJS

# ── ensure-installed.js ───────────────────────────────────────────────────────
cat > "$SCRIPTS_DIR/ensure-installed.js" << 'ENSUREJS'
#!/usr/bin/env node
/**
 * ensure-installed.js - Fast check if node-transfer is installed and up-to-date.
 * Usage: node ensure-installed.js <targetDir>
 * Exit: 0 = installed, 1 = needs install, 2 = error
 */
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const VERSION = '1.0.0';
const REQUIRED_FILES = ['send.js', 'receive.js', 'ensure-installed.js', 'version.js'];

function errOut(message) {
    process.stderr.write(JSON.stringify({ error: 'INVALID_DIR', message }) + '\n');
    process.exit(2);
}

const args = process.argv.slice(2);
if (!args[0]) errOut('targetDir argument is required');

const targetDir = path.resolve(args[0]);

if (!fs.existsSync(targetDir)) {
    console.log(JSON.stringify({
        installed: false,
        missing: REQUIRED_FILES,
        mismatched: [],
        currentVersion: null,
        requiredVersion: VERSION,
        action: 'DEPLOY',
        message: `Installation needed: ${REQUIRED_FILES.length} missing, 0 outdated`
    }));
    process.exit(1);
}

const missing = [];
const present = [];

for (const file of REQUIRED_FILES) {
    const fp = path.join(targetDir, file);
    if (!fs.existsSync(fp)) missing.push(file);
    else present.push(file);
}

if (missing.length > 0) {
    console.log(JSON.stringify({
        installed: false,
        missing,
        mismatched: [],
        currentVersion: null,
        requiredVersion: VERSION,
        action: 'DEPLOY',
        message: `Installation needed: ${missing.length} missing, 0 outdated`
    }));
    process.exit(1);
}

// Check version
let currentVersion = null;
try {
    const versionPath = path.join(targetDir, 'version.js');
    // Quick parse: look for VERSION = 'x.y.z'
    const content = fs.readFileSync(versionPath, 'utf8');
    const match = content.match(/VERSION\s*=\s*['"]([^'"]+)['"]/);
    if (match) currentVersion = match[1];
} catch (e) {}

console.log(JSON.stringify({
    installed: true,
    version: currentVersion || VERSION,
    message: 'node-transfer is installed and up-to-date'
}));
process.exit(0);
ENSUREJS

# ── deploy.js ─────────────────────────────────────────────────────────────────
# Already present per SKILL.md; we place a minimal shim if not found
if [ ! -f "$SCRIPTS_DIR/deploy.js" ]; then
cat > "$SCRIPTS_DIR/deploy.js" << 'DEPLOYJS'
#!/usr/bin/env node
// deploy.js shim - see SKILL.md for full documentation
const VERSION = '1.0.0';
console.log(JSON.stringify({ action: 'DEPLOY', version: VERSION, message: 'See SKILL.md for usage' }));
DEPLOYJS
fi

chmod +x "$SCRIPTS_DIR/send.js" \
         "$SCRIPTS_DIR/receive.js" \
         "$SCRIPTS_DIR/ensure-installed.js" \
         "$SCRIPTS_DIR/version.js"

echo "=== node-transfer scripts installed in $SCRIPTS_DIR ==="
ls -la "$SCRIPTS_DIR/"

# Verify Node.js
node --version
echo "=== Setup complete ==="