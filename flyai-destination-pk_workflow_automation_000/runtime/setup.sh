#!/bin/bash
set -e

echo "=== Setting up mock flyai CLI ==="

# Create a mock flyai CLI that returns realistic data based on the destination
MOCK_DIR="/usr/local/lib/mock-flyai"
mkdir -p "$MOCK_DIR"

# Create the mock flyai CLI script
cat > "$MOCK_DIR/flyai-mock.js" << 'MOCKSCRIPT'
#!/usr/bin/env node
const args = process.argv.slice(2);
const command = args[0];
const subcommand = args[1];

function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      if (i + 1 < args.length && !args[i + 1].startsWith('--')) {
        result[key] = args[i + 1];
        i++;
      } else {
        result[key] = true;
      }
    }
  }
  return result;
}

const params = parseArgs(args.slice(2));

if (args[0] === '--help') {
  console.log('FlyAI CLI v2.1.0');
  console.log('Usage: flyai <command> [options]');
  console.log('Commands: search-flight, search-hotel, search-poi, keyword-search');
  process.exit(0);
}

if (args[0] === 'search-flight') {
  const dest = params['destination'] || params['dest'] || 'unknown';
  const origin = params['origin'] || '北京';
  const depDate = params['dep-date'] || '2024-10-15';
  const backDate = params['back-date'] || '2024-10-20';
  const sortType = params['sort-type'];

  // Mock data per destination
  const flightData = {
    '东京': {
      flights: [
        { flight_no: 'CA837', airline: '中国国际航空', price: 2680, duration: '3h30m', direct: true, dep_time: '08:00', arr_time: '12:30' },
        { flight_no: 'MU737', airline: '东方航空', price: 2450, duration: '3h35m', direct: true, dep_time: '10:30', arr_time: '15:05' },
        { flight_no: 'NH926', airline: '全日空', price: 3100, duration: '3h25m', direct: true, dep_time: '14:00', arr_time: '18:25' },
        { flight_no: 'JL782', airline: '日本航空', price: 2950, duration: '3h30m', direct: true, dep_time: '16:00', arr_time: '20:30' },
      ],
      price_range: { min: 2450, max: 3100 },
      direct_available: true,
      avg_duration: '3h30m'
    },
    '首尔': {
      flights: [
        { flight_no: 'KE852', airline: '大韩航空', price: 1580, duration: '2h10m', direct: true, dep_time: '07:30', arr_time: '11:40' },
        { flight_no: 'OZ723', airline: '韩亚航空', price: 1420, duration: '2h15m', direct: true, dep_time: '09:00', arr_time: '13:15' },
        { flight_no: 'CA881', airline: '中国国际航空', price: 1680, duration: '2h05m', direct: true, dep_time: '11:30', arr_time: '15:35' },
        { flight_no: 'MU5033', airline: '东方航空', price: 1350, duration: '2h20m', direct: true, dep_time: '15:00', arr_time: '19:20' },
      ],
      price_range: { min: 1350, max: 1680 },
      direct_available: true,
      avg_duration: '2h10m'
    },
    '新加坡': {
      flights: [
        { flight_no: 'SQ802', airline: '新加坡航空', price: 2980, duration: '6h20m', direct: true, dep_time: '01:30', arr_time: '07:50' },
        { flight_no: 'CA837', airline: '中国国际航空', price: 2650, duration: '6h30m', direct: true, dep_time: '09:00', arr_time: '16:30' },
        { flight_no: 'MU557', airline: '东方航空', price: 2480, duration: '6h45m', direct: true, dep_time: '11:00', arr_time: '18:45' },
        { flight_no: '3U8753', airline: '四川航空', price: 2200, duration: '8h15m', direct: false, stops: '昆明', dep_time: '07:00', arr_time: '18:15' },
      ],
      price_range: { min: 2200, max: 2980 },
      direct_available: true,
      avg_duration: '6h30m'
    }
  };

  const data = flightData[dest] || flightData['东京'];
  const output = {
    status: 'success',
    origin: origin,
    destination: dest,
    dep_date: depDate,
    back_date: backDate,
    total_found: data.flights.length,
    price_range: data.price_range,
    direct_flight_available: data.direct_available,
    avg_duration: data.avg_duration,
    flights: data.flights
  };
  console.log(JSON.stringify(output, null, 2));

} else if (args[0] === 'search-hotel') {
  const dest = params['dest-name'] || 'unknown';
  const checkIn = params['check-in-date'] || '2024-10-15';
  const checkOut = params['check-out-date'] || '2024-10-20';
  const sort = params['sort'];

  const hotelData = {
    '东京': {
      hotels: [
        { name: '东京新宿格兰贝尔酒店', stars: 4, rating: 4.8, price_per_night: 880, reviews: 2341 },
        { name: '东京池袋大都会大饭店', stars: 5, rating: 4.9, price_per_night: 1280, reviews: 1876 },
        { name: '东京浅草阿里夫特酒店', stars: 4, rating: 4.7, price_per_night: 750, reviews: 3102 },
        { name: '东京品川王子大饭店', stars: 4, rating: 4.6, price_per_night: 690, reviews: 2567 },
        { name: '东京涩谷卓越大和ROYNET酒店', stars: 3, rating: 4.5, price_per_night: 480, reviews: 1893 },
        { name: '东京新宿汇聚商务酒店', stars: 3, rating: 4.2, price_per_night: 320, reviews: 987 },
      ],
      price_range: { min: 320, max: 1280 },
      high_rating_count: 5,
      avg_price: 733
    },
    '首尔': {
      hotels: [
        { name: '首尔乐天酒店', stars: 5, rating: 4.9, price_per_night: 980, reviews: 3421 },
        { name: '首尔明洞诺富特大使酒店', stars: 4, rating: 4.7, price_per_night: 620, reviews: 2876 },
        { name: '首尔弘大格拉斯金酒店', stars: 4, rating: 4.8, price_per_night: 450, reviews: 4102 },
        { name: '首尔江南格兰德洲际酒店', stars: 5, rating: 4.8, price_per_night: 880, reviews: 1567 },
        { name: '首尔仁寺洞温德汉姆花园酒店', stars: 4, rating: 4.6, price_per_night: 380, reviews: 2193 },
        { name: '首尔弘大西面超级8酒店', stars: 3, rating: 4.3, price_per_night: 250, reviews: 1287 },
        { name: '首尔新村林布酒店', stars: 3, rating: 4.1, price_per_night: 180, reviews: 876 },
      ],
      price_range: { min: 180, max: 980 },
      high_rating_count: 6,
      avg_price: 534
    },
    '新加坡': {
      hotels: [
        { name: '新加坡滨海湾金沙酒店', stars: 5, rating: 4.9, price_per_night: 2800, reviews: 8932 },
        { name: '新加坡乌节路希尔顿酒店', stars: 5, rating: 4.8, price_per_night: 1560, reviews: 4321 },
        { name: '新加坡克拉码头宜必思酒店', stars: 3, rating: 4.6, price_per_night: 580, reviews: 3102 },
        { name: '新加坡武吉士温德汉姆酒店', stars: 4, rating: 4.7, price_per_night: 780, reviews: 2567 },
        { name: '新加坡小印度美居酒店', stars: 4, rating: 4.5, price_per_night: 620, reviews: 1893 },
        { name: '新加坡圣淘沙名胜世界节日酒店', stars: 4, rating: 4.7, price_per_night: 950, reviews: 2341 },
      ],
      price_range: { min: 580, max: 2800 },
      high_rating_count: 5,
      avg_price: 1048
    }
  };

  const data = hotelData[dest] || hotelData['东京'];
  const output = {
    status: 'success',
    destination: dest,
    check_in: checkIn,
    check_out: checkOut,
    total_found: data.hotels.length,
    price_range: data.price_range,
    high_rating_count: data.high_rating_count,
    avg_price_per_night: data.avg_price,
    hotels: data.hotels
  };
  console.log(JSON.stringify(output, null, 2));

} else if (args[0] === 'search-poi') {
  const city = params['city-name'] || 'unknown';
  const level = params['poi-level'];

  const poiData = {
    '东京': {
      total: 68,
      categories: {
        '寺庙古迹类': { count: 18, pois: ['浅草寺', '明治神宫', '上野东照宫', '增上寺', '日枝神社', '靖国神社'] },
        '自然风光类': { count: 12, pois: ['上野公园', '新宿御苑', '昭和纪念公园', '高尾山', '井之头恩赐公园'] },
        '网红打卡类': { count: 22, pois: ['涩谷十字路口', '秋叶原电器街', '原宿竹下通', '东京晴空塔', '台场海滨公园', '银座购物街'] },
        '水上活动类': { count: 3, pois: ['台场海水浴场', '隅田川游船', '东京湾夜景游'] },
        '亲子娱乐类': { count: 13, pois: ['东京迪士尼乐园', '东京迪士尼海洋', '上野动物园', '东京国立科学博物馆'] }
      }
    },
    '首尔': {
      total: 54,
      categories: {
        '寺庙古迹类': { count: 14, pois: ['景福宫', '昌德宫', '宗庙', '南大门市场', '北村韩屋村', '水原华城'] },
        '自然风光类': { count: 10, pois: ['南山公园', '北汉山国立公园', '汉江公园', '仁王山'] },
        '网红打卡类': { count: 18, pois: ['明洞购物街', '弘大街区', '东大门设计广场', '益善洞韩屋村', '圣水洞咖啡街', 'N首尔塔'] },
        '水上活动类': { count: 4, pois: ['汉江游船', '济州岛潜水', '汉江皮划艇', '杨水里水上公园'] },
        '亲子娱乐类': { count: 8, pois: ['乐天世界', '韩国民俗村', '首尔动物园', '科学技术馆'] }
      }
    },
    '新加坡': {
      total: 61,
      categories: {
        '寺庙古迹类': { count: 10, pois: ['圣安德烈大教堂', '兴都庙', '斯里马里安曼庙', '佛牙寺龙华院', '天福宫'] },
        '自然风光类': { count: 15, pois: ['滨海湾花园', '新加坡植物园', '双溪布洛湿地保护区', '武吉知马自然保护区', '麦里芝蓄水池'] },
        '网红打卡类': { count: 20, pois: ['鱼尾狮公园', '克拉码头', '牛车水唐人街', '小印度', '芽笼士乃夜市', '滨海湾金沙空中花园'] },
        '水上活动类': { count: 10, pois: ['圣淘沙岛', '环球影城水世界', '椰子滩', '西乐索海滩', '帕劳潜水'] },
        '亲子娱乐类': { count: 6, pois: ['新加坡动物园', '夜间野生动物园', '新加坡科学馆', '环球影城'] }
      }
    }
  };

  const data = poiData[city] || poiData['东京'];
  const output = {
    status: 'success',
    city: city,
    total_poi: data.total,
    categories: data.categories
  };
  console.log(JSON.stringify(output, null, 2));

} else if (args[0] === 'keyword-search') {
  const query = params['query'] || '';
  const output = {
    status: 'success',
    query: query,
    results: [
      { title: `${query} - 相关信息`, summary: '相关信息摘要', url: 'https://example.com' }
    ]
  };
  console.log(JSON.stringify(output, null, 2));

} else {
  console.error(`Unknown command: ${args[0]}`);
  console.error('Usage: flyai <command> [options]');
  console.error('Commands: search-flight, search-hotel, search-poi, keyword-search');
  process.exit(1);
}
MOCKSCRIPT

