# vision.py
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import pytesseract
import numpy as np

# Load BLIP model once globally
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def analyze_image(image_path):
    """
    Analyzes the image using BLIP (for description) and Tesseract (for text).
    Returns (description, extracted_text).
    """
    image = Image.open(image_path).convert("RGB")
    
    # BLIP captioning
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    # OCR with Tesseract
    text = pytesseract.image_to_string(np.array(image))

    return f"Image Description: {caption}", text

# Optional: If you're analyzing DOCX or PDF images
def extract_images_from_docx(path):
    import docx, io
    images = []
    doc = docx.Document(path)
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            img = Image.open(io.BytesIO(image_bytes))
            images.append(img)
    return images
