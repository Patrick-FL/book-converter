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
            
            # Create a mapping of image filenames to their index (for numbering)
            image_mapping = {}
            for i, img_path in enumerate(images, start=1):
                img_filename = os.path.basename(img_path)
                image_mapping[img_filename] = i
            
            # Process HTML content
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    # Replace image tags with numbered references
                    content = self.replace_image_tags_with_references(content, image_mapping)
                    html_content += content
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

    def replace_image_tags_with_references(self, html_content, image_mapping):
        """
        Replace <img> tags in HTML with numbered image references that match the image PDF.
        """
        import re
        
        # Function to replace each img tag with a numbered reference
        def replace_img(match):
            img_tag = match.group(0)
            # Extract the src attribute
            src_match = re.search(r'src=[\'"](.*?)[\'"]', img_tag)
            if src_match:
                src = src_match.group(1)
                # Get just the filename from the path
                img_filename = os.path.basename(src)
                # Find the image number in our mapping
                if img_filename in image_mapping:
                    img_number = image_mapping[img_filename]
                    # Return a styled image reference
                    return f'<div style="text-align: center; margin: 20px 0; font-weight: bold; font-size: 14px; color: #333; padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;">[Bild {img_number} - Siehe Bildanhang]</div>'
            # If we couldn't process the image, return the original tag
            return img_tag
        
        # Find and replace all img tags in the HTML
        result = re.sub(r'<img\s+[^>]+>', replace_img, html_content)
        return result

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
