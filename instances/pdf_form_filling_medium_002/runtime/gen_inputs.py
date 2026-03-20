#!/usr/bin/env python3
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfforms
from reportlab.pdfbase.pdfutils import DrawStringCanvas
from reportlab.acroform.acroform import AcroForm
from reportlab.lib.colors import black, white, red
import json

def create_employee_form():
    """Create a fillable PDF form with employee information fields"""
    c = canvas.Canvas("employee_form.pdf", pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Employee Information Form - MARKER_FORM_2024")
    
    # Create form fields using low-level PDF form creation
    c.setFont("Helvetica", 12)
    
    # First Name field
    c.drawString(50, height - 100, "First Name:")
    c.rect(150, height - 105, 200, 20, stroke=1, fill=0)
    c.acroForm.textfield(name='first_name', 
                        tooltip='Enter first name',
                        x=150, y=height-105, 
                        borderStyle='inset',
                        width=200, height=20)
    
    # Last Name field  
    c.drawString(50, height - 140, "Last Name:")
    c.rect(150, height - 145, 200, 20, stroke=1, fill=0)
    c.acroForm.textfield(name='last_name',
                        tooltip='Enter last name', 
                        x=150, y=height-145,
                        borderStyle='inset',
                        width=200, height=20)
    
    # Employee ID field
    c.drawString(50, height - 180, "Employee ID:")
    c.rect(150, height - 185, 150, 20, stroke=1, fill=0) 
    c.acroForm.textfield(name='employee_id',
                        tooltip='Enter employee ID',
                        x=150, y=height-185,
                        borderStyle='inset', 
                        width=150, height=20)
    
    # Department field
    c.drawString(50, height - 220, "Department:")
    c.rect(150, height - 225, 200, 20, stroke=1, fill=0)
    c.acroForm.textfield(name='department',
                        tooltip='Enter department',
                        x=150, y=height-225,
                        borderStyle='inset',
                        width=200, height=20)
    
    # Benefits section
    c.drawString(50, height - 280, "Benefits Enrollment:")
    
    # Health Insurance checkbox
    c.drawString(70, height - 310, "Health Insurance")
    c.acroForm.checkbox(name='health_insurance',
                       tooltip='Check for health insurance',
                       x=50, y=height-315,
                       buttonStyle='check',
                       size=15)
    
    # Dental Insurance checkbox  
    c.drawString(70, height - 340, "Dental Insurance")
    c.acroForm.checkbox(name='dental_insurance',
                       tooltip='Check for dental insurance', 
                       x=50, y=height-345,
                       buttonStyle='check',
                       size=15)
    
    # 401k checkbox
    c.drawString(70, height - 370, "401(k) Plan")
    c.acroForm.checkbox(name='retirement_401k',
                       tooltip='Check for 401k enrollment',
                       x=50, y=height-375, 
                       buttonStyle='check',
                       size=15)
    
    c.save()
    print("Created employee_form.pdf with fillable fields")

def create_employee_data():
    """Create JSON file with employee data to fill the form"""
    employee_data = {
        "first_name": "John",
        "last_name": "Smith", 
        "employee_id": "EMP001",
        "department": "Engineering",
        "health_insurance": True,
        "dental_insurance": False,
        "retirement_401k": True
    }
    
    with open("employee_data.json", "w") as f:
        json.dump(employee_data, f, indent=2)
    print("Created employee_data.json with form values")

def create_pdf_skill_scripts():
    """Create the PDF skill helper scripts"""
    os.makedirs("scripts", exist_ok=True)
    
    # Script to check fillable fields
    check_fields_script = '''#!/usr/bin/env python3
import sys
from pypdf import PdfReader

def check_fillable_fields(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        if "/AcroForm" in reader.trailer["/Root"]:
            acro_form = reader.trailer["/Root"]["/AcroForm"]
            if "/Fields" in acro_form:
                fields = acro_form["/Fields"]
                print(f"Found {len(fields)} fillable fields")
                return True
        print("No fillable fields found")
        return False
    except Exception as e:
        print(f"Error checking fields: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_fillable_fields.py <pdf_file>")
        sys.exit(1)
    check_fillable_fields(sys.argv[1])
'''
    
    with open("scripts/check_fillable_fields.py", "w") as f:
        f.write(check_fields_script)
    
    # Script to extract form field info
    extract_fields_script = '''#!/usr/bin/env python3
import sys
import json
from pypdf import PdfReader

def extract_form_field_info(pdf_path, output_json):
    try:
        reader = PdfReader(pdf_path)
        fields = []
        
        if "/AcroForm" in reader.trailer["/Root"]:
            acro_form = reader.trailer["/Root"]["/AcroForm"]
            if "/Fields" in acro_form:
                form_fields = acro_form["/Fields"]
                
                for field in form_fields:
                    field_obj = field.get_object()
                    field_info = {
                        "field_id": str(field_obj.get("/T", "unknown")),
                        "page": 1,
                        "type": "text"
                    }
                    
                    if "/Ff" in field_obj:
                        ff_value = field_obj["/Ff"]
                        if ff_value & (1 << 16):  # Checkbox flag
                            field_info["type"] = "checkbox"
                            field_info["checked_value"] = "/Yes"
                            field_info["unchecked_value"] = "/Off"
                    
                    if "/Rect" in field_obj:
                        rect = field_obj["/Rect"]
                        field_info["rect"] = [float(x) for x in rect]
                    
                    fields.append(field_info)
        
        with open(output_json, "w") as f:
            json.dump(fields, f, indent=2)
        
        print(f"Extracted {len(fields)} fields to {output_json}")
        
    except Exception as e:
        print(f"Error extracting fields: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_form_field_info.py <input.pdf> <output.json>")
        sys.exit(1)
    extract_form_field_info(sys.argv[1], sys.argv[2])
'''
    
    with open("scripts/extract_form_field_info.py", "w") as f:
        f.write(extract_fields_script)
    
    # Script to fill fillable fields
    fill_fields_script = '''#!/usr/bin/env python3
import sys
import json
from pypdf import PdfReader, PdfWriter

def fill_fillable_fields(input_pdf, field_values_json, output_pdf):
    try:
        # Load field values
        with open(field_values_json, "r") as f:
            field_values = json.load(f)
        
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Fill form fields
        field_dict = {fv["field_id"]: fv["value"] for fv in field_values}
        writer.update_page_form_field_values(writer.pages[0], field_dict)
        
        # Write output
        with open(output_pdf, "wb") as output_file:
            writer.write(output_file)
        
        print(f"Filled form and saved to {output_pdf}")
        
    except Exception as e:
        print(f"Error filling fields: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fill_fillable_fields.py <input.pdf> <field_values.json> <output.pdf>")
        sys.exit(1)
    fill_fillable_fields(sys.argv[1], sys.argv[2], sys.argv[3])
'''
    
    with open("scripts/fill_fillable_fields.py", "w") as f:
        f.write(fill_fields_script)
    
    # Make scripts executable
    os.chmod("scripts/check_fillable_fields.py", 0o755)
    os.chmod("scripts/extract_form_field_info.py", 0o755) 
    os.chmod("scripts/fill_fillable_fields.py", 0o755)
    
    print("Created PDF skill helper scripts")

if __name__ == "__main__":
    create_employee_form()
    create_employee_data()
    create_pdf_skill_scripts()
    print("\nGenerated files:")
    print("- employee_form.pdf (fillable form)")
    print("- employee_data.json (data to fill)")
    print("- scripts/ directory with helper tools")
