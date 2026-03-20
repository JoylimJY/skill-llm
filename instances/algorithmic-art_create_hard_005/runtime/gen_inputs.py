#!/usr/bin/env python3
import os
import json

# Create templates directory and viewer.html template
os.makedirs('templates', exist_ok=True)

viewer_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generative Art Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&family=Lora:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* ANTHROPIC_BRANDING_MARKER - Keep all styling exactly as shown */
        :root {
            --claude-orange: #FF6B35;
            --claude-light: #FFF5F0;
            --claude-gray: #6B7280;
            --claude-dark: #1F2937;
        }
        body {
            margin: 0;
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
            display: flex;
            min-height: 100vh;
        }
        .container {
            display: flex;
            width: 100%;
        }
        .sidebar {
            width: 280px;
            background: rgba(255, 255, 255, 0.95);
            padding: 24px;
            box-shadow: 2px 0 12px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        .main-content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        h1 {
            font-family: 'Lora', serif;
            color: var(--claude-dark);
            margin-bottom: 24px;
            font-size: 24px;
            font-weight: 500;
        }
        .section {
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e7eb;
        }
        .control-group {
            margin-bottom: 16px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--claude-dark);
            font-size: 14px;
        }
        input[type="range"] {
            width: 100%;
            margin-bottom: 4px;
        }
        .value-display {
            font-size: 12px;
            color: var(--claude-gray);
        }
        button {
            background: var(--claude-orange);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-family: inherit;
            font-weight: 500;
            cursor: pointer;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        button:hover {
            background: #e55a2b;
        }
        .seed-controls {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        .seed-display {
            font-family: monospace;
            font-size: 18px;
            font-weight: 600;
            color: var(--claude-dark);
        }
    </style>
</head>
<body>
    <!-- TEMPLATE_STRUCTURE_MARKER - Keep exact HTML structure -->
    <div class="container">
        <div class="sidebar">
            <h1>Algorithmic Art</h1>
            
            <!-- SEED_SECTION_MARKER - Always include exactly as shown -->
            <div class="section">
                <label>Seed</label>
                <div class="seed-display" id="seed-display">12345</div>
                <div class="seed-controls">
                    <button onclick="previousSeed()">Prev</button>
                    <button onclick="nextSeed()">Next</button>
                    <button onclick="randomSeed()">Random</button>
                </div>
                <div style="margin-top: 12px;">
                    <input type="number" id="seed-input" placeholder="Jump to seed" style="width: 140px; padding: 4px;">
                    <button onclick="jumpToSeed()">Go</button>
                </div>
            </div>

            <!-- PARAMETERS_SECTION_MARKER - Replace with algorithm-specific controls -->
            <div class="section">
                <label>Parameters</label>
                <!-- ADD YOUR PARAMETER CONTROLS HERE -->
                <div class="control-group">
                    <label>Example Parameter</label>
                    <input type="range" id="example" min="1" max="100" value="50" oninput="updateParam('example', this.value)">
                    <span class="value-display" id="example-value">50</span>
                </div>
            </div>

            <!-- COLORS_SECTION_MARKER - Optional, include if needed -->
            <div class="section">
                <label>Colors</label>
                <!-- ADD COLOR CONTROLS IF NEEDED -->
            </div>

            <!-- ACTIONS_SECTION_MARKER - Always include exactly as shown -->
            <div class="section">
                <button onclick="regenerate()">Regenerate</button>
                <button onclick="resetParameters()">Reset</button>
                <button onclick="downloadPNG()">Download PNG</button>
            </div>
        </div>

        <div class="main-content">
            <div id="p5-container"></div>
        </div>
    </div>

    <script>
        // ALGORITHM_MARKER - Replace with your p5.js algorithm
        let params = {
            seed: 12345,
            example: 50
        };

        function setup() {
            let canvas = createCanvas(800, 800);
            canvas.parent('p5-container');
            randomSeed(params.seed);
            noiseSeed(params.seed);
        }

        function draw() {
            background(240);
            // YOUR ALGORITHM HERE
            fill(255, 100, 100);
            ellipse(width/2, height/2, params.example * 4);
        }

        // UI_HANDLERS_MARKER - Keep seed functions, add parameter handlers
        function updateParam(name, value) {
            params[name] = parseFloat(value);
            document.getElementById(name + '-value').textContent = value;
            redraw();
        }

        function previousSeed() {
            params.seed = Math.max(1, params.seed - 1);
            updateSeed();
        }

        function nextSeed() {
            params.seed += 1;
            updateSeed();
        }

        function randomSeed() {
            params.seed = Math.floor(Math.random() * 999999) + 1;
            updateSeed();
        }

        function jumpToSeed() {
            let newSeed = parseInt(document.getElementById('seed-input').value);
            if (newSeed && newSeed > 0) {
                params.seed = newSeed;
                updateSeed();
                document.getElementById('seed-input').value = '';
            }
        }

        function updateSeed() {
            randomSeed(params.seed);
            noiseSeed(params.seed);
            document.getElementById('seed-display').textContent = params.seed;
            redraw();
        }

        function regenerate() {
            updateSeed();
        }

        function resetParameters() {
            params.example = 50;
            document.getElementById('example').value = 50;
            document.getElementById('example-value').textContent = '50';
            redraw();
        }

        function downloadPNG() {
            save('algorithmic-art-' + params.seed + '.png');
        }
    </script>
</body>
</html>'''

with open('templates/viewer.html', 'w') as f:
    f.write(viewer_template)

# Create a marker file for evaluation
marker_content = {
    "task_type": "quantum_entanglement_art",
    "required_elements": [
        "algorithmic_philosophy",
        "interactive_html_artifact",
        "quantum_mechanics_theme",
        "particle_entanglement_visualization"
    ],
    "verification_markers": {
        "philosophy_marker": "QUANTUM_ENTANGLEMENT_PHILOSOPHY",
        "html_marker": "QUANTUM_ART_HTML",
        "p5js_marker": "QUANTUM_PARTICLES_CODE"
    }
}

with open('task_markers.json', 'w') as f:
    json.dump(marker_content, f, indent=2)

print("Input files generated successfully")