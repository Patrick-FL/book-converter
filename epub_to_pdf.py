# Convert epub to pdf
# Usage: python epub_to_pdf.py input.epub output.pdf


import sys
import ebooklib
from ebooklib import epub
import pdfkit
import os
from PIL import Image
from fpdf import FPDF
import shutil
import logging

# Configure logging
logging.basicConfig(filename='conversion.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class EpubConverter:
    def __init__(self):
        pass

    def convert_epub_to_pdf(self, epub_path, pdf_path):
        try:
            # Create a temporary directory for extracted resources
            temp_dir = 'temp_resources'
            os.makedirs(temp_dir, exist_ok=True)

            # Read the EPUB file
            book = epub.read_epub(epub_path)
            html_content = ''

            # Extract all resources and update HTML content
            images = self.extract_images(book, temp_dir)
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    html_content += item.get_content().decode('utf-8')
                elif item.get_type() in [ebooklib.ITEM_IMAGE, ebooklib.ITEM_STYLE, ebooklib.ITEM_SCRIPT]:
                    # Save the resource to the temporary directory
                    resource_path = os.path.join(temp_dir, item.get_name())
                    os.makedirs(os.path.dirname(resource_path), exist_ok=True)
                    try:
                        with open(resource_path, 'wb') as f:
                            f.write(item.get_content())
                    except Exception as e:
                        logging.error(f'Error extracting resource: {item.get_name()}. Error: {str(e)}')

            # Write the HTML content to a temporary file
            with open('temp.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info('HTML content written to temp.html')

            # Convert the HTML to PDF with improved styling and image handling
            options = {
                'quiet': '',
                'enable-local-file-access': '',
                'load-media-error-handling': 'ignore',  # Ignore missing resources
                'disable-smart-shrinking': '',  # Prevent font compression
                'margin-top': '15mm',
                'margin-bottom': '15mm',
                'margin-left': '10mm',
                'margin-right': '10mm',
                'encoding': 'UTF-8',
                'page-size': 'A4',  # Ensure A4 format
            }
            try:
                # Create PDF with full content
                pdfkit.from_file('temp.html', pdf_path, options=options)
                logging.info('PDF conversion successful')

                # Create separate PDF with images only
                images_pdf_path = os.path.splitext(pdf_path)[0] + '_images.pdf'
                self.create_images_pdf(images, images_pdf_path)
                logging.info('Images PDF created successfully')

            except Exception as e:
                logging.error(f'PDF conversion failed. Error: {str(e)}')
                raise

        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.remove('temp.html')
            logging.info('Temporary files cleaned up')

    def extract_images(self, book, temp_dir):
        images = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                image_path = os.path.join(temp_dir, item.get_name())
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                with open(image_path, 'wb') as f:
                    f.write(item.get_content())
                images.append(image_path)
        return images

    def create_images_pdf(self, images, output_path):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        for i, image_path in enumerate(images, start=1):
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    aspect_ratio = width / height

                    # Calculate dimensions for A4 page (210mm x 297mm)
                    max_width = 190  # mm, with 10mm margins
                    max_height = 267  # mm, with 15mm margins

                    # Calculate new dimensions maintaining aspect ratio
                    if aspect_ratio > 1:
                        # Landscape orientation
                        new_width = min(max_width, max_height * aspect_ratio)
                        new_height = new_width / aspect_ratio
                    else:
                        # Portrait orientation
                        new_height = min(max_height, max_width / aspect_ratio)
                        new_width = new_height * aspect_ratio

                    # Add new page and image
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, f'Bild {i}', 0, 1, 'C')
                    pdf.image(image_path, x=(210 - new_width)/2, y=30, w=new_width)
            except Exception as e:
                logging.error(f'Error processing image {image_path}: {str(e)}')
                continue

        pdf.output(output_path)

if __name__ == '__main__':
    converter = EpubConverter()
    if len(sys.argv) != 3:
        print('Usage: python epub_to_pdf.py <input.epub> <output.pdf>')
    else:
        converter.convert_epub_to_pdf(sys.argv[1], sys.argv[2])
