import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Courier", size=10)

def convert_txt_to_pdf(txt_path, pdf_path):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Courier", size=10)
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            pdf.cell(200, 5, txt=line.replace("\n", ""), ln=1, align='L')
    pdf.output(pdf_path)

base_dir = "data/health-insurance-claim/synthetic data/documents/A001/"
for filename in os.listdir(base_dir):
    if filename.endswith(".txt"):
        txt_path = os.path.join(base_dir, filename)
        pdf_path = os.path.join(base_dir, filename.replace(".txt", ".pdf"))
        convert_txt_to_pdf(txt_path, pdf_path)
        print(f"Converted {filename} to PDF.")
