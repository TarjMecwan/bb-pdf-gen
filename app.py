import os
import random
import tempfile
import fitz  # PyMuPDF
from fpdf import FPDF
from datetime import datetime
from flask import Flask, render_template, request, send_file, send_from_directory, jsonify, redirect, url_for, make_response
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import shutil

def generate_pdf_with_markdown(pdf_path, markdown_content, page_count=None,
                               text_enabled=True, shapes_enabled=False, shape_types=None):
    """Generate a PDF by overlaying bubble comments onto the PDF background.
    Each non-empty line of the provided markdown_content becomes a separate
    comment bubble with a leader line (callout) pointing to a random spot.
    Only include the requested number of pages."""
    try:
        # Create a temporary directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Open the PDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            if page_count is not None:
                page_count = int(page_count)
            else:
                page_count = total_pages
            
            # Create a new PDF (use points so coordinates match background image size)
            pdf = FPDF(unit='pt')

            # Prepare comments once and distribute across pages
            all_comments = []
            if markdown_content:
                all_comments = [ln.strip() for ln in markdown_content.split('\n') if ln.strip()]
            
            # We will distribute comments randomly across the requested pages
            comments_by_page = {}
            # We'll fill this after we know page_count (computed just below)
            # Determine the default page size (from first page of PDF or fallback)
            if total_pages > 0:
                first_page = doc.load_page(0)
                default_width, default_height = first_page.rect.width, first_page.rect.height
                width_pt = default_width * 72 / 72
                height_pt = default_height * 72 / 72
            else:
                width_pt, height_pt = 612, 792  # 8.5x11" default

            # Initialize page assignment map now that we know the page_count
            comments_by_page = {i: [] for i in range(page_count)}
            for txt in all_comments:
                assigned = random.randint(0, max(0, page_count - 1))
                comments_by_page[assigned].append(txt)

            # Simple helper to wrap text and get height for a given width
            def wrap_lines(pdf_obj, text, max_width, line_height):
                words = text.split(' ')
                lines = []
                cur = ''
                for word in words:
                    candidate = (cur + ' ' + word).strip()
                    if pdf_obj.get_string_width(candidate) <= max_width:
                        cur = candidate
                    else:
                        if cur:
                            lines.append(cur)
                        cur = word
                if cur:
                    lines.append(cur)
                return lines

            # Normalize shape types
            if not shape_types:
                shape_types = []
            allowed_shapes = {'box', 'cloud', 'pen'}
            shape_types = [s for s in shape_types if s in allowed_shapes]
            if shapes_enabled and not shape_types:
                shape_types = ['box']

            for page_num in range(page_count):
                if page_num < total_pages:
                    page = doc.load_page(page_num)
                    width, height = page.rect.width, page.rect.height
                    width_pt = width * 72 / 72
                    height_pt = height * 72 / 72
                    pdf.add_page(format=(width_pt, height_pt))
                    img_path = os.path.join(temp_dir, f'page_{page_num}.png')
                    pix = page.get_pixmap()
                    pix.save(img_path)
                    pdf.image(img_path, x=0, y=0, w=width_pt, h=height_pt)
                else:
                    pdf.add_page(format=(width_pt, height_pt))
                # Overlay bubble comment callouts randomly on this page
                page_comments = comments_by_page.get(page_num, [])
                if not page_comments:
                    continue
                
                # Styling and layout constraints
                pdf.set_font('Arial', '', 12)
                margin = 36  # 0.5 inch
                line_height = 16
                min_w, max_w = 180, 300
                placed_boxes = []  # track placed rects (x, y, w, h) to avoid overlaps

                def overlaps(r1, r2):
                    x1, y1, w1, h1 = r1
                    x2, y2, w2, h2 = r2
                    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

                def draw_shape_with_optional_text(text, shape_kind, idx=0):
                    # choose a random box width for shapes/text area
                    w = random.uniform(min_w, min(max_w, max(120, width_pt - 2 * margin)))
                    # Estimate height based on text if text_enabled
                    inner_w = w - 12
                    lines = wrap_lines(pdf, text, inner_w, line_height) if (text_enabled and text) else []
                    text_h = (12 + len(lines) * line_height) if lines else 0
                    base_h = max(36, text_h or 48)

                    # Try to find a non-overlapping random position
                    for _ in range(25):
                        x = random.uniform(margin, max(margin, width_pt - margin - w))
                        y = random.uniform(margin, max(margin, height_pt - margin - base_h))
                        candidate = (x, y, w, base_h)
                        if all(not overlaps(candidate, pb) for pb in placed_boxes):
                            pdf.set_draw_color(30, 144, 255)
                            pdf.set_fill_color(255, 255, 255)
                            if shapes_enabled:
                                if shape_kind == 'box':
                                    # outline box
                                    pdf.rect(x, y, w, base_h, style='D')
                                elif shape_kind == 'cloud':
                                    # crude cloud effect: small circles around the boundary
                                    bumps = max(8, int(w / 30))
                                    r = 8
                                    step = (w - 2*r) / bumps
                                    cx = x + r
                                    top = y
                                    bottom = y + base_h
                                    # top edge bumps
                                    for i in range(bumps):
                                        pdf.ellipse(cx + i*step - r/2, top - r/2, r, r)
                                    # bottom edge bumps
                                    for i in range(bumps):
                                        pdf.ellipse(cx + i*step - r/2, bottom - r/2, r, r)
                                    # left/right edges bumps
                                    vbumps = max(4, int(base_h / 24))
                                    vstep = (base_h - 2*r) / vbumps
                                    cy = y + r
                                    for i in range(vbumps):
                                        pdf.ellipse(x - r/2, cy + i*vstep - r/2, r, r)
                                        pdf.ellipse(x + w - r/2, cy + i*vstep - r/2, r, r)
                                elif shape_kind == 'pen':
                                    # simple freehand polyline within area
                                    px = x + 6
                                    py = y + base_h/2
                                    segments = max(5, int(w / 40))
                                    for i in range(segments):
                                        nx = min(x + w - 6, px + random.uniform(15, 30))
                                        ny = min(max(y + 6, py + random.uniform(-20, 20)), y + base_h - 6)
                                        pdf.line(px, py, nx, ny)
                                        px, py = nx, ny
                            # draw text if requested
                            if text_enabled and lines:
                                pdf.set_text_color(0, 0, 0)
                                pdf.set_xy(x + 6, y + 6)
                                for ln in lines:
                                    pdf.cell(inner_w, line_height, ln, ln=1)
                            placed_boxes.append(candidate)
                            return True
                    return False

                def draw_text_only(text):
                    # Choose area width for wrapping text, but render without any box or leader
                    w = random.uniform(min_w, min(max_w, max(120, width_pt - 2 * margin)))
                    inner_w = w
                    lines = wrap_lines(pdf, text, inner_w, line_height)
                    h = len(lines) * line_height
                    for _ in range(25):
                        x = random.uniform(margin, max(margin, width_pt - margin - w))
                        y = random.uniform(margin, max(margin, height_pt - margin - h))
                        candidate = (x, y, w, h)
                        if all(not overlaps(candidate, pb) for pb in placed_boxes):
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_xy(x, y)
                            for ln in lines:
                                pdf.cell(inner_w, line_height, ln, ln=1)
                            placed_boxes.append(candidate)
                            return True
                    return False

                shape_idx = 0
                for text in page_comments:
                    if shapes_enabled:
                        kind = shape_types[shape_idx % len(shape_types)] if shape_types else 'box'
                        draw_shape_with_optional_text(text, kind, shape_idx)
                        shape_idx += 1
                    elif text_enabled:
                        draw_text_only(text)
            
            # Save the PDF to a bytes buffer
            pdf_bytes = pdf.output(dest='S')
            if isinstance(pdf_bytes, str):
                return pdf_bytes.encode('latin-1')
            return bytes(pdf_bytes)
            
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_sample_markdown():
    """Generate sample markdown content for demonstration."""
    titles = [
        "Project Overview",
        "Key Findings",
        "Methodology",
        "Results",
        "Conclusion",
        "Next Steps"
    ]
    
    content = []
    content.append(f"# {random.choice(titles)}\\n")
    
    paragraphs = [
        "This is a sample paragraph that demonstrates how markdown content will appear on the PDF background.",
        "The background will be the uploaded PDF, creating a professional-looking document.",
        "You can add as much content as needed, and the generator will automatically handle pagination.",
        "The system will duplicate the background PDF if more pages are needed for your content.",
        "This is just a demonstration of the markdown generation capabilities."
    ]
    
    for _ in range(random.randint(2, 4)):
        content.append(f"{random.choice(paragraphs)}\\n")
    
    content.append("\\n**Key Points:**")
    bullet_points = [
        "Point 1: Important information",
        "Point 2: Additional details",
        "Point 3: More content here",
        "Point 4: Final thoughts"
    ]
    for point in random.sample(bullet_points, random.randint(2, 4)):
        content.append(f"- {point}")
    
    return '\\n'.join(content)

