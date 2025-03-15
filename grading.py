import requests
import os
from vision import analyze_image
import streamlit as st

API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def grade_extracted_text(extracted_text, image_analysis="", total_marks=100):
    """Send extracted text + AI image analysis to the Groq AI model for grading."""

    image_analysis = str(image_analysis) if image_analysis else ""

    combined_text = extracted_text
    if image_analysis.strip():
        combined_text += f"\n\nAdditional AI Image Analysis:\n{image_analysis}"

    messages = [
        {"role": "system", "content": "You are an AI exam evaluator. Grade the student's answers based on their understanding and thought process. Ignore english grammar and spelling mistakes. Consider the image analysis for context. If calculations are correct, solution's almost correct. If calculations are incorrect, solution's incorrect. Mark based on student's concepts and understanding. Not following a proper structure should not lead to marks deduction."},
        {"role": "user", "content": f"""
        Student's Answers:
        {combined_text}

        Task:
        - Give a score out of {total_marks} (allow partial marking).
        - Explain why you gave this score.
        - Provide feedback on how to improve.

        Output Format:
        - Score: X/{total_marks}
        - Explanation: ...
        - Feedback: ...
        """}
    ]

    payload = {"model": "mixtral-8x7b-32768", "messages": messages, "temperature": 0.7}
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)
    
    return response.json()

def grade_image(image_path, total_marks=100):
    """Analyze an image and grade it based on the extracted text and AI analysis."""
    analysis, extracted_text = analyze_image(image_path)
    grading_result = grade_extracted_text(extracted_text, analysis, total_marks)
    return grading_result

def grade_code(extracted_text, image_analysis="", code_feedback="", total_marks=100):
    """Send extracted code text + AI image analysis + Code Analysis to the Groq AI model for grading."""

    image_analysis = str(image_analysis) if image_analysis else ""
    code_feedback = str(code_feedback) if code_feedback else ""

    combined_text = extracted_text
    if image_analysis.strip():
        combined_text += f"\n\nAdditional AI Image Analysis:\n{image_analysis}"
    if code_feedback.strip():
        combined_text += f"\n\nCode Review Feedback:\n{code_feedback}"

    messages = [
        {"role": "system", "content": "You are an AI evaluator. Grade the student's answers, image analysis, and Python code based on their understanding and clarity. Ignore grammar and spelling mistakes. If possible make accurate suggestions for improvement and make guesses about the student's understanding."},
        {"role": "user", "content": f"""
        Student's Work:
        {combined_text}

        Task:
        - Give a score out of {total_marks} (allow partial marking).
        - Explain why you gave this score.
        - Provide feedback on how to improve.

        Output Format:
        - Score: X/{total_marks}
        - Explanation: ...
        - Feedback: ...
        """}
    ]

    payload = {"model": "mixtral-8x7b-32768", "messages": messages, "temperature": 0.7}
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)

    return response.json()

def classify_uploaded_content(text):
    """
    Uses AI to determine whether the uploaded content is a solution, a question, or another type of content.
    """

    messages = [
        {"role": "system", "content": "You are an AI that classifies text into categories: 'solution', 'question', 'topic', or 'other'."},
        {"role": "user", "content": f"Analyze this text:\n{text}\n\nIs this a 'solution', 'question', 'topic', or 'other'? Respond with only one word."}
    ]

    payload = {"model": "mixtral-8x7b-32768", "messages": messages, "temperature": 0.7}
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        result = response.json()
        classification = result["choices"][0]["message"]["content"].strip().lower()

        if classification in ["solution", "question", "topic", "other"]:
            return classification
        return "other"  # Default if AI response is unexpected
    return "error"  # If API call fails