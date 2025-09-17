import streamlit as st
import os
import ocr
import vision  
import code_grader
from grading import grade_extracted_text, grade_image, classify_uploaded_content
from PIL import Image

# ----------------------- UI CONFIG -----------------------
st.set_page_config(page_title="Evalence", layout="wide")
st.title("Evalence")

# --- Light Almond Background + Dark Sidebar ---
st.markdown("""
    <style>
    body, .stApp {
        background-color: #EEE5DA;
        color: black;
    }
    div[data-testid="stSidebar"] {
        background-color: #262424;
    }
    .stTextArea textarea, .stTextInput input, .stTextInput textarea {
        background-color: #EEE5DA;
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------- USER INPUTS -----------------------
total_marks = st.number_input("Enter total marks for evaluation (default: 100)", min_value=1, value=100)
st.markdown("Upload any **exam paper** (pdf, image, docx, or code), and Evalence will auto-analyze + grade it.")

uploaded_file = st.file_uploader("Upload your file", type=["jpg", "jpeg", "png", "pdf", "docx", "py", "c", "txt"])

# ----------------------- HELPERS -----------------------
def validate_score(score, total):
    try:
        score = int(score)
        if score > total:
            st.warning(f"Score {score} exceeds total {total}, adjusting...")
            return total
        return score
    except:
        return "N/A"

def extract_elements(content):
    score, explanation, feedback = "N/A", "No explanation.", "No feedback."
    try:
        if "Score:" in content:
            score = content.split("Score:")[1].split("/")[0].strip()
        if "Explanation:" in content:
            explanation = content.split("Explanation:")[1].split("Feedback:")[0].strip()
        if "Feedback:" in content:
            feedback = content.split("Feedback:")[1].strip()
    except:
        feedback = content
    return score, explanation, feedback

def sidebar_box(title, score, total, explanation, feedback):
    st.sidebar.markdown(f"""
        <div style="border-radius: 15px; padding: 20px; background: #262424; color: white; font-family: 'Segoe UI', sans-serif;">
            <h3 style="text-align: center;">{title}</h3>
            <p><b>Score:</b> <span style="font-size: 20px; color: #EEE5DA;">{score}/{total}</span></p>
            <hr>
            <p><b>Explanation:</b></p>
            <p>{explanation}</p>
            <hr>
            <p><b>Feedback:</b></p>
            <p>{feedback}</p>
        </div>
    """, unsafe_allow_html=True)

# ----------------------- MAIN LOGIC -----------------------
if uploaded_file:
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        with st.spinner("Processing..."):
            if file_ext == ".pdf":
                extracted_text = ocr.extract_text_from_pdf(file_path)
            elif file_ext == ".docx":
                extracted_text = ocr.extract_text_from_docx(file_path)
                extracted_images = vision.extract_images_from_docx(file_path)
            elif file_ext in [".py", ".txt", ".c"]:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    extracted_text = f.read()
            elif file_ext in [".jpg", ".jpeg", ".png"]:
                extracted_text = ocr.extract_text_from_image(file_path)
            else:
                st.error("Unsupported file type.")
                st.stop()

            if extracted_text.strip():
                st.text_area("Extracted Text", extracted_text, height=200)

                # Classify & Evaluate
                content_type = classify_uploaded_content(extracted_text)

                if content_type in ["solution", "assignment", "project report"]:
                    grading = grade_extracted_text(extracted_text, total_marks)
                    title = "Evaluation"
                else:
                    grading = grade_extracted_text(extracted_text, total_marks)
                    title = "Explanation"

                content = grading.get("choices", [{}])[0].get("message", {}).get("content", "")
                score, explanation, feedback = extract_elements(content)

                if content_type in ["solution", "assignment", "project report"]:
                    score = validate_score(score, total_marks)
                sidebar_box(title, score, total_marks, explanation, feedback)

            # ---------- IMAGE FILE ANALYSIS ----------
            if file_ext in [".jpg", ".jpeg", ".png"]:
                grading = grade_image(file_path, total_marks)
                content = grading.get("choices", [{}])[0].get("message", {}).get("content", "")
                score, explanation, feedback = extract_elements(content)
                score = validate_score(score, total_marks)
                sidebar_box("Image Evaluation", score, total_marks, explanation, feedback)
                st.image(file_path, caption="Uploaded Image", use_container_width=True)

            # ---------- IMAGES FROM DOCX ----------
            if file_ext == ".docx" and extracted_images:
                for i, img in enumerate(extracted_images):
                    temp_img_path = f"docx_img_{i}.png"
                    img.save(temp_img_path)
                    grading = grade_image(temp_img_path, total_marks)
                    content = grading.get("choices", [{}])[0].get("message", {}).get("content", "")
                    score, explanation, feedback = extract_elements(content)
                    score = validate_score(score, total_marks)
                    sidebar_box(f"Image from DOCX (Page {i+1})", score, total_marks, explanation, feedback)
                    os.remove(temp_img_path)

    except Exception as e:
        st.error(f"Error: {e}")

    os.remove(file_path)
