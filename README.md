# Bluebeam PDF Generator - Intern Project

Hello, my name is Tarj and I worked as a Software Engineer Intern on the Cloud team during Summer 2025. As a side project, I built a tool that generates customizable PDF markdown files — allowing users to specify file size, content, shapes, tools, and metadata for more efficient and targeted testing.

## Features

- Generate PDFs with specific file sizes (in MB)
- Customize the number of pages
- Add various types of markups:
  - Text annotations with callouts
  - Shapes (rectangles, circles, lines)
  - Measurement annotations
- Customize comments and annotations
- Download generated PDFs directly from the browser

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/TarjMecwan/bb-pdf-gen.git
   cd bb-pdf-gen
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask development server:
   ```bash
   python3 app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Fill out the form with your desired settings:
   - Target PDF size (in MB)
   - Number of pages
   - Types of markups to include
   - Custom comments (optional)

4. Click "Generate PDF" and wait for the download to start.

## Requirements

- Python 3.7+
- Flask
- ReportLab
- PyPDF2
- python-dotenv (for environment variables)
