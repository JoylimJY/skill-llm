import os
import json

# Create sample Python module to document
sample_code = '''"""Sample module for testing documentation generation.

This module contains utility functions for data processing.
"""

import math
from typing import List, Optional

class DataProcessor:
    """A class for processing various data types.
    
    Attributes:
        name (str): The name of the processor.
        version (str): Version of the processor.
    """
    
    def __init__(self, name: str, version: str = "1.0"):
        """Initialize the DataProcessor.
        
        Args:
            name (str): Name for this processor instance.
            version (str, optional): Version string. Defaults to "1.0".
        """
        self.name = name
        self.version = version
    
    def process_numbers(self, numbers: List[float]) -> dict:
        """Process a list of numbers and return statistics.
        
        Args:
            numbers (List[float]): List of numeric values to process.
            
        Returns:
            dict: Statistics including mean, median, and sum.
            
        Raises:
            ValueError: If the input list is empty.
        """
        if not numbers:
            raise ValueError("Input list cannot be empty")
        
        return {
            "mean": sum(numbers) / len(numbers),
            "median": sorted(numbers)[len(numbers) // 2],
            "sum": sum(numbers),
            "count": len(numbers)
        }

def calculate_area(radius: float) -> float:
    """Calculate the area of a circle.
    
    Args:
        radius (float): The radius of the circle.
        
    Returns:
        float: The calculated area.
        
    Raises:
        ValueError: If radius is negative.
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius ** 2

def format_text(text: str, uppercase: bool = False) -> str:
    """Format text with optional case conversion.
    
    Args:
        text (str): Input text to format.
        uppercase (bool, optional): Convert to uppercase. Defaults to False.
        
    Returns:
        str: Formatted text string.
    """
    formatted = text.strip()
    return formatted.upper() if uppercase else formatted.lower()
'''

# Write the sample Python file
with open('sample_module.py', 'w') as f:
    f.write(sample_code)

# Create a requirements file
with open('requirements.txt', 'w') as f:
    f.write('numpy>=1.20.0\nrequests>=2.25.0\npandas>=1.3.0\n')

print('Generated sample Python module for documentation testing')