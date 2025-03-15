import requests
import os
import fitz  # PyMuPDF for PDFs
import docx
import io
import ocr
from PIL import Image

# Set Azure AI Vision API credentials
AZURE_VISION_API_KEY = "6YHDMGjMmgWlJ8wdgU6MPYabvLJS3sps8Xmzflm5XNZ7Y3GFvQaxJQQJ99BCACYeBjFXJ3w3AAAFACOG1B4g" 
AZURE_VISION_ENDPOINT = "https://evalence.cognitiveservices.azure.com/"

def analyze_image(image_path):
    """Uses Azure AI to analyze an image and extract text for grading."""
    if not os.path.exists(image_path):
        return "Error: Image file not found."

    extracted_text = ocr.extract_text_from_image(image_path)

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_API_KEY,
        "Content-Type": "application/octet-stream"
    }

    params = {"visualFeatures": "Categories,Description,Objects,Tags", "language": "en"}

    response = requests.post(
        f"{AZURE_VISION_ENDPOINT}/vision/v3.2/analyze",
        headers=headers,
        params=params,
        data=image_data
    )

    if response.status_code == 200:
        analysis = response.json()
        result = []

        caption = analysis.get("description", {}).get("captions", [{}])[0].get("text", "No description available.")
        result.append(f"Caption: {caption}")

        objects = [obj["object"] for obj in analysis.get("objects", [])]
        if objects:
            result.append(f"Detected Objects: {', '.join(objects)}")

        tags = [tag["name"] for tag in analysis.get("tags", [])]
        result.append(f"Tags: {', '.join(tags)}")

        if any(tag in tags for tag in ["chart", "graph", "plot"]):
            image_type = "Graph"
            feedback = "This appears to be a graph. Ensure the axes are labeled clearly, and data points are well-defined."
        elif any(tag in tags for tag in ["table", "spreadsheet", "grid"]):
            image_type = "Table"
            feedback = "This appears to be a table. Ensure the columns and rows are well-organized and labeled properly."
        elif any(tag in tags for tag in ["diagram", "schematic", "flowchart"]):
            image_type = "Diagram"
            feedback = "This appears to be a diagram. Ensure all components are clearly labeled and interconnected."
        else:
            image_type = "General Image"
            feedback = "This image does not match a common structured format. Please verify if it's relevant for analysis."

        result.append(f"Detected Image Type: {image_type}")
        result.append(f"Feedback: {feedback}")

        full_analysis = "\n".join(result)
        return full_analysis, extracted_text

    else:
        return f"API Error: {response.status_code} - {response.text}", extracted_text

def extract_images_from_pdf(pdf_path):
    """Extract images from a PDF file."""
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."

    images = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)

    return images

def extract_images_from_docx(docx_path):
    """Extract images from a Word document."""
    if not os.path.exists(docx_path):
        return "Error: DOCX file not found."

    images = []
    doc = docx.Document(docx_path)

    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_bytes = rel.target_part.blob
            image = Image.open(io.BytesIO(image_bytes))
            images.append(image)

    return images

def analyze_file(file_path):
    """Analyzes a file (PDF, DOCX, or image) and extracts insights using Azure Vision API."""
    file_extension = os.path.splitext(file_path)[1].lower()
    results = []

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']:
        analysis, extracted_text = analyze_image(file_path)
        results.append(analysis)
    elif file_extension == '.pdf':
        images = extract_images_from_pdf(file_path)
        for img in images:
            img_path = "temp_image.png"
            img.save(img_path)
            analysis, extracted_text = analyze_image(img_path)
            results.append(analysis)
            os.remove(img_path)
    elif file_extension == '.docx':
        images = extract_images_from_docx(file_path)
        for img in images:
            img_path = "temp_image.png"
            img.save(img_path)
            analysis, extracted_text = analyze_image(img_path)
            results.append(analysis)
            os.remove(img_path)
    else:
        return "Unsupported file type."

    return "\n".join(results)

# import os
# import torch
# from transformers import AutoProcessor, LlavaForConditionalGeneration
# from PIL import Image

# # Set the correct path to the downloaded model
# LOCAL_MODEL_PATH = r"C:\Users\HP\Desktop\Atomcamp\FBP\llava-1.5-7b-hf"  

# if not os.path.exists(os.path.join(LOCAL_MODEL_PATH, "pytorch_model.bin")) and not os.path.exists(os.path.join(LOCAL_MODEL_PATH, "model.safetensors")):
#     raise FileNotFoundError(f"Model weights not found in {LOCAL_MODEL_PATH}. Ensure you've run 'git lfs pull'.")

# # Load LLaVA model from local storage
# print("Loading LLaVA model from local storage...")
# model = LlavaForConditionalGeneration.from_pretrained(LOCAL_MODEL_PATH, local_files_only=True)
# processor = AutoProcessor.from_pretrained(LOCAL_MODEL_PATH, local_files_only=True)

# def analyze_image(image_path, question="Describe the image."):
#     """
#     Analyzes an image using LLaVA and generates an AI-based explanation.

#     :param image_path: Path to the image file
#     :param question: Custom question about the image
#     :return: AI-generated response
#     """
#     image = Image.open(image_path).convert("RGB")
#     inputs = processor(text=question, images=image, return_tensors="pt")

#     with torch.no_grad():
#         output = model.generate(**inputs)

#     answer = processor.decode(output[0], skip_special_tokens=True)
#     return answer
