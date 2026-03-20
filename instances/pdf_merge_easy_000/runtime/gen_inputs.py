#!/usr/bin/env python3

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Create report1.pdf with marker content
c = canvas.Canvas("report1.pdf", pagesize=letter)
width, height = letter

# Page 1
c.drawString(100, height - 100, "REPORT ONE - SALES DATA")
c.drawString(100, height - 130, "Marker: SALES_2023_Q1")
c.drawString(100, height - 160, "This is the first report containing sales data.")
c.showPage()

# Page 2 
c.drawString(100, height - 100, "REPORT ONE - PAGE TWO")
c.drawString(100, height - 130, "Marker: REVENUE_SUMMARY")
c.drawString(100, height - 160, "Additional sales metrics and analysis.")
c.save()

# Create report2.pdf with marker content
c = canvas.Canvas("report2.pdf", pagesize=letter)
width, height = letter

# Page 1
c.drawString(100, height - 100, "REPORT TWO - MARKETING DATA")
c.drawString(100, height - 130, "Marker: MARKETING_2023_Q1")
c.drawString(100, height - 160, "This is the second report with marketing metrics.")
c.save()

# Create report3.pdf with marker content
c = canvas.Canvas("report3.pdf", pagesize=letter)
width, height = letter

# Page 1
c.drawString(100, height - 100, "REPORT THREE - OPERATIONS")
c.drawString(100, height - 130, "Marker: OPERATIONS_2023_Q1")
c.drawString(100, height - 160, "This is the third report covering operations.")
c.showPage()

# Page 2
c.drawString(100, height - 100, "REPORT THREE - CONCLUSIONS")
c.drawString(100, height - 130, "Marker: FINAL_CONCLUSIONS")
c.drawString(100, height - 160, "Summary and recommendations for next quarter.")
c.save()

print("Generated input PDFs: report1.pdf (2 pages), report2.pdf (1 page), report3.pdf (2 pages)")