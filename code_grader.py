import requests
import os

API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def grade_python_code(code_snippet, total_marks=100):
    """Sends code to AI for grading based on logic, efficiency, and readability."""

    messages = [
        {"role": "system", "content": "You are a senior software engineer. Review the following Python code for logic, efficiency, and best practices."},
        {"role": "user", "content": f"""
        Python Code:
        ```
        {code_snippet}
        ```

        Task:
        - Give a score out of {total_marks} (allow partial marking).
        - Explain why you gave this score.
        - Provide feedback on how to optimize and improve the logic.

        Output Format:
        - Score: X/{total_marks}
        - Explanation: ...
        - Feedback: ...
        """}
    ]

    payload = {"model": "mixtral-8x7b-32768", "messages": messages, "temperature": 0.7}
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)

    return response.json()

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
        {"role": "system", "content": "You are an AI evaluator. Grade the student's answers, image analysis, and Python code based on their understanding and clarity."},
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