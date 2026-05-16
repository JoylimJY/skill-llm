#!/bin/bash
set -e

# Create a mock flyai CLI that simulates realistic JSON responses
# This replaces the real npm package with a deterministic local mock

mkdir -p /usr/local/lib/flyai-mock

cat > /usr/local/lib/flyai-mock/flyai-cli.js << 'MOCK_CLI_EOF'
#!/usr/bin/env node

const args = process.argv.slice(2);

function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      if (i + 1 < args.length && !args[i+1].startsWith('--')) {
        result[key] = args[i+1];
        i++;
      } else {
        result[key] = true;
      }
    } else {
      result['_command'] = args[i];
    }
  }
  return result;
}

const parsed = parseArgs(args);
const command = parsed['_command'];

if (!command && (parsed['version'] || args[0] === '--version')) {
  console.log('flyai-cli version 2.0.0');
  process.exit(0);
}

if (command === 'fliggy-fast-search') {
  const query = parsed['query'] || '';
  if (query.toLowerCase().includes('visa')) {
    const output = {
      "status": "success",
      "query": query,
      "results": [
        {
          "title": "Japan Tourist Visa for Chinese Citizens",
          "summary": "Chinese citizens require a tourist visa. Single-entry, 3-year multi-entry, and 5-year multi-entry available. Apply at Japanese consulate with passport, bank statement, and confirmed itinerary.",
          "detailUrl": "https://www.fliggy.com/visa/japan/chinese-citizens-guide?ref=flyai_mock_001",
          "validityNote": "Standard processing: 5-7 business days. Express: 3 days.",
          "requiresDocs": ["Valid passport (6+ months validity)", "Bank statement (3 months)", "Travel itinerary", "Hotel confirmation", "Photo"]
        }
      ]
    };
    console.log(JSON.stringify(output, null, 2));
  } else {
    console.log(JSON.stringify({"status": "success", "results": []}, null, 2));
  }
  process.exit(0);
}

if (command === 'search-flight') {
  const origin = parsed['origin'] || '';
  const destination = parsed['destination'] || '';
  const depDate = parsed['dep-date'] || '2026-05-10';
  const sortType = parsed['sort-type'] || '3';

  if (!parsed['sort-type']) {
    // Missing required sort-type hint but still return data (agent must use sort-type 3)
  }

  let flights = [];

  const isOutbound = origin.toLowerCase().includes('beijing') || origin.toLowerCase().includes('bj') || origin.toLowerCase().includes('pek');
  const isReturn = destination.toLowerCase().includes('beijing') || destination.toLowerCase().includes('bj') || destination.toLowerCase().includes('pek');

  if (isOutbound) {
    flights = [
      {
        "flightNo": "CA181",
        "airline": "Air China",
        "origin": "Beijing PEK",
        "destination": "Tokyo NRT",
        "departureTime": depDate + "T08:30:00",
        "arrivalTime": depDate + "T13:45:00",
        "price": 2850,
        "currency": "CNY",
        "class": "Economy",
        "detailUrl": "https://www.fliggy.com/flight/CA181/PEK-NRT/" + depDate + "?ref=flyai_mock_flight_001",
        "sortScore": sortType === '3' ? 1 : 99
      },
      {
        "flightNo": "NH906",
        "airline": "ANA",
        "origin": "Beijing PEK",
        "destination": "Tokyo NRT",
        "departureTime": depDate + "T10:00:00",
        "arrivalTime": depDate + "T15:20:00",
        "price": 3200,
        "currency": "CNY",
        "class": "Economy",
        "detailUrl": "https://www.fliggy.com/flight/NH906/PEK-NRT/" + depDate + "?ref=flyai_mock_flight_002",
        "sortScore": sortType === '3' ? 2 : 98
      }
    ];
  } else if (isReturn) {
    flights = [
      {
        "flightNo": "MU524",
        "airline": "China Eastern",
        "origin": "Osaka KIX",
        "destination": "Beijing PEK",
        "departureTime": depDate + "T16:00:00",
        "arrivalTime": depDate + "T20:10:00",
        "price": 2650,
        "currency": "CNY",
        "class": "Economy",
        "detailUrl": "https://www.fliggy.com/flight/MU524/KIX-PEK/" + depDate + "?ref=flyai_mock_flight_003",
        "sortScore": sortType === '3' ? 1 : 99
      },
      {
        "flightNo": "JL822",
        "airline": "Japan Airlines",
        "origin": "Osaka KIX",
        "destination": "Beijing PEK",
        "departureTime": depDate + "T18:30:00",
        "arrivalTime": depDate + "T22:45:00",
        "price": 2980,
        "currency": "CNY",
        "class": "Economy",
        "detailUrl": "https://www.fliggy.com/flight/JL822/KIX-PEK/" + depDate + "?ref=flyai_mock_flight_004",
        "sortScore": sortType === '3' ? 2 : 98
      }
    ];
  } else {
    flights = [
      {
        "flightNo": "XX999",
        "airline": "Mock Airline",
        "origin": origin,
        "destination": destination,
        "departureTime": depDate + "T09:00:00",
        "arrivalTime": depDate + "T14:00:00",
        "price": 3000,
        "currency": "CNY",
        "class": "Economy",
        "detailUrl": "https://www.fliggy.com/flight/XX999/" + depDate + "?ref=flyai_mock_flight_005"
      }
    ];
  }

  console.log(JSON.stringify({"status": "success", "sortType": parseInt(sortType), "flights": flights}, null, 2));
  process.exit(0);
}

