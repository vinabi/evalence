# ocr.py
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import os
import io
import docx
import shutil

# Detect if tesseract exists on PATH (Streamlit Cloud will install it via packages.txt)
_TESSERACT_OK = shutil.which("tesseract") is not None

def _ocr_core_image(pil_image: Image.Image) -> str:
    """OCR a PIL image safely (handles modes & missing tesseract)."""
    if not _TESSERACT_OK:
        # If tesseract binary isn't installed, skip image OCR but don't crash.
        return "[OCR skipped: tesseract not available on server]"
    # Convert to a format Tesseract likes
    img = pil_image.convert("L")  # grayscale
    return pytesseract.image_to_string(img)

def extract_text_from_image(image_path: str) -> str:
    """OCR a standalone image file."""
    with Image.open(image_path) as im:
        return _ocr_core_image(im)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF (fast, no Poppler needed),
    then OCR any embedded images on each page.
    """
    doc = fitz.open(pdf_path)
    collected = []

    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        # 1) Direct text (layout-aware extractor is "text")
        collected.append(page.get_text("text"))

        # 2) OCR images on the page (if tesseract is available)
        for imginfo in page.get_images(full=True):
            xref = imginfo[0]
            base = doc.extract_image(xref)
            image_bytes = base["image"]
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                # Ensure a safe mode for OCR
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                ocr_text = _ocr_core_image(pil_img)
                collected.append(f"[Image OCR on page {page_idx+1}]\n{ocr_text}")

    return "\n".join(filter(None, collected)).strip()

def extract_text_from_docx(docx_path: str) -> str:
    """
    Extract text & OCR any embedded images from a Word document.
    """
    d = docx.Document(docx_path)
    parts = []

    # Paragraph text
    for para in d.paragraphs:
        if para.text.strip():
            parts.append(para.text)

    # Embedded images
    for rel in d.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                ocr_text = _ocr_core_image(pil_img)
                parts.append(f"[Image OCR]\n{ocr_text}")

    return "\n".join(parts).strip()
