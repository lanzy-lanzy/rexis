from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import glob

# Get all the invalid PDF stubs
pdf_files = glob.glob(r"media/proposals/budgets/*.pdf")
pdf_files.extend(glob.glob(r"media/proposals/documents/*.pdf"))
pdf_files.extend(glob.glob(r"media/extension/documents/*.pdf"))

count = 0
for pdf_path in pdf_files:
    file_size = os.path.getsize(pdf_path)
    if file_size < 1000:  # If it's a stub (< 1KB)
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(50, 750, "Test Document")
        c.drawString(50, 730, os.path.basename(pdf_path))
        c.showPage()
        c.save()
        count += 1
        print(f"Fixed: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

print(f"\nTotal PDFs fixed: {count}")
