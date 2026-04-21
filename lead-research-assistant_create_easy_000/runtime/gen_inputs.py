import json

# Generate deterministic mock data files for companies and decision makers
# These files simulate databases to help the skill identify leads

companies = [
    {
        "name": "CollabTech Solutions",
        "website": "https://www.collabtech.com",
        "industry": "SaaS",
        "location": "New York",
        "size": 120,
        "pain_points": ["project collaboration", "internal communication"],
        "decision_maker": {
            "role": "VP of Product",
            "linkedin": "https://linkedin.com/in/janedoe"
        }
    },
    {
        "name": "Streamline Apps",
        "website": "https://www.streamlineapps.com",
        "industry": "Software",
        "location": "San Francisco",
        "size": 75,
        "pain_points": ["team productivity", "remote collaboration"],
        "decision_maker": {
            "role": "Head of Engineering",
            "linkedin": "https://linkedin.com/in/johnsmith"
        }
    },
    {
        "name": "TechNova",
        "website": "https://www.technova.com",
        "industry": "SaaS",
        "location": "New York",
        "size": 180,
        "pain_points": ["project visibility", "cross-team syncing"],
        "decision_maker": {
            "role": "Director of Operations",
            "linkedin": "https://linkedin.com/in/alexjohnson"
        }
    },
    {
        "name": "CodeCrafters",
        "website": "https://www.codecrafters.com",
        "industry": "Software",
        "location": "San Francisco",
        "size": 60,
        "pain_points": ["workflow bottlenecks", "deadline management"],
        "decision_maker": {
            "role": "CTO",
            "linkedin": "https://linkedin.com/in/emilywong"
        }
    },
    {
        "name": "BrightApps",
        "website": "https://www.brightapps.com",
        "industry": "SaaS",
        "location": "New York",
        "size": 90,
        "pain_points": ["collaboration tools", "project coordination"],
        "decision_maker": {
            "role": "Product Manager",
            "linkedin": "https://linkedin.com/in/michaelbrown"
        }
    }
]

# Save as JSON input data file
with open('mock_companies.json', 'w') as f:
    json.dump(companies, f, indent=2)

# Also create a README.txt with marker for verification
with open('README.txt', 'w') as f:
    f.write('Mock companies data for lead research skill testing. [MARKER-COMPANIES-DATA]\n')
