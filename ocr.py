from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import os
import io
import docx

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_core(image):
    """
    This function will handle the core OCR processing of images.
    """
    text = pytesseract.image_to_string(image)  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    return text

def extract_text_from_image(image_path):
    """
    This function will extract text from a standalone image file.
    """
    image = Image.open(image_path)
    text = ocr_core(image)
    return text

def extract_text_from_pdf(pdf_path):
    """
    This function will extract text from a PDF file, including text from images within the PDF.
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
        
        # Extract images from the page
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            text += "\n[Text from image {} on page {}]:\n".format(img_index + 1, page_num + 1)
            text += ocr_core(image)
    return text

def extract_text_from_docx(docx_path):
    """
    This function will extract text from a Word document, including text from images within the document.
    """
    doc = docx.Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    
    # Extract images from the document
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            image = Image.open(io.BytesIO(image_bytes))
            text += "\n[Text from image]:\n"
            text += ocr_core(image)
    
    return text

def main():
    file_path = input("Please enter the path to your file: ")
    
    if not os.path.isfile(file_path):
        print("The file does not exist.")
        return
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
        print("Processing image file...")
        text = extract_text_from_image(file_path)
    elif file_extension == '.pdf':
        print("Processing PDF file...")
        text = extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        print("Processing Word document...")
        text = extract_text_from_docx(file_path)
    else:
        print("Unsupported file type.")
        return
    
    print("Extracted Text:")
    print(text)

if __name__ == "__main__":
    main()