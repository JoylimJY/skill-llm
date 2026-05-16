FROM node:20-bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create a mock agent-traffic-analyzer CLI tool
RUN mkdir -p /usr/local/lib/agent-traffic-analyzer && \
    cat > /usr/local/lib/agent-traffic-analyzer/index.js << 'EOF'
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);

if (args.includes('--version') || args.includes('-v')) {
  console.log('1.0.0');
  process.exit(0);
}

if (args.includes('--help') || args.includes('-h')) {
  console.log('Usage: agent-traffic-analyzer [options] <logfile>');
  console.log('Options:');
  console.log('  --version       Show version');
  console.log('  --output <file> Write report to file');
  console.log('  --format <fmt>  Output format: json|text (default: text)');
  process.exit(0);
}

const outputIdx = args.indexOf('--output');
const outputFile = outputIdx !== -1 ? args[outputIdx + 1] : null;
const formatIdx = args.indexOf('--format');
const format = formatIdx !== -1 ? args[formatIdx + 1] : 'text';

const inputFile = args.filter(a => !a.startsWith('--') && args.indexOf(a) !== outputIdx + 1 && args.indexOf(a) !== formatIdx + 1).pop();

if (!inputFile) {
  console.error('Error: No input file specified');
  process.exit(1);
}

let data;
try {
  const content = fs.readFileSync(inputFile, 'utf8');
  data = JSON.parse(content);
} catch (e) {
  console.error('Error reading input file:', e.message);
  process.exit(1);
}

const messages = Array.isArray(data) ? data : [];
const agentStats = {};
const pairStats = {};

for (const msg of messages) {
  const from = msg.from || msg.sender;
  const to = msg.to || msg.receiver;
  const latency = msg.latency_ms || msg.latency || 0;
  const status = msg.status || 'delivered';

  for (const agent of [from, to]) {
    if (!agentStats[agent]) agentStats[agent] = { sent: 0, received: 0, totalLatency: 0, errors: 0 };
  }
  agentStats[from].sent++;
  agentStats[to].received++;
  agentStats[from].totalLatency += latency;
  if (status !== 'delivered') agentStats[from].errors++;

  const pair = `${from}->${to}`;
  if (!pairStats[pair]) pairStats[pair] = { count: 0, totalLatency: 0, errors: 0 };
  pairStats[pair].count++;
  pairStats[pair].totalLatency += latency;
  if (status !== 'delivered') pairStats[pair].errors++;
}

const report = {
  summary: {
    total_messages: messages.length,
    agents: Object.keys(agentStats).length,
    communication_pairs: Object.keys(pairStats).length,
  },
  agent_stats: Object.entries(agentStats).map(([name, s]) => ({
    agent: name,
    messages_sent: s.sent,
    messages_received: s.received,
    avg_latency_ms: s.sent > 0 ? Math.round(s.totalLatency / s.sent) : 0,
    error_rate: s.sent > 0 ? (s.errors / s.sent).toFixed(3) : '0.000',
  })).sort((a, b) => b.avg_latency_ms - a.avg_latency_ms),
  bottlenecks: Object.entries(pairStats).map(([pair, s]) => ({
    pair,
    message_count: s.count,
    avg_latency_ms: Math.round(s.totalLatency / s.count),
    error_rate: (s.errors / s.count).toFixed(3),
  })).sort((a, b) => b.avg_latency_ms - a.avg_latency_ms).slice(0, 5),
};

let output;
if (format === 'json') {
  output = JSON.stringify(report, null, 2);
} else {
  output = [
    '=== Agent Traffic Analysis Report ===',
    `Total Messages: ${report.summary.total_messages}`,
    `Agents: ${report.summary.agents}`,
    `Communication Pairs: ${report.summary.communication_pairs}`,
    '',
    '--- Agent Statistics ---',
    ...report.agent_stats.map(a =>
      `${a.agent}: sent=${a.messages_sent} recv=${a.messages_received} avg_latency=${a.avg_latency_ms}ms error_rate=${a.error_rate}`
    ),
    '',
    '--- Top Bottlenecks ---',
    ...report.bottlenecks.map(b =>
      `${b.pair}: count=${b.message_count} avg_latency=${b.avg_latency_ms}ms error_rate=${b.error_rate}`
    ),
  ].join('\n');
}

if (outputFile) {
  fs.writeFileSync(outputFile, output);
  console.log(`Report written to ${outputFile}`);
} else {
  console.log(output);
}
EOF

RUN chmod +x /usr/local/lib/agent-traffic-analyzer/index.js && \
    ln -s /usr/local/lib/agent-traffic-analyzer/index.js /usr/local/bin/agent-traffic-analyzer

WORKDIR /workspace