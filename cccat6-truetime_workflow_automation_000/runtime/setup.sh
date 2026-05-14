#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Install the TrueTime skill scripts
SKILL_DIR="/opt/skills/truetime"
mkdir -p "$SKILL_DIR/scripts"

# Write the true_time.mjs script
cat > "$SKILL_DIR/scripts/true_time.mjs" << 'TRUETIME_EOF'
#!/usr/bin/env node
/**
 * TrueTime Helper Script
 * Provides deterministic time calculations for scheduling tasks.
 */
import { DateTime, Duration, Settings } from 'luxon';
import { createRequire } from 'module';
import { execSync } from 'child_process';
import * as dgram from 'dgram';

const args = process.argv.slice(2);

function getArg(flag, defaultVal = null) {
  const idx = args.indexOf(flag);
  if (idx !== -1 && idx + 1 < args.length) return args[idx + 1];
  return defaultVal;
}

function hasFlag(flag) {
  return args.includes(flag);
}

// --list-timezones
if (hasFlag('--list-timezones')) {
  // Output Luxon-compatible IANA timezones via Intl
  const zones = Intl.supportedValuesOf('timeZone');
  console.log(zones.join('\n'));
  process.exit(0);
}

const plusArg = getArg('--plus');
const targetArg = getArg('--target');
const targetTzArg = getArg('--target-tz');
const userTzArg = getArg('--user-tz', 'UTC');
const calendarTzArg = getArg('--calendar-tz');
const timeSource = getArg('--time-source', 'server');
const ntpServer = getArg('--ntp-server', 'pool.ntp.org');
const ntpTimeoutMs = parseInt(getArg('--ntp-timeout-ms', '3000'), 10);
const lunarTzArg = getArg('--lunar-tz', 'Asia/Shanghai');

