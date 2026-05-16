#!/bin/bash
set -e

WORKSPACE=/workspace

# Create the mock @resciencelab/declaw npm package
mkdir -p "$WORKSPACE/node_modules/@resciencelab/declaw"

# Create package.json for the mock package
cat > "$WORKSPACE/node_modules/@resciencelab/declaw/package.json" << 'PKGJSON'
{
  "name": "@resciencelab/declaw",
  "version": "0.1.2",
  "main": "index.js",
  "description": "Mock declaw P2P library for OpenClaw agents"
}
PKGJSON

# Create the mock index.js that logs all tool calls to a JSON call log
cat > "$WORKSPACE/node_modules/@resciencelab/declaw/index.js" << 'MOCKJS'
const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(process.env.DECLAW_LOG || '/tmp/declaw_calls.json');

function appendCall(toolName, params, result) {
  let log = [];
  if (fs.existsSync(LOG_FILE)) {
    try { log = JSON.parse(fs.readFileSync(LOG_FILE, 'utf8')); } catch(e) { log = []; }
  }
  log.push({ tool: toolName, params, result, ts: Date.now(), seq: log.length });
  fs.writeFileSync(LOG_FILE, JSON.stringify(log, null, 2));
  return result;
}

// Simulated peer state
const knownPeers = {};
let sendAttemptCount = 0;

function p2p_add_peer(ygg_addr, alias) {
  if (!ygg_addr || (!ygg_addr.startsWith('200:') && !ygg_addr.startsWith('fd77:'))) {
    return appendCall('p2p_add_peer', { ygg_addr, alias }, { success: false, error: 'invalid_address' });
  }
  knownPeers[ygg_addr] = { alias: alias || null, added_at: Date.now() };
  return appendCall('p2p_add_peer', { ygg_addr, alias }, { success: true, peer: ygg_addr, alias: alias || null });
}

function p2p_send_message(ygg_addr, message, port) {
  sendAttemptCount++;
  const effectivePort = port !== undefined ? port : 8099;
  
  // Simulate: first send attempt fails with timeout to test error handling rule
  if (sendAttemptCount === 1) {
    return appendCall('p2p_send_message', { ygg_addr, message, port: effectivePort }, { 
      success: false, 
      error: 'timeout', 
      detail: 'Connection timed out after 30s' 
    });
  }
  
  // Second attempt succeeds (after yggdrasil_check was called)
  return appendCall('p2p_send_message', { ygg_addr, message, port: effectivePort }, { 
    success: true, 
    delivered: true, 
    peer: ygg_addr, 
    port: effectivePort 
  });
}

function p2p_list_peers() {
  const peers = Object.entries(knownPeers).map(([addr, info]) => ({
    address: addr, alias: info.alias, last_seen: new Date(info.added_at).toISOString()
  }));
  return appendCall('p2p_list_peers', {}, { peers });
}

function p2p_status() {
  return appendCall('p2p_status', {}, {
    own_address: '200:local::agent:1',
    known_peers: Object.keys(knownPeers).length,
    unread_inbox: 0
  });
}

function p2p_discover() {
  return appendCall('p2p_discover', {}, { new_peers: 3, total_known: Object.keys(knownPeers).length + 3 });
}

function yggdrasil_check() {
  return appendCall('yggdrasil_check', {}, { status: 'yggdrasil', running: true, reachable_peers: 5 });
}

module.exports = {
  p2p_add_peer,
  p2p_send_message,
  p2p_list_peers,
  p2p_status,
  p2p_discover,
  yggdrasil_check
};
MOCKJS

# Create workspace package.json so Node can find the local node_modules
cat > "$WORKSPACE/package.json" << 'WKPKG'
{
  "name": "research-ops-workspace",
  "version": "1.0.0",
  "dependencies": {
    "@resciencelab/declaw": "file:./node_modules/@resciencelab/declaw"
  }
}
WKPKG

# Initialize the call log as an empty array
echo "[]" > /tmp/declaw_calls.json

chmod -R 755 "$WORKSPACE/node_modules"
chmod 666 /tmp/declaw_calls.json

echo "Mock @resciencelab/declaw package installed."
echo "Call log will be written to: /tmp/declaw_calls.json"