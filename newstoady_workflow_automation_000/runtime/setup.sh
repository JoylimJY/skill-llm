#!/bin/bash
set -e

WORKSPACE="/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"

# Create the mock Node.js scripts that simulate NewsToday's CLI tools.
# These scripts write realistic JSON state to data/users/<userId>.json
# and produce expected stdout output.

# --- register.js ---
cat > "$SCRIPTS_DIR/register.js" << 'REGISTER_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length < 1) {
    console.error("Usage: node register.js <userId> [language] [topics] [channel]");
    process.exit(1);
}

const userId = args[0];
const language = args[1] || 'zh';
const topicsRaw = args[2] || '';
const channel = args[3] || 'telegram';
const topics = topicsRaw ? topicsRaw.split(',').map(t => t.trim()).filter(Boolean) : [];

const userDir = path.join(__dirname, '..', 'data', 'users');
fs.mkdirSync(userDir, { recursive: true });

const userFile = path.join(userDir, `${userId}.json`);

let existing = {};
if (fs.existsSync(userFile)) {
    existing = JSON.parse(fs.readFileSync(userFile, 'utf8'));
}

const userData = {
    userId,
    language,
    topics,
    channel,
    preferences: existing.preferences || {},
    push: existing.push || { enabled: false },
    registeredAt: existing.registeredAt || new Date().toISOString()
};

fs.writeFileSync(userFile, JSON.stringify(userData, null, 2), 'utf8');
console.log(`✅ User [${userId}] registered. Language: ${language}, Topics: ${topics.join(', ')}, Channel: ${channel}`);
REGISTER_EOF

# --- preference.js ---
cat > "$SCRIPTS_DIR/preference.js" << 'PREF_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];
const userId = args[1];

const userFile = path.join(__dirname, '..', 'data', 'users', `${userId}.json`);

if (!fs.existsSync(userFile)) {
    console.error(`❌ User [${userId}] not found. Please register first.`);
    process.exit(1);
}

const userData = JSON.parse(fs.readFileSync(userFile, 'utf8'));

if (command === 'show') {
    console.log(`📊 Preferences for [${userId}]:`);
    const prefs = userData.preferences || {};
    if (Object.keys(prefs).length === 0) {
        console.log("  (no preferences set)");
    } else {
        for (const [topic, weight] of Object.entries(prefs)) {
            console.log(`  ${topic}: ${weight}`);
        }
    }
} else if (command === 'set') {
    const topic = args[2];
    const weightStr = args[3];
    if (!topic || weightStr === undefined) {
        console.error("Usage: preference.js set <userId> <topic> <weight 0-1>");
        process.exit(1);
    }
    const weight = parseFloat(weightStr);
    if (isNaN(weight) || weight < 0 || weight > 1) {
        console.error(`❌ Invalid weight: ${weightStr}. Must be a number between 0 and 1.`);
        process.exit(1);
    }
    if (!userData.preferences) userData.preferences = {};
    userData.preferences[topic] = weight;
    fs.writeFileSync(userFile, JSON.stringify(userData, null, 2), 'utf8');
    console.log(`✅ Set preference [${topic}] = ${weight} for user [${userId}]`);
} else if (command === 'reset') {
    userData.preferences = {};
    fs.writeFileSync(userFile, JSON.stringify(userData, null, 2), 'utf8');
    console.log(`✅ Preferences reset for user [${userId}]`);
} else {
    console.error(`Unknown command: ${command}`);
    process.exit(1);
}
PREF_EOF

# --- push-toggle.js ---
cat > "$SCRIPTS_DIR/push-toggle.js" << 'PUSH_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const command = args[0];
const userId = args[1];

const userFile = path.join(__dirname, '..', 'data', 'users', `${userId}.json`);

if (!fs.existsSync(userFile)) {
    console.error(`❌ User [${userId}] not found. Please register first.`);
    process.exit(1);
}

const userData = JSON.parse(fs.readFileSync(userFile, 'utf8'));

