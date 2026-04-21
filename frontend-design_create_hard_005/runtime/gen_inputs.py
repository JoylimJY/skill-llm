import json
import os

# Create package.json for any potential npm dependencies
package_json = {
    "name": "alex-rivera-portfolio",
    "version": "1.0.0",
    "description": "Portfolio website for digital artist Alex Rivera",
    "dependencies": {},
    "devDependencies": {}
}

with open('package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

# Create artist bio content for reference
artist_bio = """
Alex Rivera is a pioneering digital artist whose work explores the intersection of technology, nature, and human consciousness. Born in Mexico City and based in Brooklyn, Rivera creates immersive generative art experiences that challenge traditional notions of artistic creation.

Their practice encompasses algorithmic sculptures, interactive installations, and data-driven visualizations that respond to environmental inputs. Rivera's work has been featured in galleries across North America and Europe, including the Whitney Museum, SFMOMA, and the Centre Pompidou.

Rivera holds an MFA in Digital Media from the Rhode Island School of Design and has been awarded residencies at NEW INC, Eyebeam, and the MacDowell Colony. They are currently developing a large-scale installation exploring climate data visualization for the Venice Biennale 2024.
"""

with open('artist_bio.txt', 'w') as f:
    f.write(artist_bio)

# Create artwork data for gallery
artworks = [
    {"title": "Neural Cascades", "year": "2023", "medium": "Generative Algorithm, LED Installation", "description": "An evolving neural network visualization that responds to gallery visitors' movements, creating cascading patterns of light and shadow."},
    {"title": "Data Streams", "year": "2023", "medium": "Real-time Data Visualization", "description": "A live visualization of internet traffic patterns, transforming digital information flow into organic, river-like forms."},
    {"title": "Quantum Garden", "year": "2022", "medium": "Interactive Projection", "description": "Visitors' biometric data generates unique digital flora that grows and evolves in real-time across gallery walls."},
    {"title": "Temporal Echoes", "year": "2022", "medium": "AR Installation", "description": "Augmented reality sculptures that exist only when viewed through mobile devices, exploring themes of digital permanence."},
    {"title": "Algorithmic Fossils", "year": "2021", "medium": "3D Printed Sculptures", "description": "Machine learning algorithms trained on paleontological data generate speculative future fossil forms."},
    {"title": "Frequency Paintings", "year": "2021", "medium": "Sound-Responsive Visuals", "description": "Audio frequencies from urban environments are translated into dynamic abstract compositions that shift throughout the day."}
]

with open('artworks.json', 'w') as f:
    json.dump(artworks, f, indent=2)

print("Input files generated successfully")