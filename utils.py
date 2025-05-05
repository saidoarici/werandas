# utils.py
from flask import render_template
from weasyprint import HTML
from io import BytesIO

def generate_pdf(offer):
    html_string = render_template("pdf_template.html", offer=offer)
    pdf_file = BytesIO()
    HTML(string=html_string, base_url='.').write_pdf(target=pdf_file)
    return pdf_file.getvalue()