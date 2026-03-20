#!/usr/bin/env python3
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfform import textFieldAbsolute, checkboxAbsolute
from reportlab.lib.colors import black, blue, red
from PIL import Image, ImageDraw, ImageFont
import os

# Set deterministic seed
random.seed(42)

def create_insurance_form():
    c = canvas.Canvas("insurance_claim_form.pdf", pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "INSURANCE CLAIM FORM - MARKER_FORM_2024")
    
    # Add fillable fields with known values
    c.setFont("Helvetica", 12)
    
    # Policy Number field
    c.drawString(50, height - 100, "Policy Number:")
    textFieldAbsolute(c, "policy_number", 180, height - 105, 200, 20, "POL-MARKER-123456")
    
    # Claimant Name field
    c.drawString(50, height - 140, "Claimant Name:")
    textFieldAbsolute(c, "claimant_name", 180, height - 145, 200, 20, "MARKER_JOHN_DOE")
    
    # Claim Amount field
    c.drawString(50, height - 180, "Claim Amount ($):")
    textFieldAbsolute(c, "claim_amount", 180, height - 185, 200, 20, "15750.00")
    
    # Incident Date field
    c.drawString(50, height - 220, "Incident Date:")
    textFieldAbsolute(c, "incident_date", 180, height - 225, 200, 20, "2024-01-15")
    
    # Category checkboxes
    c.drawString(50, height - 260, "Claim Category:")
    c.drawString(70, height - 280, "Auto")
    checkboxAbsolute(c, "category_auto", 50, height - 285, 15, 15, checked=True)
    
    c.drawString(150, height - 280, "Home")
    checkboxAbsolute(c, "category_home", 130, height - 285, 15, 15, checked=False)
    
    c.drawString(230, height - 280, "Health")
    checkboxAbsolute(c, "category_health", 210, height - 285, 15, 15, checked=False)
    
    # Add some static text areas that will need OCR
    c.drawString(50, height - 320, "Description of Incident:")
    c.rect(50, height - 420, 500, 80, stroke=1, fill=0)
    
    # Add marker text in description area
    c.setFont("Helvetica", 10)
    c.drawString(60, height - 340, "Vehicle collision at intersection. MARKER_INCIDENT_DESC_2024")
    c.drawString(60, height - 355, "Damage to front bumper and headlight. Police report #PR789.")
    c.drawString(60, height - 370, "Other party admitted fault. VALIDATION_MARKER_COMPLETE")
    
    # Add approval section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 460, "For Office Use Only:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 480, "Approved Amount: $13,500.00 MARKER_APPROVED")
    c.drawString(50, height - 500, "Adjuster: MARKER_ADJUSTER_SMITH")
    c.drawString(50, height - 520, "Approval Date: 2024-02-01")
    
    c.save()
    
def create_handwritten_supplement():
    """Create a scanned-looking supplement with handwritten-style text"""
    img = Image.new('RGB', (612, 792), 'white')  # Letter size in pixels
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Add header
    draw.text((50, 50), "CLAIM SUPPLEMENT - MARKER_SUPPLEMENT_2024", fill='black', font=font)
    
    # Add handwritten-style content
    draw.text((50, 100), "Additional damages discovered:", fill='black', font=font)
    draw.text((50, 130), "- Radiator damage: $2,250 MARKER_RADIATOR", fill='black', font=font)
    draw.text((50, 160), "- Paint repair needed: $500 MARKER_PAINT", fill='black', font=font)
    draw.text((50, 190), "- Alignment issues: $300 MARKER_ALIGNMENT", fill='black', font=font)
    
    draw.text((50, 250), "Total additional: $3,050.00", fill='black', font=font)
    draw.text((50, 280), "VALIDATION_SUPPLEMENT_COMPLETE", fill='blue', font=font)
    
    # Add some noise to simulate scanning
    for _ in range(100):
        x, y = random.randint(0, 611), random.randint(0, 791)
        draw.point((x, y), fill=(200, 200, 200))
    
    img.save("handwritten_supplement.png")
    
    # Convert to PDF
    img_pdf = Image.open("handwritten_supplement.png")
    img_pdf.save("handwritten_supplement.pdf")
    
def create_business_rules():
    """Create business rules file for validation"""
    rules = '''{
  "rules": {
    "max_auto_claim": 50000,
    "max_home_claim": 100000,
    "max_health_claim": 25000,
    "required_fields": ["policy_number", "claimant_name", "claim_amount", "incident_date"],
    "policy_prefix": "POL-",
    "adjuster_validation": "MARKER_ADJUSTER_",
    "approval_threshold": 10000
  },
  "categories": {
    "auto": {"code": "A", "color": "blue", "max_amount": 50000},
    "home": {"code": "H", "color": "green", "max_amount": 100000},
    "health": {"code": "M", "color": "red", "max_amount": 25000}
  },
  "validation_markers": [
    "MARKER_FORM_2024",
    "VALIDATION_MARKER_COMPLETE",
    "MARKER_APPROVED"
  ]
}'''
    
    with open("business_rules.json", "w") as f:
        f.write(rules)

def create_expected_data():
    """Create expected extracted data for validation"""
    expected = '''{
  "form_data": {
    "policy_number": "POL-MARKER-123456",
    "claimant_name": "MARKER_JOHN_DOE",
    "claim_amount": "15750.00",
    "incident_date": "2024-01-15",
    "category": "auto",
    "approved_amount": "13500.00",
    "adjuster": "MARKER_ADJUSTER_SMITH"
  },
  "supplement_data": {
    "radiator_damage": "2250",
    "paint_repair": "500",
    "alignment": "300",
    "total_additional": "3050.00"
  },
  "markers_found": [
    "MARKER_FORM_2024",
    "MARKER_INCIDENT_DESC_2024",
    "VALIDATION_MARKER_COMPLETE",
    "MARKER_APPROVED",
    "MARKER_SUPPLEMENT_2024",
    "VALIDATION_SUPPLEMENT_COMPLETE"
  ]
}'''
    
    with open("expected_data.json", "w") as f:
        f.write(expected)

if __name__ == "__main__":
    create_insurance_form()
    create_handwritten_supplement()
    create_business_rules()
    create_expected_data()
    print("Generated insurance claim files with embedded markers")