#!/usr/bin/env python3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_pdf(filename, title, content):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, title)
    
    # Content marker for verification
    c.setFont("Helvetica", 12)
    y_pos = height - 100
    for line in content:
        c.drawString(50, y_pos, line)
        y_pos -= 20
    
    c.save()

# Create three test PDFs with deterministic content
create_pdf("report1.pdf", "Report 1 - Sales Data", [
    "MARKER_REPORT1_START",
    "Q1 sales figures show strong growth",
    "Revenue increased by 15% over last quarter",
    "MARKER_REPORT1_END"
])

create_pdf("report2.pdf", "Report 2 - Marketing Analysis", [
    "MARKER_REPORT2_START",
    "Customer engagement metrics improved",
    "Social media reach expanded by 25%",
    "MARKER_REPORT2_END"
])

create_pdf("summary.pdf", "Executive Summary", [
    "MARKER_SUMMARY_START",
    "Overall company performance exceeds targets",
    "Recommended actions for next quarter",
    "MARKER_SUMMARY_END"
])

print("Created input PDFs: report1.pdf, report2.pdf, summary.pdf")