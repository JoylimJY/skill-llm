#!/usr/bin/env python3
import os

# Create templates directory structure
os.makedirs('templates', exist_ok=True)

# Create viewer.html template with required structure
viewer_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Algorithmic Art Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
    <style>
        /* FIXED: Keep exact Anthropic branding */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&family=Lora:wght@400;500&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: #2d3748;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        /* FIXED: Exact sidebar structure */
        .sidebar {
            width: 300px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 0, 0, 0.1);
            padding: 20px;
            overflow-y: auto;
        }
        
        .logo {
            font-family: 'Lora', serif;
            font-size: 24px;
            font-weight: 500;
            color: #1a202c;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #4a5568;
            margin-bottom: 15px;
        }
        
        /* VARIABLE: Replace parameter controls as needed */
        .control-group {
            margin-bottom: 15px;
        }
        
        .control-group label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: #2d3748;
            margin-bottom: 5px;
        }
        
        input[type="range"] {
            width: 100%;
            margin-bottom: 5px;
        }
        
        .value-display {
            font-size: 11px;
            color: #718096;
        }
        
        /* FIXED: Keep button styling */
        .btn {
            background: #4299e1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            margin: 2px;
        }
        
        .btn:hover {
            background: #3182ce;
        }
        
        .btn-group {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        #seed-display {
            font-family: 'Courier New', monospace;
            background: #edf2f7;
            padding: 8px;
            border-radius: 4px;
            text-align: center;
            margin-bottom: 10px;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- FIXED: Keep exact sidebar structure -->
        <div class="sidebar">
            <div class="logo">Algorithmic Art</div>
            
            <!-- FIXED: Seed section - always include -->
            <div class="section">
                <div class="section-title">Seed</div>
                <div id="seed-display">12345</div>
                <div class="btn-group">
                    <button class="btn" onclick="prevSeed()">Previous</button>
                    <button class="btn" onclick="nextSeed()">Next</button>
                    <button class="btn" onclick="randomSeed()">Random</button>
                </div>
                <div style="margin-top: 10px;">
                    <input type="number" id="seed-input" placeholder="Jump to seed" style="width: 70%; margin-right: 5px;">
                    <button class="btn" onclick="jumpToSeed()">Go</button>
                </div>
            </div>
            
            <!-- VARIABLE: Replace with actual parameters for each artwork -->
            <div class="section">
                <div class="section-title">Parameters</div>
                <!-- REPLACE THIS SECTION WITH ACTUAL PARAMETER CONTROLS -->
                <div class="control-group">
                    <label>Sample Parameter</label>
                    <input type="range" id="sample" min="1" max="100" step="1" value="50">
                    <span class="value-display">50</span>
                </div>
            </div>
            
            <!-- FIXED: Actions section - always include -->
            <div class="section">
                <div class="section-title">Actions</div>
                <div class="btn-group">
                    <button class="btn" onclick="regenerate()">Regenerate</button>
                    <button class="btn" onclick="resetParams()">Reset</button>
                    <button class="btn" onclick="downloadPNG()">Download PNG</button>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div id="canvas-container"></div>
        </div>
    </div>
    
    <script>
        // VARIABLE: Replace with actual algorithm
        let params = {
            seed: 12345,
            sampleParam: 50
        };
        
        // TEMPLATE MARKER: viewer_template_v1.0
        
        function setup() {
            let canvas = createCanvas(800, 800);
            canvas.parent('canvas-container');
            // REPLACE: Add actual algorithm setup
        }
        
        function draw() {
            // REPLACE: Add actual algorithm
            background(220);
            fill(0);
            textAlign(CENTER, CENTER);
            text('Replace with actual algorithm', width/2, height/2);
        }
        
        // FIXED: Keep these UI functions
        function prevSeed() {
            params.seed--;
            updateSeedDisplay();
            regenerate();
        }
        
        function nextSeed() {
            params.seed++;
            updateSeedDisplay();
            regenerate();
        }
        
        function randomSeed() {
            params.seed = Math.floor(Math.random() * 999999) + 1;
            updateSeedDisplay();
            regenerate();
        }
        
        function jumpToSeed() {
            let newSeed = parseInt(document.getElementById('seed-input').value);
            if (!isNaN(newSeed)) {
                params.seed = newSeed;
                updateSeedDisplay();
                regenerate();
            }
        }
        
        function updateSeedDisplay() {
            document.getElementById('seed-display').textContent = params.seed;
        }
        
        function regenerate() {
            randomSeed(params.seed);
            noiseSeed(params.seed);
            redraw();
        }
        
        function resetParams() {
            // VARIABLE: Reset to default parameter values
            params.sampleParam = 50;
            document.getElementById('sample').value = 50;
            regenerate();
        }
        
        function downloadPNG() {
            save('algorithmic_art_seed_' + params.seed + '.png');
        }
    </script>
</body>
</html>'''

with open('templates/viewer.html', 'w') as f:
    f.write(viewer_html)

print("Generated templates/viewer.html with required structure")
