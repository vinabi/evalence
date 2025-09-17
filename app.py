import streamlit as st
import os
import ocr
import vision  
import code_grader
from grading import grade_extracted_text, grade_image, classify_uploaded_content
from PIL import Image

st.set_page_config(page_title="Evalence", layout="wide")
st.title("Evalence")

total_marks = st.number_input("Enter total marks for evaluation (default: 100)", min_value=1, value=100)
st.markdown("Upload an **exam paper (pdf, img, docx, code)**, and the AI will **evaluate the content**.")

def validate_score(score, total_marks):
    try:
        score = int(score)
        if score > total_marks:
            st.warning(f"The score ({score}) exceeds the total marks ({total_marks}). Adjusting to total marks.")
            score = total_marks
    except ValueError:
        score = "N/A"
    return score

def extract_grading_elements(content):
    """
    Extracts Score, Explanation, and Feedback from AI-generated content
    while handling missing sections properly.
    """
    score = "N/A"
    explanation = "No explanation provided."
    feedback = "No feedback available."

    try:
        if "Score:" in content:
            score = content.split("Score:")[1].split("/")[0].strip()
        if "Explanation:" in content:
            explanation = content.split("Explanation:")[1].split("Feedback:")[0].strip()
        if "Feedback:" in content:
            feedback = content.split("Feedback:")[1].strip()
    except (IndexError, ValueError):
        feedback = content  # If parsing fails, show raw response

    return score, explanation, feedback

uploaded_file = st.file_uploader("Upload a file", type=["jpg", "png", "pdf", "py", "txt", "docx", "c"])

if uploaded_file:
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    file_extension = os.path.splitext(file_path)[1].lower()

    with st.spinner("Processing..."):
        try:
            if file_extension == ".pdf":
                extracted_text = ocr.extract_text_from_pdf(file_path)
            elif file_extension in [".py", ".txt", ".c"]:
                with open(file_path, "r", encoding="utf-8", errors="replace") as code_file:
                    extracted_text = code_file.read()
            elif file_extension == ".docx":
                extracted_text = ocr.extract_text_from_docx(file_path)
                extracted_images = vision.extract_images_from_docx(file_path)
            else:
                extracted_text = ocr.extract_text_from_image(file_path)

            if extracted_text.strip():
                st.text_area("| Extracted Text:", extracted_text, height=200)

                # Classify the uploaded content
                content_type = classify_uploaded_content(extracted_text)

                if content_type == "solution":
                    st.success("This appears to be a solution. Proceeding with grading...")
                    
                    with st.spinner("Grading answers..."):
                        grading_result = grade_extracted_text(extracted_text, total_marks)
                    
                elif content_type == "assignment" or content_type == "project report":
                    st.success(f"This appears to be a {content_type}. Proceeding with thorough evaluation...")
                    
                    with st.spinner("Evaluating content..."):
                        grading_result = grade_extracted_text(extracted_text, total_marks)
                    
                else:
                    st.info(f"The uploaded content was classified as **{content_type}**. Providing an explanation.")
                    grading_result = grade_extracted_text(extracted_text, total_marks)

                if "error" in grading_result:
                    st.error(grading_result["error"])
                else:
                    content = grading_result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if not content.strip():
                        st.warning("AI response was empty. Instead of stopping, we are providing a basic explanation.")
                        content = "No specific evaluation available, but the text was analyzed."

                    score, explanation, feedback = extract_grading_elements(content)

                    if content_type == "solution" or content_type == "assignment" or content_type == "project report":
                        score = validate_score(score, total_marks)

                        st.sidebar.markdown(f"""
                            <div style="border-radius: 15px; padding: 20px; background: #262424; color: white; font-family: Times New Roman, sans-serif;">
                                <h2 style="text-align: center; font-size: 26px;"> Evaluation Stats </h2>
                                <p><b>Score:</b> <span style="font-size: 24px; color: #EEE5DA;">{score}/{total_marks}</span></p>
                                <hr>
                                <p><b>Explanation:</b></p>
                                <p style="font-style: italic;">{explanation}</p>
                                <hr>
                                <p><b>Feedback:</b></p>
                                <p>{feedback}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.sidebar.markdown(f"""
                            <div style="border-radius: 15px; padding: 20px; background: #262424; color: white; font-family: Arial, sans-serif;">
                                <h2 style="text-align: center; font-size: 26px;"> Explanation </h2>
                                <p>{explanation}</p>
                            </div>
                        """, unsafe_allow_html=True)

                # Display image analysis results from DOCX files
                if file_extension == ".docx" and extracted_images:
                    image_analysis_results = []
                    for img in extracted_images:
                        img_path = "temp_image.png"
                        img.save(img_path)
                        analysis, extracted_text_img = grade_image(img_path)
                        image_analysis_results.append(analysis)
                        os.remove(img_path)
                    image_analysis = "\n\n".join(image_analysis_results)
                    st.sidebar.markdown(f"""
                        <div style="border-radius: 15px; padding: 20px; background: #EEE5DA; color: white; font-family: Arial, sans-serif;">
                            <h2 style="text-align: center; font-size: 26px;"> Image Analysis from DOCX </h2>
                            <p>{image_analysis}</p>
                        </div>
                    """, unsafe_allow_html=True)

            # If the file is an image, analyze and grade it 
            if file_extension in [".jpg", ".jpeg", ".png"]:
                with st.spinner("Analyzing and grading image content..."):
                    grading_result = grade_image(file_path)

                if "error" in grading_result:
                    st.error("An error occurred while grading the image. Please check the API key.")
                else:
                    content = grading_result.get("choices", [{}])[0].get("message", {}).get("content", "")

                    if not content.strip():
                        st.error("AI response was empty. Try again.")
                        os.remove(file_path)
                        st.stop()

                    score, explanation, feedback = extract_grading_elements(content)

                    # Multiply the score by 2
                    try:
                        score = str(int(score) * 2)
                    except ValueError:
                        score = "N/A"

                    # Validate the score
                    score = validate_score(score, total_marks)

                    st.sidebar.markdown(f"""
                        <div style="border-radius: 15px; padding: 20px; background: #262424; color: white; font-family: Times New Roman, sans-serif;">
                            <h2 style="text-align: center; font-size: 26px;"> Evaluation Stats </h2>
                            <p><b>Score:</b> <span style="font-size: 24px; color: #EEE5DA;">{score}/{total_marks}</span></p>
                            <hr>
                            <p><b>Explanation:</b></p>
                            <p style="font-style: italic;">{explanation}</p>
                            <hr>
                            <p><b>Feedback:</b></p>
                            <p>{feedback}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    # Display the image being analyzed
                    st.image(file_path, caption="Analyzed Image", use_container_width=True)

        except Exception as e:
            st.warning(f"AI encountered an issue but instead of stopping, providing available analysis. Error: {e}")

    os.remove(file_path)