# Sample AEC comments
DEFAULT_COMMENTS = [
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

COLORS = [colors.red, colors.blue, colors.green, colors.orange, colors.purple, colors.brown]
PAGE_WIDTH = 36 * inch  # 36"
PAGE_HEIGHT = 24 * inch  # 24"

def draw_diamond(c, x, y, size=12, color=colors.blue):
    half = size/2
    p = c.beginPath()
    p.moveTo(x, y + half)
    p.lineTo(x + half, y)
    p.lineTo(x, y - half)
    p.lineTo(x - half, y)
    p.close()
    c.setStrokeColor(color)
    c.setFillColor(colors.white)
    c.setLineWidth(1)
    c.drawPath(p, stroke=1, fill=1)

def draw_rectangle(c, x, y, width, height, color):
    c.setStrokeColor(color)
    c.setFillColor(colors.white)
    c.setLineWidth(1.5)
    c.rect(x, y, width, height, stroke=1, fill=1)

def draw_text(c, x, y, text, font_size=10, color=colors.black):
    c.setFillColor(color)
    c.setFont("Helvetica", font_size)
    c.drawString(x, y, text)

def draw_measurement(c, x1, y1, x2, y2, text, color=colors.black):
    # Draw line
    c.setStrokeColor(color)
    c.setLineWidth(0.5)
    c.line(x1, y1, x2, y2)
    
    # Draw end markers
    marker_size = 5
    c.line(x1 - marker_size, y1 - marker_size, x1 + marker_size, y1 + marker_size)
    c.line(x1 - marker_size, y1 + marker_size, x1 + marker_size, y1 - marker_size)
    c.line(x2 - marker_size, y2 - marker_size, x2 + marker_size, y2 + marker_size)
    c.line(x2 - marker_size, y2 + marker_size, x2 + marker_size, y2 - marker_size)
    
    # Draw measurement text
    text_width = c.stringWidth(text, "Helvetica", 8)
    text_x = (x1 + x2) / 2 - text_width / 2
    text_y = (y1 + y2) / 2 + 10
    draw_text(c, text_x, text_y, text, 8, color)

def draw_page(page_num, path, comments, include_text=True, include_shapes=True, include_measurements=False):
    c = canvas.Canvas(path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pageCompression=0)
    
    # Draw a light grid background
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.1)
    for x in range(0, int(PAGE_WIDTH), 50):
        c.line(x, 0, x, PAGE_HEIGHT)
    for y in range(0, int(PAGE_HEIGHT), 50):
        c.line(0, y, PAGE_WIDTH, y)
    
    # Add random markups based on selected types
    if include_text:
        # Add text annotations
        count = random.randint(3, 8)
        for _ in range(count):
            comment = random.choice(comments)
            color = random.choice(COLORS)
            w = 6 * len(comment) + 20
            h = 20
            x = random.uniform(100, PAGE_WIDTH - w - 100)
            y = random.uniform(100, PAGE_HEIGHT - h - 100)
            
            # Draw text box
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            c.rect(x, y, w, h, stroke=1, fill=1)
            
            # Draw text
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            c.drawString(x + 5, y + 5, comment)
            
            # Draw arrow to a random point
            ex, ey = x + w/2 + random.uniform(-100, 100), y + h/2 + random.uniform(-100, 100)
            c.setStrokeColor(color)
            c.setLineWidth(1)
            c.line(x + w/2, y + h/2, ex, ey)
            draw_diamond(c, ex, ey, size=8, color=color)
    
    if include_shapes:
        # Add random shapes
        shape_count = random.randint(2, 5)
        for _ in range(shape_count):
            color = random.choice(COLORS)
            x = random.uniform(100, PAGE_WIDTH - 200)
            y = random.uniform(100, PAGE_HEIGHT - 200)
            w = random.uniform(50, 300)
            h = random.uniform(30, 100)
            
            if random.random() > 0.5:
                # Rectangle
                draw_rectangle(c, x, y, w, h, color)
            else:
                # Circle
                c.setStrokeColor(color)
                c.setFillColor(colors.white)
                c.setLineWidth(1.5)
                radius = min(w, h) / 2
                c.circle(x + radius, y + radius, radius, stroke=1, fill=1)
    
    if include_measurements:
        # Add random measurements
        measure_count = random.randint(2, 4)
        for _ in range(measure_count):
            color = random.choice(COLORS)
            x1 = random.uniform(100, PAGE_WIDTH - 200)
            y1 = random.uniform(100, PAGE_HEIGHT - 200)
            x2 = x1 + random.uniform(50, 300)
            y2 = y1 + random.uniform(-100, 100)
            length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            draw_measurement(c, x1, y1, x2, y2, f"{length/72:.1f} in", color)
    
    # Add footer
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.gray)
    c.drawCentredString(PAGE_WIDTH/2, 30, f"AEC Test Document - Page {page_num} - Generated on {datetime.now().strftime('%Y-%m-%d')}")
    
    c.save()

