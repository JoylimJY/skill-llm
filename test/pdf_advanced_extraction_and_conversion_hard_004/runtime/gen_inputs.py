#!/usr/bin/env python3
import random
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import os

# Set random seed for deterministic output
random.seed(42)

def create_financial_report():
    """Create a financial report PDF with tables and text annotations"""
    doc = SimpleDocTemplate("financial_report.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("MARKER_FINANCIAL_REPORT_2024", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Financial data table
    financial_data = [
        ['Quarter', 'Revenue', 'Expenses', 'Profit'],
        ['Q1 2024', '$125,000', '$85,000', '$40,000'],
        ['Q2 2024', '$142,500', '$92,000', '$50,500'],
        ['Q3 2024', '$158,000', '$98,000', '$60,000'],
        ['Q4 2024', '$167,000', '$105,000', '$62,000']
    ]
    
    table = Table(financial_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Add annotation text
    annotation = Paragraph("MARKER_ANNOTATION: Revenue growth shows consistent upward trend with 33% year-over-year increase.", styles['Normal'])
    story.append(annotation)
    
    doc.build(story)

def create_scientific_paper():
    """Create a scientific paper with complex tables"""
    doc = SimpleDocTemplate("scientific_paper.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("MARKER_SCIENTIFIC_STUDY: Effects of Temperature on Chemical Reactions", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Abstract
    abstract = Paragraph("This study examines the relationship between temperature and reaction rates in organic synthesis.", styles['Normal'])
    story.append(abstract)
    story.append(Spacer(1, 20))
    
    # Experimental data table
    experimental_data = [
        ['Temperature (°C)', 'Reaction Time (min)', 'Yield (%)', 'Purity (%)'],
        ['25', '120', '78.5', '94.2'],
        ['50', '85', '82.1', '95.8'],
        ['75', '62', '85.7', '96.5'],
        ['100', '45', '88.3', '97.1']
    ]
    
    table = Table(experimental_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Statistical analysis table
    stats_data = [
        ['Parameter', 'Mean', 'Std Dev', 'R²'],
        ['Temperature Coefficient', '0.85', '0.12', '0.94'],
        ['Activation Energy (kJ/mol)', '45.2', '3.1', '0.98']
    ]
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(stats_table)
    
    # Add annotation
    annotation = Paragraph("MARKER_ANNOTATION: Statistical analysis confirms strong correlation between temperature and reaction efficiency.", styles['Normal'])
    story.append(annotation)
    
    doc.build(story)

def create_engineering_diagram():
    """Create an engineering diagram with annotations"""
    c = canvas.Canvas("engineering_diagram.pdf", pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "MARKER_ENGINEERING_DIAGRAM: Hydraulic System Layout")
    
    # Draw simple diagram
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.lightblue)
    
    # Main tank
    c.rect(100, 400, 150, 100, fill=1)
    c.setFont("Helvetica", 10)
    c.drawString(110, 440, "Main Tank")
    c.drawString(110, 425, "500L Capacity")
    
    # Pump
    c.setFillColor(colors.yellow)
    c.circle(350, 450, 30, fill=1)
    c.drawString(330, 445, "Pump P1")
    
    # Pipes
    c.line(250, 450, 320, 450)  # Horizontal pipe
    c.line(380, 450, 450, 450)  # Output pipe
    
    # Specifications table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 300, "System Specifications")
    
    specs = [
        ["Component", "Model", "Pressure (PSI)", "Flow Rate (GPM)"],
        ["Main Pump", "HP-2500", "150", "25"],
        ["Secondary Pump", "HP-1200", "100", "15"],
        ["Relief Valve", "RV-300", "200", "N/A"]
    ]
    
    y_pos = 280
    for i, row in enumerate(specs):
        x_pos = 100
        for cell in row:
            if i == 0:
                c.setFont("Helvetica-Bold", 10)
            else:
                c.setFont("Helvetica", 10)
            c.drawString(x_pos, y_pos, cell)
            x_pos += 120
        y_pos -= 15
    
    # Add annotation
    c.setFont("Helvetica", 10)
    c.drawString(100, 200, "MARKER_ANNOTATION: System designed for maximum efficiency at 150 PSI operating pressure.")
    c.drawString(100, 185, "MARKER_ANNOTATION: Regular maintenance required every 500 operating hours.")
    
    c.save()

if __name__ == "__main__":
    create_financial_report()
    create_scientific_paper()
    create_engineering_diagram()
    print("Generated 3 test PDF files with embedded markers")