// Chinese lunar calendar approximation
function getLunarDate(dt) {
  // Use a simple offset-based approximation for the lunar calendar
  // Reference: 2000-01-06 was lunar 2000-01-01 (New Year)
  const lunarEpoch = DateTime.fromISO('2000-01-06T00:00:00', { zone: lunarTzArg });
  const lunarMonthDays = [30,29,30,29,30,29,30,29,30,29,30,29]; // alternating approximation
  
  const localDt = dt.setZone(lunarTzArg);
  const diffDays = Math.floor(localDt.diff(lunarEpoch, 'days').days);
  
  let year = 2000;
  let remaining = diffDays;
  
  // Simple approximation: 354 days/lunar year
  while (remaining >= 354) { remaining -= 354; year++; }
  while (remaining < 0) { remaining += 354; year--; }
  
  let month = 1;
  let mlen = 30;
  while (remaining >= mlen) {
    remaining -= mlen;
    month++;
    mlen = (month % 2 === 0) ? 29 : 30;
    if (month > 12) { month = 1; year++; }
  }
  const day = remaining + 1;
  
  return `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
}

function parsePlusArg(plus) {
  // Parse compound duration strings like "1h30m", "2.5month", "1month2weeks"
  const unitMap = {
    'milliseconds': ['ms','msec','msecs','millisecond','milliseconds'],
    'seconds': ['s','sec','second','seconds'],
    'minutes': ['m','min','minute','minutes'],
    'hours': ['h','hr','hour','hours'],
    'days': ['d','day','days'],
    'weeks': ['w','week','weeks'],
    'months': ['mo','mon','month','months'],
    'years': ['y','yr','year','years'],
    'decades': ['decade','decades'],
    'centuries': ['century','centuries'],
  };
  
  const calendarUnits = new Set(['months','years','decades','centuries']);
  
  // Normalize comma decimals
  const normalized = plus.replace(/,/g, '.');
  
  // Match all value+unit tokens
  const tokenRe = /([0-9]*\.?[0-9]+)\s*(milliseconds|millisecond|msecs|msec|ms|seconds|second|sec|minutes|minute|min|hours|hour|hr|weeks|week|days|day|months|month|mon|mo|years|year|decades|decade|centuries|century|[ymhdws])/gi;
  
  const tokens = [];
  let match;
  while ((match = tokenRe.exec(normalized)) !== null) {
    const val = parseFloat(match[1]);
    const rawUnit = match[2].toLowerCase();
    let canonicalUnit = null;
    for (const [canon, aliases] of Object.entries(unitMap)) {
      if (aliases.includes(rawUnit)) { canonicalUnit = canon; break; }
    }
    if (!canonicalUnit) throw new Error(`Unknown unit: ${rawUnit}`);
    tokens.push({ val, unit: canonicalUnit });
  }
  
  if (tokens.length === 0) throw new Error(`Cannot parse duration: ${plus}`);
  
  return tokens;
}

function applyCalendarToken(dt, val, unit, calTz) {
  const workDt = calTz ? dt.setZone(calTz) : dt;
  let result;
  
  if (unit === 'decades') {
    const totalMonths = val * 120;
    return applyCalendarToken(dt, totalMonths, 'months', calTz);
  }
  if (unit === 'centuries') {
    const totalMonths = val * 1200;
    return applyCalendarToken(dt, totalMonths, 'months', calTz);
  }
  if (unit === 'years') {
    const totalMonths = val * 12;
    return applyCalendarToken(dt, totalMonths, 'months', calTz);
  }
  
  // months
  const intPart = Math.floor(val);
  const fracPart = val - intPart;
  
  // Integer month shift
  result = workDt.plus({ months: intPart });
  
  // Fractional: use shifted month length
  if (fracPart > 0) {
    const monthLenDays = result.daysInMonth;
    const fracMs = fracPart * monthLenDays * 24 * 60 * 60 * 1000;
    result = result.plus({ milliseconds: fracMs });
  }
  
  // Convert back to original zone
  return result.setZone(dt.zoneName);
}

async function getNtpTime(server, timeoutMs) {
  return new Promise((resolve, reject) => {
    const client = dgram.createSocket('udp4');
    const ntpMsg = Buffer.alloc(48);
    ntpMsg[0] = 0x1B; // NTP v3, client mode
    
    const timer = setTimeout(() => {
      client.close();
      reject(new Error(`NTP timeout after ${timeoutMs}ms from ${server}`));
    }, timeoutMs);
    
    client.send(ntpMsg, 0, 48, 123, server, (err) => {
      if (err) { clearTimeout(timer); client.close(); reject(err); }
    });
    
    client.on('message', (msg) => {
      clearTimeout(timer);
      client.close();
      // Transmit timestamp at bytes 40-47
      const intPart = msg.readUInt32BE(40);
      const fracPart = msg.readUInt32BE(44);
      // NTP epoch is 1900-01-01, Unix epoch is 1970-01-01 (diff = 2208988800)
      const unixSec = intPart - 2208988800;
      const ms = Math.round((fracPart / 0x100000000) * 1000);
      resolve(unixSec * 1000 + ms);
    });
    
    client.on('error', (err) => { clearTimeout(timer); reject(err); });
  });
}

async function main() {
  let nowMs;
  let usedNtpServer = null;
  
  if (timeSource === 'ntp') {
    const servers = ntpServer.split(',').map(s => s.trim());
    let ntpSuccess = false;
    for (const srv of servers) {
      try {
        nowMs = await getNtpTime(srv, ntpTimeoutMs);
        usedNtpServer = srv;
        ntpSuccess = true;
        break;
      } catch(e) {
        // try next
      }
    }
    if (!ntpSuccess) {
      console.error(JSON.stringify({ error: 'All NTP servers failed', servers }));
      process.exit(1);
    }
  } else {
    nowMs = Date.now();
  }
  
  const nowUtc = DateTime.fromMillis(nowMs, { zone: 'UTC' });
  
  let targetUtc;
  
  if (plusArg) {
    const tokens = parsePlusArg(plusArg);
    const calendarUnits = new Set(['months','years','decades','centuries']);
    
    let current = nowUtc;
    for (const { val, unit } of tokens) {
      if (calendarUnits.has(unit)) {
        const calTz = calendarTzArg || userTzArg;
        current = applyCalendarToken(current, val, unit, calTz);
      } else {
        // Fixed unit
        let ms;
        switch(unit) {
          case 'milliseconds': ms = val; break;
          case 'seconds': ms = val * 1000; break;
          case 'minutes': ms = val * 60 * 1000; break;
          case 'hours': ms = val * 3600 * 1000; break;
          case 'days': ms = val * 86400 * 1000; break;
          case 'weeks': ms = val * 7 * 86400 * 1000; break;
          default: ms = 0;
        }
        current = current.plus({ milliseconds: ms });
      }
    }
    targetUtc = current;
    
  } else if (targetArg) {
    if (targetArg.includes('Z') || targetArg.match(/[+-]\d{2}:\d{2}$/)) {
      targetUtc = DateTime.fromISO(targetArg, { setZone: true }).toUTC();
    } else {
      const tz = targetTzArg || userTzArg;
      targetUtc = DateTime.fromISO(targetArg, { zone: tz }).toUTC();
    }
  } else {
    console.error(JSON.stringify({ error: 'Must provide --plus or --target' }));
    process.exit(1);
  }
  
  const deltaMs = targetUtc.toMillis() - nowUtc.toMillis();
  
  const targetUserTz = targetUtc.setZone(userTzArg);
  const targetServerTz = targetUtc.setZone(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');
  
  const nowLunarDt = nowUtc.setZone(lunarTzArg);
  const targetLunarDt = targetUtc.setZone(lunarTzArg);
  
  const output = {
    time_source: timeSource,
    ntp_server: usedNtpServer,
    now_utc: nowUtc.toISO(),
    now_utc_epoch_ms: nowUtc.toMillis(),
    target_utc: targetUtc.toISO(),
    target_utc_epoch_ms: targetUtc.toMillis(),
    target_user_tz: targetUserTz.toISO(),
    target_user_tz_name: userTzArg,
    target_server_tz: targetServerTz.toISO(),
    delta_milliseconds: Math.round(deltaMs),
    delta_seconds: deltaMs / 1000,
    lunar_timezone: lunarTzArg,
    now_lunar: getLunarDate(nowUtc),
    target_lunar: getLunarDate(targetUtc),
  };
  
  console.log(JSON.stringify(output, null, 2));
}

main().catch(e => {
  console.error(JSON.stringify({ error: e.message }));
  process.exit(1);
});
TRUETIME_EOF

chmod +x "$SKILL_DIR/scripts/true_time.mjs"

# Install luxon for the skill script
cd "$SKILL_DIR" && npm init -y > /dev/null 2>&1 && npm install luxon > /dev/null 2>&1

# Create a skill manifest so the agent can discover the baseDir
cat > "$SKILL_DIR/SKILL.md" << 'EOF'
name: truetime
baseDir: /opt/skills/truetime
EOF

# Export baseDir into environment
echo "export TRUETIME_BASE=/opt/skills/truetime" >> /etc/bash.bashrc

# Make workspace accessible
chmod -R 755 "${WORKSPACE:-/workspace}"

echo "TrueTime skill installed at $SKILL_DIR"
echo "Test: node $SKILL_DIR/scripts/true_time.mjs --plus 1m --user-tz Asia/Shanghai"