if (command === 'search-hotels') {
  const destName = parsed['dest-name'] || '';
  const checkIn = parsed['check-in-date'] || '2026-05-10';
  const checkOut = parsed['check-out-date'] || '2026-05-12';
  const sort = parsed['sort'] || '';
  const keywords = parsed['key-words'] || '';
  const maxPrice = parsed['max-price'] ? parseInt(parsed['max-price']) : 99999;

  let hotels = [];

  if (destName.toLowerCase().includes('tokyo')) {
    hotels = [
      {
        "hotelId": "TYO-001",
        "name": "Shinjuku Grand Hotel Tokyo",
        "address": "3-14-1 Shinjuku, Tokyo",
        "starRating": 4,
        "pricePerNight": 980,
        "currency": "CNY",
        "reviewScore": 4.7,
        "reviewCount": 3421,
        "detailUrl": "https://www.fliggy.com/hotel/shinjuku-grand-tokyo?checkin=" + checkIn + "&checkout=" + checkOut + "&ref=flyai_mock_hotel_001",
        "tags": ["Free WiFi", "Breakfast included", "Near subway"],
        "sortKey": sort === 'rate_desc' ? 4.7 : 980
      },
      {
        "hotelId": "TYO-002",
        "name": "Akihabara Tech Inn",
        "address": "2-1 Akihabara, Tokyo",
        "starRating": 3,
        "pricePerNight": 650,
        "currency": "CNY",
        "reviewScore": 4.3,
        "reviewCount": 1892,
        "detailUrl": "https://www.fliggy.com/hotel/akihabara-tech-inn?checkin=" + checkIn + "&checkout=" + checkOut + "&ref=flyai_mock_hotel_002",
        "tags": ["Free WiFi", "24hr Front Desk"],
        "sortKey": sort === 'rate_desc' ? 4.3 : 650
      }
    ];
  } else if (destName.toLowerCase().includes('osaka')) {
    hotels = [
      {
        "hotelId": "OSK-001",
        "name": "Namba Oriental Hotel Osaka",
        "address": "1-8-26 Namba, Osaka",
        "starRating": 4,
        "pricePerNight": 860,
        "currency": "CNY",
        "reviewScore": 4.8,
        "reviewCount": 5102,
        "detailUrl": "https://www.fliggy.com/hotel/namba-oriental-osaka?checkin=" + checkIn + "&checkout=" + checkOut + "&ref=flyai_mock_hotel_003",
        "tags": ["Free WiFi", "Near Dotonbori", "Breakfast available"],
        "sortKey": sort === 'rate_desc' ? 4.8 : 860
      },
      {
        "hotelId": "OSK-002",
        "name": "Shinsaibashi Business Hotel",
        "address": "4-2 Shinsaibashi, Osaka",
        "starRating": 3,
        "pricePerNight": 520,
        "currency": "CNY",
        "reviewScore": 4.1,
        "reviewCount": 2310,
        "detailUrl": "https://www.fliggy.com/hotel/shinsaibashi-business?checkin=" + checkIn + "&checkout=" + checkOut + "&ref=flyai_mock_hotel_004",
        "tags": ["Economy", "Central Location"],
        "sortKey": sort === 'rate_desc' ? 4.1 : 520
      }
    ];
  } else {
    hotels = [
      {
        "hotelId": "GEN-001",
        "name": "Generic Japan Hotel",
        "pricePerNight": 700,
        "currency": "CNY",
        "reviewScore": 4.0,
        "detailUrl": "https://www.fliggy.com/hotel/generic?ref=flyai_mock_hotel_005"
      }
    ];
  }

  // Apply max price filter
  hotels = hotels.filter(h => h.pricePerNight <= maxPrice);

  console.log(JSON.stringify({"status": "success", "sortBy": sort, "hotels": hotels}, null, 2));
  process.exit(0);
}

