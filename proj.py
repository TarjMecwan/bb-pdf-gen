#!/usr/bin/env python3
"""
generate_test_pdf.py

Generates a fake AEC-style PDF with random markups, then pads
it with null bytes to hit an exact file size.
"""

import os
import random
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfMerger

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TARGET_SIZE_MB = 1500        # ← Change this to whatever MB size you need (e.g. 1500 for ~1.5 GB)
PAGES = 20                   # ← Number of distinct pages to generate
TEMP_DIR = "tmp_pages"
OUTPUT_PDF = "test_pdf_exact_size.pdf"
# ────────────────────────────────────────────────────────────────────────────────

# Sample “realistic” AEC comments
COMMENTS = [
    "Check beam alignment",
    "Verify load calculations",
    "Reinforce column #5",
    "Adjust window dimensions",
    "Confirm electrical grounding",
    "Seal pipe joints",
    "Update HVAC diagram",
    "Inspect weld quality",
    "Review wall thickness",
    "Coordinate with plumbing team",
]

COLORS = [colors.red, colors.blue, colors.green, colors.orange]

PAGE_WIDTH  = 36 * inch   # 36"
PAGE_HEIGHT = 24 * inch   # 24"

def draw_diamond(c, x, y, size=12):
    half = size/2
    p = c.beginPath()
    p.moveTo(x, y + half)
    p.lineTo(x + half, y)
    p.lineTo(x, y - half)
    p.lineTo(x - half, y)
    p.close()
    c.setStrokeColor(colors.blue)
    c.setFillColor(colors.white)
    c.setLineWidth(1)
    c.drawPath(p, stroke=1, fill=1)

def draw_page(page_num, path):
    c = canvas.Canvas(path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pageCompression=0)
    # Random boxes + text
    count = random.randint(5, 10)
    for i in range(count):
        comment = random.choice(COMMENTS)
        clr     = random.choice(COLORS)
        w       = 6 * len(comment) + 20
        h       = 20
        x = random.uniform(100, PAGE_WIDTH - w - 100)
        y = random.uniform(100, PAGE_HEIGHT - h - 100)

        # box
        c.setStrokeColor(clr)
        c.setLineWidth(2)
        c.rect(x, y, w, h)

        # text
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(x + 5, y + 5, comment)

        # arrow to a nearby point
        ex, ey = x + w/2 + random.uniform(-50, 50), y + h/2 + random.uniform(-50, 50)
        c.setStrokeColor(clr)
        c.setLineWidth(1)
        c.line(x + w/2, y + h/2, ex, ey)
        # small arrowhead
        draw_diamond(c, ex, ey, size=8)

    # footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(PAGE_WIDTH/2, 30, f"Mockup PDF – Page {page_num}")
    c.save()

def generate_pages():
    os.makedirs(TEMP_DIR, exist_ok=True)
    paths = []
    for i in range(1, PAGES+1):
        p = os.path.join(TEMP_DIR, f"page_{i}.pdf")
        draw_page(i, p)
        paths.append(p)
        print(f" → generated {p}")
    return paths

def merge_pages(paths):
    merger = PdfMerger()
    for p in paths:
        merger.append(p)
    merger.write(OUTPUT_PDF)
    merger.close()
    print(f" → merged into {OUTPUT_PDF}")

def pad_to_target():
    target_bytes = int(TARGET_SIZE_MB * 1024**2)
    actual = os.path.getsize(OUTPUT_PDF)
    if actual > target_bytes:
        print(f"⚠️  PDF is already {actual//1024**2} MB, which is > target {TARGET_SIZE_MB} MB.")
        return
    to_pad = target_bytes - actual
    with open(OUTPUT_PDF, "ab") as f:
        f.write(b"\0" * to_pad)
    print(f" → padded with {to_pad} null bytes")
    final = os.path.getsize(OUTPUT_PDF)
    print(f"✅ Final size: {final/1024**2:.2f} MB")

if __name__ == "__main__":
    print("Generating pages…")
    page_files = generate_pages()

    print("\nMerging…")
    merge_pages(page_files)

    print("\nPadding to exact size…")
    pad_to_target()

    # cleanup if you like:
    # import shutil; shutil.rmtree(TEMP_DIR)
