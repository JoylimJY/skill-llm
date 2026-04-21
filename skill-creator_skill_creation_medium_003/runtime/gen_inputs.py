import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Create sample research paper PDF
styles = getSampleStyleSheet()
doc = SimpleDocTemplate('sample_paper.pdf', pagesize=letter)
story = []

# Title
title = Paragraph('The Effects of Machine Learning on Data Processing Efficiency', styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

# Authors
authors = Paragraph('Dr. Jane Smith, Prof. John Doe', styles['Normal'])
story.append(authors)
story.append(Spacer(1, 12))

# Abstract
abstract_title = Paragraph('Abstract', styles['Heading1'])
story.append(abstract_title)
abstract_text = Paragraph('This study examines the impact of machine learning algorithms on data processing efficiency. We conducted experiments using 1000 datasets and found a 45% improvement in processing speed when using neural networks compared to traditional methods. The results indicate significant potential for automation in data analysis workflows.', styles['Normal'])
story.append(abstract_text)
story.append(Spacer(1, 12))

# Methodology
methodology_title = Paragraph('Methodology', styles['Heading1'])
story.append(methodology_title)
methodology_text = Paragraph('We used a controlled experimental design with three groups: traditional algorithms, decision trees, and neural networks. Each group processed the same 1000 datasets measuring execution time and accuracy metrics.', styles['Normal'])
story.append(methodology_text)
story.append(Spacer(1, 12))

# Results
results_title = Paragraph('Results', styles['Heading1'])
story.append(results_title)
results_text = Paragraph('Neural networks showed 45% faster processing times with 92% accuracy. Decision trees achieved 25% improvement with 88% accuracy. Traditional algorithms maintained baseline performance with 85% accuracy.', styles['Normal'])
story.append(results_text)
story.append(Spacer(1, 12))

# Conclusions
conclusions_title = Paragraph('Conclusions', styles['Heading1'])
story.append(conclusions_title)
conclusions_text = Paragraph('Machine learning significantly improves data processing efficiency. Neural networks provide the best performance gains while maintaining high accuracy levels.', styles['Normal'])
story.append(conclusions_text)

doc.build(story)

# Create a second sample paper
doc2 = SimpleDocTemplate('climate_study.pdf', pagesize=letter)
story2 = []

title2 = Paragraph('Climate Change Impacts on Arctic Wildlife Populations', styles['Title'])
story2.append(title2)
story2.append(Spacer(1, 12))

authors2 = Paragraph('Dr. Sarah Johnson, Dr. Michael Chen', styles['Normal'])
story2.append(authors2)
story2.append(Spacer(1, 12))

abstract2_title = Paragraph('Abstract', styles['Heading1'])
story2.append(abstract2_title)
abstract2_text = Paragraph('This longitudinal study tracked Arctic wildlife populations from 2010-2023. We observed a 30% decline in polar bear populations and 25% reduction in seal colonies. Temperature increases of 2.5°C correlate strongly with habitat loss.', styles['Normal'])
story2.append(abstract2_text)
story2.append(Spacer(1, 12))

methodology2_title = Paragraph('Methodology', styles['Heading1'])
story2.append(methodology2_title)
methodology2_text = Paragraph('We conducted annual population surveys using satellite tracking and field observations across 15 Arctic regions. Temperature data was collected from weather stations and analyzed for correlation patterns.', styles['Normal'])
story2.append(methodology2_text)
story2.append(Spacer(1, 12))

results2_title = Paragraph('Results', styles['Heading1'])
story2.append(results2_title)
results2_text = Paragraph('Population data shows consistent decline: polar bears decreased from 26,000 to 18,200 individuals. Seal populations dropped from 150,000 to 112,500. Temperature correlation coefficient: r=0.87.', styles['Normal'])
story2.append(results2_text)
story2.append(Spacer(1, 12))

conclusions2_title = Paragraph('Conclusions', styles['Heading1'])
story2.append(conclusions2_title)
conclusions2_text = Paragraph('Climate change significantly threatens Arctic wildlife. Immediate conservation efforts are needed to prevent further population declines.', styles['Normal'])
story2.append(conclusions2_text)

doc2.build(story2)

print('Generated sample_paper.pdf and climate_study.pdf')