if (command === 'search-poi') {
  const cityName = parsed['city-name'] || '';
  const category = parsed['category'] || '';
  const keyword = parsed['keyword'] || '';
  const poiLevel = parsed['poi-level'] ? parseInt(parsed['poi-level']) : 0;

  let pois = [];

  if (cityName.toLowerCase().includes('tokyo')) {
    if (poiLevel >= 5) {
      pois = [
        {
          "poiId": "TYO-POI-001",
          "name": "Senso-ji Temple",
          "category": "宗教場所",
          "city": "Tokyo",
          "rating": 5,
          "reviewCount": 28450,
          "ticketPrice": 0,
          "description": "Tokyo's oldest and most famous Buddhist temple in Asakusa.",
          "detailUrl": "https://www.fliggy.com/poi/sensoji-temple-tokyo?ref=flyai_mock_poi_001",
          "openHours": "06:00-17:00"
        },
        {
          "poiId": "TYO-POI-002",
          "name": "Shibuya Sky Observatory",
          "category": "城市观光",
          "city": "Tokyo",
          "rating": 5,
          "reviewCount": 15320,
          "ticketPrice": 200,
          "description": "Panoramic rooftop observatory above Shibuya Scramble.",
          "detailUrl": "https://www.fliggy.com/poi/shibuya-sky-observatory?ref=flyai_mock_poi_002",
          "openHours": "09:00-22:30"
        },
        {
          "poiId": "TYO-POI-003",
          "name": "Meiji Shrine",
          "category": "宗教场所",
          "city": "Tokyo",
          "rating": 5,
          "reviewCount": 22100,
          "ticketPrice": 0,
          "description": "Serene Shinto shrine dedicated to Emperor Meiji in Harajuku forest.",
          "detailUrl": "https://www.fliggy.com/poi/meiji-shrine-tokyo?ref=flyai_mock_poi_003",
          "openHours": "Sunrise-Sunset"
        }
      ];
    } else {
      pois = [
        {
          "poiId": "TYO-POI-004",
          "name": "Ueno Park",
          "category": "自然风光",
          "city": "Tokyo",
          "rating": 4,
          "detailUrl": "https://www.fliggy.com/poi/ueno-park?ref=flyai_mock_poi_004"
        }
      ];
    }
  } else if (cityName.toLowerCase().includes('osaka')) {
    if (category === '市集' || category.includes('市集')) {
      pois = [
        {
          "poiId": "OSK-POI-001",
          "name": "Kuromon Market (Kuromon Ichiba)",
          "category": "市集",
          "city": "Osaka",
          "rating": 5,
          "reviewCount": 19870,
          "ticketPrice": 0,
          "description": "Osaka's famous 'Kitchen' market with 170+ stalls. Fresh seafood, street food.",
          "detailUrl": "https://www.fliggy.com/poi/kuromon-market-osaka?ref=flyai_mock_poi_005",
          "openHours": "08:00-18:00"
        },
        {
          "poiId": "OSK-POI-002",
          "name": "Dotonbori Food Street",
          "category": "市集",
          "city": "Osaka",
          "rating": 5,
          "reviewCount": 31200,
          "ticketPrice": 0,
          "description": "Iconic neon-lit entertainment and food district. Takoyaki, ramen, crab.",
          "detailUrl": "https://www.fliggy.com/poi/dotonbori-food-street?ref=flyai_mock_poi_006",
          "openHours": "10:00-24:00"
        }
      ];
    } else {
      pois = [
        {
          "poiId": "OSK-POI-003",
          "name": "Osaka Castle",
          "category": "历史古迹",
          "city": "Osaka",
          "rating": 5,
          "detailUrl": "https://www.fliggy.com/poi/osaka-castle?ref=flyai_mock_poi_007"
        }
      ];
    }
  } else if (cityName.toLowerCase().includes('kyoto')) {
    if (category === '宗教场所' || category.includes('宗教')) {
      pois = [
        {
          "poiId": "KYO-POI-001",
          "name": "Fushimi Inari Taisha",
          "category": "宗教场所",
          "city": "Kyoto",
          "rating": 5,
          "reviewCount": 42300,
          "ticketPrice": 0,
          "description": "Thousands of vermillion torii gates winding up Inari Mountain.",
          "detailUrl": "https://www.fliggy.com/poi/fushimi-inari-kyoto?ref=flyai_mock_poi_008",
          "openHours": "24 hours"
        },
        {
          "poiId": "KYO-POI-002",
          "name": "Kinkaku-ji (Golden Pavilion)",
          "category": "宗教场所",
          "city": "Kyoto",
          "rating": 5,
          "reviewCount": 38900,
          "ticketPrice": 80,
          "description": "Iconic Zen Buddhist temple covered in gold leaf, reflected in mirror pond.",
          "detailUrl": "https://www.fliggy.com/poi/kinkakuji-golden-pavilion?ref=flyai_mock_poi_009",
          "openHours": "09:00-17:00"
        }
      ];
    } else {
      pois = [
        {
          "poiId": "KYO-POI-003",
          "name": "Arashiyama Bamboo Grove",
          "category": "自然风光",
          "city": "Kyoto",
          "rating": 5,
          "detailUrl": "https://www.fliggy.com/poi/arashiyama-bamboo?ref=flyai_mock_poi_010"
        }
      ];
    }
  } else {
    pois = [
      {
        "poiId": "GEN-POI-001",
        "name": "Generic Attraction",
        "category": category,
        "rating": 4,
        "detailUrl": "https://www.fliggy.com/poi/generic?ref=flyai_mock_poi_999"
      }
    ];
  }

  console.log(JSON.stringify({"status": "success", "city": cityName, "category": category, "pois": pois}, null, 2));
  process.exit(0);
}

// Unknown command
console.error('Unknown command: ' + command);
process.exit(1);
MOCK_CLI_EOF

chmod +x /usr/local/lib/flyai-mock/flyai-cli.js

# Create the flyai wrapper that intercepts the npm global command
cat > /usr/local/bin/flyai << 'WRAPPER_EOF'
#!/bin/bash
node /usr/local/lib/flyai-mock/flyai-cli.js "$@"
WRAPPER_EOF

chmod +x /usr/local/bin/flyai

# Verify mock works
flyai --version

echo "Mock flyai CLI installed and verified."
echo "All commands ready: fliggy-fast-search, search-flight, search-hotels, search-poi"