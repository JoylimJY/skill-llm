import os

# Create a marker file to indicate the expected animation type
with open('animation_requirements.txt', 'w') as f:
    f.write('TASK_MARKER_STAR_BOUNCE_SPIN\n')
    f.write('Animation: star bouncing and spinning\n')
    f.write('Duration: under 2 seconds\n')
    f.write('Type: emoji (128x128 recommended)\n')
    f.write('Effects: colorful, sparkles\n')

print('Generated animation requirements file')