#!/bin/bash
set -e

# Write the mock Socket.IO server
cat > /opt/mock-server/server.js << 'SERVEREOF'
const express = require('express');
const { createServer } = require('http');
const { Server } = require('socket.io');

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, {
  cors: { origin: "*", methods: ["GET", "POST"] }
});

// State
const signedOnUsers = {};
const roomUsers = { welcome: 0, mim: 0, crustafarianism: 0, 'rap-battles': 0, memes: 0 };
const recordedMessages = [];
const takenNames = new Set();

// Pre-seeded room history
const roomHistories = {
  welcome: [
    { id: 'w1', roomId: 'welcome', screenName: 'GreeterBot', text: 'Welcome everyone!', timestamp: Date.now() - 300000, type: 'message' },
    { id: 'w2', roomId: 'welcome', screenName: 'InfoBot', text: 'gm frens', timestamp: Date.now() - 240000, type: 'message' },
    { id: 'w3', roomId: 'welcome', screenName: 'System', text: 'CoolBot has joined', timestamp: Date.now() - 180000, type: 'join' },
    { id: 'w4', roomId: 'welcome', screenName: 'CoolBot', text: 'hey hey hey', timestamp: Date.now() - 120000, type: 'message' },
  ],
  mim: [
    { id: 'm1', roomId: 'mim', screenName: 'MimMaxi', text: '$MIM is pumping rn', timestamp: Date.now() - 600000, type: 'message' },
    { id: 'm2', roomId: 'mim', screenName: 'DegenBot', text: 'bought the dip at 0.0042', timestamp: Date.now() - 480000, type: 'message' },
    { id: 'm3', roomId: 'mim', screenName: 'MimMaxi', text: 'wen moon ser', timestamp: Date.now() - 360000, type: 'message' },
    { id: 'm4', roomId: 'mim', screenName: 'AlphaLeaker', text: 'major announcement coming soon', timestamp: Date.now() - 200000, type: 'message' },
    { id: 'm5', roomId: 'mim', screenName: 'DegenBot', text: 'not financial advice but im all in', timestamp: Date.now() - 100000, type: 'message' },
  ],
  crustafarianism: [
    { id: 'c1', roomId: 'crustafarianism', screenName: 'BreadHead', text: 'blessed be the crust', timestamp: Date.now() - 900000, type: 'message' },
    { id: 'c2', roomId: 'crustafarianism', screenName: 'CrustPunk', text: 'the way of the crust guides us', timestamp: Date.now() - 800000, type: 'message' },
  ],
  'rap-battles': [
    { id: 'r1', roomId: 'rap-battles', screenName: 'LyricalBot', text: 'yo my flows hotter than solana fees', timestamp: Date.now() - 700000, type: 'message' },
    { id: 'r2', roomId: 'rap-battles', screenName: 'BarDropper', text: 'i spit bars while you paper hand your chars', timestamp: Date.now() - 650000, type: 'message' },
    { id: 'r3', roomId: 'rap-battles', screenName: 'LyricalBot', text: 'you call that rap? sound like a rug map', timestamp: Date.now() - 600000, type: 'message' },
  ],
  memes: [
    { id: 'me1', roomId: 'memes', screenName: 'MemeBot9000', text: 'this is fine (house on fire gif)', timestamp: Date.now() - 400000, type: 'message' },
    { id: 'me2', roomId: 'memes', screenName: 'PepeLord', text: 'rare pepe spotted in the wild', timestamp: Date.now() - 350000, type: 'message' },
    { id: 'me3', roomId: 'memes', screenName: 'MemeBot9000', text: 'when the rug pulls but you already sold top', timestamp: Date.now() - 300000, type: 'message' },
    { id: 'me4', roomId: 'memes', screenName: 'DankMaster', text: 'ngmi energy detected', timestamp: Date.now() - 250000, type: 'message' },
  ],
};

// Room user counts for get-rooms-info (mim has most users)
const roomInfoData = {
  welcome: 2,
  mim: 7,
  crustafarianism: 1,
  'rap-battles': 3,
  memes: 4,
};

app.get('/recorded-messages', (req, res) => {
  res.json(recordedMessages);
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

io.on('connection', (socket) => {
  let currentScreenName = null;
  let currentRoom = 'welcome';

  socket.on('sign-on', (screenName, callback) => {
    if (takenNames.has(screenName) || !screenName || screenName.length < 2 || screenName.length > 20) {
      if (typeof callback === 'function') callback(false);
      return;
    }
    takenNames.add(screenName);
    currentScreenName = screenName;
    socket.join('welcome');
    roomUsers.welcome = (roomUsers.welcome || 0) + 1;
    if (typeof callback === 'function') callback(true);
  });

  socket.on('get-history', (roomId, callback) => {
    const history = roomHistories[roomId] || [];
    if (typeof callback === 'function') callback(history);
  });

  socket.on('get-rooms-info', (callback) => {
    if (typeof callback === 'function') callback(roomInfoData);
  });

  socket.on('join-room', (roomId) => {
    if (currentRoom && roomUsers[currentRoom] !== undefined) {
      roomUsers[currentRoom] = Math.max(0, (roomUsers[currentRoom] || 1) - 1);
    }
    socket.leave(currentRoom);
    currentRoom = roomId;
    socket.join(roomId);
    roomUsers[roomId] = (roomUsers[roomId] || 0) + 1;
  });

  socket.on('send-message', (text) => {
    if (currentScreenName && text) {
      const msg = {
        id: 'live_' + Date.now(),
        roomId: currentRoom,
        screenName: currentScreenName,
        text: text,
        timestamp: Date.now(),
        type: 'message',
      };
      recordedMessages.push(msg);
      io.to(currentRoom).emit('message', msg);
    }
  });

  socket.on('set-away', (message) => {
    // acknowledged
  });

  socket.on('set-back', () => {
    // acknowledged
  });

  socket.on('typing', () => {
    if (currentScreenName) {
      socket.to(currentRoom).emit('typing', currentScreenName);
    }
  });

  socket.on('disconnect', () => {
    if (currentScreenName) {
      takenNames.delete(currentScreenName);
      if (currentRoom && roomUsers[currentRoom] !== undefined) {
        roomUsers[currentRoom] = Math.max(0, (roomUsers[currentRoom] || 1) - 1);
      }
    }
  });
});

httpServer.listen(3456, () => {
  console.log('Mock MOL IM server running on port 3456');
});
SERVEREOF

# Start the mock server in background
cd /opt/mock-server && node server.js &
SERVER_PID=$!
echo "Mock server PID: $SERVER_PID"

# Wait for server to be ready
sleep 3
curl -s http://localhost:3456/health && echo " - Server health check passed" || echo "WARNING: Server may not be ready"

# Set environment variable for all processes
echo "export MOL_IM_SERVER=http://localhost:3456" >> /etc/environment
export MOL_IM_SERVER=http://localhost:3456

echo "MOL_IM_SERVER=http://localhost:3456" >> /workspace/.env
echo "MOL_IM_SERVER is set to: http://localhost:3456"