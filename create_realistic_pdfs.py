import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_pdf(txt_path, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    normal_style = styles["Normal"]
    normal_style.fontName = "Courier"
    normal_style.fontSize = 9
    
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        spaceAfter=6
    )

    story = []
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 10))
                continue
            
            if line.startswith("```"):
                continue
                
            # Basic formatting
            if line.startswith("**"):
                story.append(Paragraph(line.replace("**", ""), bold_style))
            elif line.isupper() and len(line) > 5 and ":" not in line:
                story.append(Paragraph(line, bold_style))
            else:
                story.append(Paragraph(line, normal_style))
                
    doc.build(story)

base_dir = "data/health-insurance-claim/synthetic data/documents/A001/"
for filename in os.listdir(base_dir):
    if filename.endswith(".txt"):
        txt_path = os.path.join(base_dir, filename)
        pdf_path = os.path.join(base_dir, filename.replace(".txt", ".pdf"))
        try:
            create_pdf(txt_path, pdf_path)
            print(f"Successfully created {pdf_path}")
        except Exception as e:
            print(f"Failed on {filename}: {e}")