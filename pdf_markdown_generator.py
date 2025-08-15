import os
import random
import fitz  # PyMuPDF
from fpdf import FPDF
from datetime import datetime

class PDFMarkdownGenerator:
    def __init__(self, input_pdf_path, output_dir='output'):
        self.input_pdf_path = input_pdf_path
        self.output_dir = output_dir
        self.markdown_content = []
        self.current_page = 0
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load the PDF
        self.doc = fitz.open(input_pdf_path)
        
    def add_markdown(self, content):
        """Add markdown content to the current page."""
        if not self.markdown_content or len(self.markdown_content) <= self.current_page:
            self.markdown_content.append("")
        self.markdown_content[self.current_page] += content + "\n\n"
    
    def new_page(self):
        """Move to a new page."""
        self.current_page += 1
    
    def generate_pdf(self, output_filename=None):
        """Generate PDF with markdown overlaid on the background PDF."""
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"generated_{timestamp}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Create a temporary directory for page images
        temp_dir = os.path.join(self.output_dir, 'temp_pages')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a new PDF with the same dimensions as the original
        pdf = FPDF()
        
        # Process each page
        for page_num in range(max(len(self.markdown_content), 1)):  # At least one page
            # Get the corresponding page from the original PDF
            src_page_num = min(page_num, len(self.doc) - 1)  # Reuse last page if needed
            page = self.doc[src_page_num]
            width, height = page.rect.width, page.rect.height
            
            # Render the page as an image
            pix = page.get_pixmap()
            img_path = os.path.join(temp_dir, f'page_{page_num}.png')
            pix.save(img_path)
            
            # Add a page with the same dimensions as the original
            pdf.add_page(format=(width, height))
            
            # Add background image
            pdf.image(img_path, x=0, y=0, w=width, h=height)
            
            # Add markdown content if it exists for this page
            if page_num < len(self.markdown_content) and self.markdown_content[page_num].strip():
                # Simple markdown to PDF conversion (basic implementation)
                lines = self.markdown_content[page_num].split('\n')
                y_position = 50  # Start position for text
                
                for line in lines:
                    if line.startswith('# '):
                        pdf.set_font('Arial', 'B', 16)
                        pdf.text(50, y_position, line[2:])
                        y_position += 10
                    elif line.startswith('## '):
                        pdf.set_font('Arial', 'B', 14)
                        pdf.text(50, y_position, line[3:])
                        y_position += 8
                    elif line.strip() == '':
                        y_position += 5  # Add extra space for empty lines
                    else:
                        pdf.set_font('Arial', '', 12)
                        pdf.text(50, y_position, line)
                        y_position += 6
                    
                    # Move to next page if we're near the bottom
                    if y_position > height - 50 and page_num < len(self.markdown_content) - 1:
                        # Save current page and start a new one
                        page_num += 1
                        src_page_num = min(page_num, len(self.doc) - 1)
                        page = self.doc[src_page_num]
                        width, height = page.rect.width, page.rect.height
                        
                        # Render the new page as an image
                        pix = page.get_pixmap()
                        img_path = os.path.join(temp_dir, f'page_{page_num}.png')
                        pix.save(img_path)
                        
                        # Add new page with background
                        pdf.add_page(format=(width, height))
                        pdf.image(img_path, x=0, y=0, w=width, h=height)
                        y_position = 50
        
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        # Save the PDF
        pdf.output(output_path)
        return output_path

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
    
    # Add a title
    content.append(f"# {random.choice(titles)}\n")
    
    # Add some paragraphs
    paragraphs = [
        "This is a sample paragraph that demonstrates how markdown content will appear on the PDF background.",
        "The background will be the uploaded PDF, creating a professional-looking document.",
        "You can add as much content as needed, and the generator will automatically handle pagination.",
        "The system will duplicate the background PDF if more pages are needed for your content.",
        "This is just a demonstration of the markdown generation capabilities."
    ]
    
    # Add 2-4 paragraphs
    for _ in range(random.randint(2, 4)):
        content.append(f"{random.choice(paragraphs)}\n")
    
    # Add a bullet list
    content.append("\n**Key Points:**")
    bullet_points = [
        "Point 1: Important information",
        "Point 2: Additional details",
        "Point 3: More content here",
        "Point 4: Final thoughts"
    ]
    for point in random.sample(bullet_points, random.randint(2, 4)):
        content.append(f"- {point}")
    
    return '\n'.join(content)

if __name__ == "__main__":
    # Example usage
    input_pdf = "/Users/tmecwan/Desktop/Intern Project/uploads/Chicago_Office_Project_Thumbnails_Panel.pdf"
    
    # Create a new generator
    generator = PDFMarkdownGenerator(input_pdf)
    
    # Add some sample markdown content
    print("Generating sample markdown content...")
    for _ in range(3):  # Generate 3 pages of content
        generator.add_markdown(generate_sample_markdown())
        generator.new_page()
    
    # Generate the final PDF
    output_path = generator.generate_pdf("sample_output.pdf")
    print(f"PDF generated successfully at: {output_path}")
