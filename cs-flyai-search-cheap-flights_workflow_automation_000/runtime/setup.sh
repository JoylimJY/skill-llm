#!/usr/bin/env bash
set -e

# ── Install flyai-cli mock ────────────────────────────────────────────────────
# We create a realistic mock of the flyai CLI that returns JSON matching
# the structure the SKILL.md expects (with both detailUrl and jumpUrl to trap
# agents who use the deprecated jumpUrl).

mkdir -p /usr/local/lib/flyai-mock

cat > /usr/local/lib/flyai-mock/flyai-cli.js << 'JSEOF'
#!/usr/bin/env node
"use strict";

const args = process.argv.slice(2);

function getArg(name) {
  const idx = args.indexOf(name);
  if (idx !== -1 && args[idx + 1] !== undefined) return args[idx + 1];
  return null;
}

if (args[0] === '--version') {
  console.log('flyai-cli v2.0.0');
  process.exit(0);
}

if (args[0] === 'search-flight') {
  const origin = getArg('--origin') || 'Unknown';
  const destination = getArg('--destination') || 'Unknown';
  const sortType = getArg('--sort-type');
  const maxPrice = getArg('--max-price') ? parseInt(getArg('--max-price')) : 9999;
  const depHourStart = getArg('--dep-hour-start') ? parseInt(getArg('--dep-hour-start')) : null;
  const depDateStart = getArg('--dep-date-start');
  const depDateEnd = getArg('--dep-date-end');
  const depDate = getArg('--dep-date');

  // Simulated flight data pool
  const allFlights = [
    {
      flightNo: "9C8841",
      airline: "Spring Airlines",
      departureTime: "06:20",
      arrivalTime: "09:35",
      duration: "3h15m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 680,
      depDate: depDateStart || depDate || "2025-11-09",
      departureHour: 6,
      detailUrl: "https://www.fliggy.com/detail/9C8841-CTU-SYX-20251109",
      jumpUrl: "https://www.fliggy.com/jump/9C8841-DEPRECATED"
    },
    {
      flightNo: "CZ6401",
      airline: "China Southern",
      departureTime: "07:45",
      arrivalTime: "11:10",
      duration: "3h25m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 790,
      depDate: depDateStart || depDate || "2025-11-10",
      departureHour: 7,
      detailUrl: "https://www.fliggy.com/detail/CZ6401-CTU-SYX-20251110",
      jumpUrl: "https://www.fliggy.com/jump/CZ6401-DEPRECATED"
    },
    {
      flightNo: "MU5613",
      airline: "China Eastern",
      departureTime: "10:30",
      arrivalTime: "14:05",
      duration: "3h35m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 870,
      depDate: depDateStart || depDate || "2025-11-11",
      departureHour: 10,
      detailUrl: "https://www.fliggy.com/detail/MU5613-CTU-SYX-20251111",
      jumpUrl: "https://www.fliggy.com/jump/MU5613-DEPRECATED"
    },
    {
      flightNo: "CA4521",
      airline: "Air China",
      departureTime: "13:20",
      arrivalTime: "17:50",
      duration: "4h30m",
      stops: 1,
      transferCity: "Guangzhou",
      transferWait: "1h10m",
      price: 950,
      depDate: depDateStart || depDate || "2025-11-12",
      departureHour: 13,
      detailUrl: "https://www.fliggy.com/detail/CA4521-CTU-CAN-SYX-20251112",
      jumpUrl: "https://www.fliggy.com/jump/CA4521-DEPRECATED"
    },
    {
      flightNo: "HU7821",
      airline: "Hainan Airlines",
      departureTime: "16:00",
      arrivalTime: "19:20",
      duration: "3h20m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 1050,
      depDate: depDateStart || depDate || "2025-11-13",
      departureHour: 16,
      detailUrl: "https://www.fliggy.com/detail/HU7821-CTU-SYX-20251113",
      jumpUrl: "https://www.fliggy.com/jump/HU7821-DEPRECATED"
    },
    {
      flightNo: "9C8899",
      airline: "Spring Airlines",
      departureTime: "22:10",
      arrivalTime: "01:30+1",
      duration: "3h20m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 520,
      depDate: depDateStart || depDate || "2025-11-09",
      departureHour: 22,
      detailUrl: "https://www.fliggy.com/detail/9C8899-CTU-SYX-REDEYE-20251109",
      jumpUrl: "https://www.fliggy.com/jump/9C8899-DEPRECATED"
    },
    {
      flightNo: "ZH9032",
      airline: "Shenzhen Airlines",
      departureTime: "23:50",
      arrivalTime: "03:20+1",
      duration: "3h30m",
      stops: 0,
      transferCity: null,
      transferWait: null,
      price: 490,
      depDate: depDateStart || depDate || "2025-11-10",
      departureHour: 23,
      detailUrl: "https://www.fliggy.com/detail/ZH9032-CTU-SYX-REDEYE-20251110",
      jumpUrl: "https://www.fliggy.com/jump/ZH9032-DEPRECATED"
    }
  ];

  // Filter by max price
  let flights = allFlights.filter(f => f.price <= maxPrice);

  // Filter by departure hour for red-eye (dep-hour-start >= 21)
  if (depHourStart !== null) {
    flights = flights.filter(f => f.departureHour >= depHourStart);
  }

  // Sort by price ascending if sort-type = 3
  if (sortType === '3') {
    flights.sort((a, b) => a.price - b.price);
  }

  const result = {
    status: "success",
    searchParams: {
      origin: origin,
      destination: destination,
      sortType: sortType,
      maxPrice: maxPrice,
      depHourStart: depHourStart,
      depDateStart: depDateStart,
      depDateEnd: depDateEnd,
      depDate: depDate
    },
    totalResults: flights.length,
    flights: flights
  };

  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

console.error("Unknown command: " + args[0]);
process.exit(1);
JSEOF

chmod +x /usr/local/lib/flyai-mock/flyai-cli.js

# Create symlink so `flyai` is available globally
ln -sf /usr/local/lib/flyai-mock/flyai-cli.js /usr/local/bin/flyai
chmod +x /usr/local/bin/flyai

# Verify mock works
flyai --version

echo "Mock flyai-cli installed and verified."
echo "Workspace ready."