def generate_pdf(target_size_mb, page_count, comments, markup_types):
    # Create temporary directory for pages
    temp_dir = tempfile.mkdtemp(dir=app.config['TEMP_FOLDER'])
    page_paths = []
    
    try:
        # Generate pages
        for i in range(1, page_count + 1):
            page_path = os.path.join(temp_dir, f"page_{i}.pdf")
            draw_page(
                i, 
                page_path, 
                comments,
                include_text='text' in markup_types,
                include_shapes='shapes' in markup_types,
                include_measurements='measurements' in markup_types
            )
            page_paths.append(page_path)
        
        # Merge pages
        output_path = os.path.join(temp_dir, "output.pdf")
        merger = PdfMerger()
        for path in page_paths:
            merger.append(path)
        merger.write(output_path)
        merger.close()
        
        # Pad to target size if needed
        target_bytes = int(target_size_mb * 1024 * 1024)
        actual_size = os.path.getsize(output_path)
        
        if actual_size < target_bytes:
            with open(output_path, 'ab') as f:
                f.write(b'\0' * (target_bytes - actual_size))
        elif actual_size > target_bytes:
            # If the PDF is already larger than target, we can't shrink it
            pass  # For now, we'll just return the PDF as is
        
        return output_path
        
    except Exception as e:
        # Clean up temp directory on error
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise

