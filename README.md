# AEC PDF Generator

A web application for generating test PDFs with customizable sizes and AEC (Architecture, Engineering, and Construction) markups for testing Bluebeam and other AEC software.

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
   git clone <repository-url>
   cd aec-pdf-generator
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask development server:
   ```bash
   python app.py
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

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