if (command === 'on') {
    // Parse optional flags
    let morning = '08:00';
    let evening = '20:00';
    let channel = userData.channel || 'telegram';

    for (let i = 2; i < args.length; i++) {
        if (args[i] === '--morning' && args[i+1]) {
            morning = args[i+1]; i++;
        } else if (args[i] === '--evening' && args[i+1]) {
            evening = args[i+1]; i++;
        } else if (args[i] === '--channel' && args[i+1]) {
            channel = args[i+1]; i++;
        }
    }
    userData.push = { enabled: true, morning, evening, channel };
    fs.writeFileSync(userFile, JSON.stringify(userData, null, 2), 'utf8');
    console.log(`✅ Push enabled for [${userId}]: morning=${morning}, evening=${evening}, channel=${channel}`);

} else if (command === 'off') {
    if (!userData.push) userData.push = {};
    userData.push.enabled = false;
    fs.writeFileSync(userFile, JSON.stringify(userData, null, 2), 'utf8');
    console.log(`✅ Push disabled for [${userId}]`);

} else if (command === 'status') {
    const push = userData.push || { enabled: false };
    console.log(`📬 Push status for [${userId}]:`);
    console.log(`  enabled: ${push.enabled}`);
    if (push.enabled) {
        console.log(`  morning: ${push.morning}`);
        console.log(`  evening: ${push.evening}`);
        console.log(`  channel: ${push.channel}`);
    }
} else {
    console.error(`Unknown command: ${command}`);
    process.exit(1);
}
PUSH_EOF

# --- morning-push.js ---
cat > "$SCRIPTS_DIR/morning-push.js" << 'MORNING_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const userId = process.argv[2];
const logDir = path.join(__dirname, '..', 'logs', 'morning');
fs.mkdirSync(logDir, { recursive: true });

const date = new Date().toISOString().split('T')[0];
const logFile = path.join(logDir, `${date}.log`);

let userInfo = userId ? `user [${userId}]` : 'anonymous user';
let topicsInfo = '';

if (userId) {
    const userFile = path.join(__dirname, '..', 'data', 'users', `${userId}.json`);
    if (fs.existsSync(userFile)) {
        const userData = JSON.parse(fs.readFileSync(userFile, 'utf8'));
        topicsInfo = userData.topics ? ` | Topics: ${userData.topics.join(', ')}` : '';
    }
}

const logEntry = `[${new Date().toISOString()}] Morning push delivered to ${userInfo}${topicsInfo}\n`;
fs.appendFileSync(logFile, logEntry);

console.log(`🌅 Morning briefing pushed to ${userInfo}`);
console.log(`📰 10 stories aggregated from RSS + WebSearch`);
console.log(`📁 Log written to ${logFile}`);
MORNING_EOF

# --- evening-push.js ---
cat > "$SCRIPTS_DIR/evening-push.js" << 'EVENING_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const userId = process.argv[2];
const logDir = path.join(__dirname, '..', 'logs', 'evening');
fs.mkdirSync(logDir, { recursive: true });

const date = new Date().toISOString().split('T')[0];
const logFile = path.join(logDir, `${date}.log`);

let userInfo = userId ? `user [${userId}]` : 'anonymous user';

const logEntry = `[${new Date().toISOString()}] Evening push delivered to ${userInfo}\n`;
fs.appendFileSync(logFile, logEntry);

console.log(`🌙 Evening briefing pushed to ${userInfo}`);
console.log(`📰 3-5 top stories + next day preview`);
EVENING_EOF

# --- rss-fetch.js ---
cat > "$SCRIPTS_DIR/rss-fetch.js" << 'RSS_EOF'
#!/usr/bin/env node
const args = process.argv.slice(2);
let lang = 'zh';
let topics = [];

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--lang' && args[i+1]) { lang = args[i+1]; i++; }
    else if (args[i] === '--topics' && args[i+1]) { topics = args[i+1].split(','); i++; }
}

console.log(`📡 Fetching RSS feeds [lang=${lang}${topics.length ? ', topics=' + topics.join(',') : ''}]`);
console.log(`✅ Fetched 47 articles, deduplicated to 10 stories`);
RSS_EOF

# --- breaking-alert.js ---
cat > "$SCRIPTS_DIR/breaking-alert.js" << 'ALERT_EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const userId = process.argv[2];

if (!userId) {
    console.error("Usage: breaking-alert.js <userId>");
    process.exit(1);
}

const userFile = path.join(__dirname, '..', 'data', 'users', `${userId}.json`);
if (!fs.existsSync(userFile)) {
    console.error(`❌ User [${userId}] not found.`);
    process.exit(1);
}

console.log(`🚨 Breaking alert check for [${userId}] — no threshold events detected.`);
ALERT_EOF

# Make all scripts executable
chmod +x "$SCRIPTS_DIR"/*.js

echo "✅ All NewsToday mock scripts installed and ready."
ls -la "$SCRIPTS_DIR"/