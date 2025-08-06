import fitz
import sys
import re
import tempfile
import subprocess

def extract_po_page_count(doc):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = f"{tmpdir}/page1.pdf"
        output_txt = f"{tmpdir}/page1.txt"

        # Create a temporary 1-page PDF
        one_page_doc = fitz.open()
        one_page_doc.insert_pdf(doc, from_page=0, to_page=0)
        one_page_doc.save(input_path)

        # OCR the first page
        subprocess.run([
            "ocrmypdf", "--force-ocr", "--sidecar", output_txt,
            "--output-type", "pdfa", input_path, "/dev/null"
        ], check=True)

        with open(output_txt, "r") as f:
            text = f.read()

    # Try matching the page count with fuzzy OCR-aware regex
    match = re.search(r'page\s*[\w\W]{0,3}of\s+(\d+)', text, re.IGNORECASE)
    if match:
        po_pages = int(match.group(1))
        print(f"[INFO] Detected PO page count from OCR: {po_pages}")
        return po_pages
    else:
        print("[WARN] OCR could not detect 'Page 1 of N' — assuming full doc is PO")
        return len(doc)

def split_pdf(input_path, po_output_path, router_output_path):
    doc = fitz.open(input_path)
    po_page_count = extract_po_page_count(doc)

    # Save PO pages
    po_doc = fitz.open()
    po_doc.insert_pdf(doc, from_page=0, to_page=po_page_count-1)
    po_doc.save(po_output_path)

    # Save Router pages if present
    if po_page_count < len(doc):
        router_doc = fitz.open()
        router_doc.insert_pdf(doc, from_page=po_page_count)
        router_doc.save(router_output_path)
        print(f"[INFO] Split complete: PO = {po_page_count} page(s), Router = {len(doc) - po_page_count} page(s)")
    else:
        print("[INFO] No Router pages detected; saved full file as PO only")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python split_po_router_basic.py input.pdf output_po.pdf output_router.pdf")
        sys.exit(1)

    split_pdf(sys.argv[1], sys.argv[2], sys.argv[3])