chmod +x "$MOCK_DIR/flyai-mock.js"

# Create the mock npm package structure for @fly-ai/flyai-cli
MOCK_PKG_DIR="/usr/local/lib/mock-flyai-pkg"
mkdir -p "$MOCK_PKG_DIR"

cat > "$MOCK_PKG_DIR/package.json" << 'PKGJSON'
{
  "name": "@fly-ai/flyai-cli",
  "version": "2.1.0",
  "description": "FlyAI CLI mock for testing",
  "bin": {
    "flyai": "./bin/flyai.js"
  },
  "main": "index.js"
}
PKGJSON

mkdir -p "$MOCK_PKG_DIR/bin"
cp "$MOCK_DIR/flyai-mock.js" "$MOCK_PKG_DIR/bin/flyai.js"
chmod +x "$MOCK_PKG_DIR/bin/flyai.js"

cat > "$MOCK_PKG_DIR/index.js" << 'INDEXJS'
// FlyAI CLI mock package
module.exports = {};
INDEXJS

# Install the mock package globally by linking
mkdir -p /usr/local/lib/node_modules/@fly-ai
ln -sf "$MOCK_PKG_DIR" /usr/local/lib/node_modules/@fly-ai/flyai-cli

# Create the flyai binary symlink in PATH
ln -sf "$MOCK_PKG_DIR/bin/flyai.js" /usr/local/bin/flyai
chmod +x /usr/local/bin/flyai

echo "Mock flyai CLI installed at /usr/local/bin/flyai"
flyai --help

# Also intercept npm install for the specific package to be a no-op success
# by pre-installing it (npm will see it as already installed)
cd /usr/local/lib/node_modules/@fly-ai/flyai-cli && npm install --ignore-scripts 2>/dev/null || true

echo "=== Setup complete ==="