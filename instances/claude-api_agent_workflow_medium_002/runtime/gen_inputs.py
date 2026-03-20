#!/usr/bin/env python3
import os
from fpdf import FPDF
import random

# Set deterministic seed
random.seed(12345)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_research_paper(filename, title, authors, findings, methodology, limitations):
    pdf = PDF()
    pdf.title = title
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)
    
    # Authors
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Authors: {authors}', 0, 1)
    pdf.ln(5)
    
    # Abstract section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Abstract', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, f'This paper presents {findings}. The research utilized {methodology}.')
    pdf.ln(5)
    
    # Main Findings section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Main Findings', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, f'MARKER_FINDINGS: {findings}')
    pdf.ln(5)
    
    # Methodology section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Methodology', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, f'MARKER_METHODOLOGY: {methodology}')
    pdf.ln(5)
    
    # Limitations section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Limitations', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 8, f'MARKER_LIMITATIONS: {limitations}')
    
    pdf.output(filename)

# Create research papers with marker content
papers = [
    {
        'filename': 'machine_learning_healthcare.pdf',
        'title': 'Machine Learning Applications in Healthcare Diagnostics',
        'authors': 'Dr. Sarah Chen, Prof. Michael Rodriguez, Dr. Lisa Wang',
        'findings': 'Deep learning models achieved 94% accuracy in medical image classification, significantly outperforming traditional methods',
        'methodology': 'Convolutional neural networks trained on 50,000 medical images using transfer learning and data augmentation techniques',
        'limitations': 'Limited to specific imaging modalities and requires large datasets for optimal performance'
    },
    {
        'filename': 'natural_language_processing.pdf', 
        'title': 'Advances in Natural Language Processing for Scientific Literature',
        'authors': 'Prof. James Thompson, Dr. Emily Foster, Dr. Alex Kumar',
        'findings': 'Transformer-based models demonstrated superior performance in extracting structured information from scientific papers with 89% precision',
        'methodology': 'Fine-tuned BERT models on domain-specific scientific corpus using supervised learning with manual annotations',
        'limitations': 'Performance degrades on highly technical jargon and requires domain-specific training data'
    },
    {
        'filename': 'climate_modeling.pdf',
        'title': 'Climate Change Modeling Using Advanced Statistical Methods', 
        'authors': 'Dr. Maria Gonzalez, Prof. Robert Kim, Dr. Jennifer Adams',
        'findings': 'Novel ensemble methods improved climate prediction accuracy by 15% compared to baseline models over 10-year forecasts',
        'methodology': 'Bayesian ensemble modeling combining multiple climate simulation outputs with uncertainty quantification',
        'limitations': 'Computational complexity limits real-time applications and uncertainty increases with longer prediction horizons'
    }
]

for paper in papers:
    create_research_paper(**paper)

print('Generated 3 research papers with embedded marker content')