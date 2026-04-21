import os
import json

# Create mock Slack configuration
slack_config = {
    "channels": {
        "#dev-tools": "C1234567890"
    },
    "webhook_url": "https://hooks.slack.com/services/mock/webhook",
    "bot_token": "xoxb-mock-token"
}

with open('slack_config.json', 'w') as f:
    json.dump(slack_config, f, indent=2)

# Create sample Python files for testing the analyzer
os.makedirs('sample_code', exist_ok=True)

# Create a complex Python file with quality issues
complex_code = '''import os, sys, json

def complex_function(a,b,c,d,e):
    if a > 10:
        if b < 5:
            if c == 3:
                if d != 0:
                    if e > 100:
                        return a + b * c / d - e
                    else:
                        return a - b
                else:
                    return c
            else:
                return b
        else:
            return a
    else:
        return 0

class badNaming:
    def __init__(self):
        self.x=1
        self.y=2
    
    def calculate(self,val):
        result=0
        for i in range(val):
            if i%2==0:
                result+=i
        return result

print("This is a test file with quality issues")
'''

with open('sample_code/complex_module.py', 'w') as f:
    f.write(complex_code)

# Create a cleaner Python file
clean_code = '''"""A well-structured Python module."""


def calculate_sum(numbers):
    """Calculate the sum of a list of numbers."""
    return sum(numbers)


class DataProcessor:
    """A class for processing data."""
    
    def __init__(self, data=None):
        self.data = data or []
    
    def process(self):
        """Process the stored data."""
        return [x * 2 for x in self.data if x > 0]
'''

with open('sample_code/clean_module.py', 'w') as f:
    f.write(clean_code)

print("Generated input files for skill creation task")