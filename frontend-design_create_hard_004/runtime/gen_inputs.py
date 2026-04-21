import os

# Create a simple reference file for the artist's background
with open('artist_info.txt', 'w') as f:
    f.write('ALEX CHEN - DIGITAL ARTIST\n')
    f.write('Specializes in generative art and interactive installations\n')
    f.write('Based in San Francisco, California\n')
    f.write('Portfolio includes abstract compositions and data visualizations\n')

# Create placeholder project descriptions
projects = [
    'Neural Landscapes - Generative terrain visualization',
    'Data Symphony - Interactive sound visualization',
    'Fractal Dreams - Mathematical art series',
    'Urban Pulse - City rhythm interpretation'
]

with open('project_list.txt', 'w') as f:
    for i, project in enumerate(projects, 1):
        f.write(f'Project {i}: {project}\n')

print('Input files generated successfully')