@app.route('/')
def index():
    # Look for PDF files in the uploads folder
    default_pdf = None
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.lower().endswith('.pdf'):
                default_pdf = file
                break
    
    return render_template('index.html', default_pdf=default_pdf)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    # Securely serve files from the uploads directory
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads_dir, filename, as_attachment=False)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Get form data
        file_name = request.form.get('fileName', 'generated_document').strip()
        markdown_content = request.form.get('markdown', '')
        modified_date_str = request.form.get('modifiedDate')  # 'YYYY-MM-DD' or None
        # Markup options
        text_enabled = (request.form.get('textEnabled', 'true').lower() == 'true')
        shapes_enabled = (request.form.get('shapesEnabled', 'false').lower() == 'true')
        shape_types_raw = request.form.get('shapeTypes', '')
        shape_types = [s.strip() for s in shape_types_raw.split(',') if s.strip()] if shape_types_raw else []
        
        # Check if we should use the default PDF
        use_default = request.form.get('useDefault') == 'true' or 'file' not in request.files
        
        if use_default:
            # Get the first PDF from the uploads folder
            default_pdf = None
            uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
            if os.path.exists(uploads_dir):
                for file in os.listdir(uploads_dir):
                    if file.lower().endswith('.pdf'):
                        default_pdf = file
                        break
            
            if not default_pdf:
                return jsonify({'error': 'No default PDF found'}), 400
                
            pdf_path = os.path.join(uploads_dir, default_pdf)
            output_filename = f'{file_name}.pdf' if file_name else f'annotated_{default_pdf}'
        else:
            # Handle uploaded file
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Invalid file type'}), 400
            
            # Save the uploaded file temporarily
            pdf_path = os.path.join(tempfile.gettempdir(), file.filename)
            file.save(pdf_path)
            output_filename = f'{file_name}.pdf' if file_name else f'annotated_{file.filename}'
        
        try:
            # Generate PDF with markdown overlay
            # Get requested page count
            page_count = request.form.get('pageCount')
            pdf_bytes = generate_pdf_with_markdown(
                pdf_path,
                markdown_content,
                page_count=page_count,
                text_enabled=text_enabled,
                shapes_enabled=shapes_enabled,
                shape_types=shape_types,
            )

            # If a modified date is provided, set it as PDF ModDate metadata
            if modified_date_str:
                try:
                    # Parse date and build PDF date string D:YYYYMMDDHHmmSS
                    dt = datetime.strptime(modified_date_str, '%Y-%m-%d')
                    pdf_date = f"D:{dt.strftime('%Y%m%d')}000000"
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    writer = PdfWriter()
                    for p in reader.pages:
                        writer.add_page(p)
                    # Preserve existing metadata and override ModDate
                    meta = {} if reader.metadata is None else dict(reader.metadata)
                    meta['/ModDate'] = pdf_date
                    writer.add_metadata(meta)
                    out_bio = io.BytesIO()
                    writer.write(out_bio)
                    pdf_bytes = out_bio.getvalue()
                except Exception as e:
                    print(f'Warning: could not set PDF ModDate: {e}')
            
            # Pad PDF to target size if requested
            target_size_mb = request.form.get('targetSize')
            if target_size_mb:
                try:
                    target_bytes = int(float(target_size_mb) * 1024 * 1024)
                    if len(pdf_bytes) < target_bytes:
                        pdf_bytes += b'\0' * (target_bytes - len(pdf_bytes))
                    # If PDF is larger, do nothing
                except Exception as e:
                    print(f'Warning: Could not pad PDF to target size: {e}')
            
            # Clean up temporary file if we created one
            if not use_default and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            
            # Create a response with the PDF
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            response.headers['Content-Length'] = len(pdf_bytes)
            
            return response
            
        except Exception as e:
            # Clean up temporary file in case of error
            if not use_default and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            raise e
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
