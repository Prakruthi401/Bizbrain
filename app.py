import os

import pandas as pd
import streamlit as st

from student_tools import make_study_plan, parse_deadlines, resume_match

# Tried in order: if one model is busy or over quota, the next one is used.
MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash"]

st.set_page_config(page_title="BizBrain AI", page_icon="🧠", layout="centered")


def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.environ.get("GEMINI_API_KEY", "")


def ask_gemini(prompt):
    """Send a prompt to Gemini. Returns None when no key is configured."""
    key = get_api_key()
    if not key:
        return None
    from google import genai
    client = genai.Client(api_key=key)
    last_error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text
        except Exception as e:
            last_error = e
    st.error(f"Could not reach Gemini: {last_error}")
    return ""


def gemini_or_key_notice(prompt):
    answer = ask_gemini(prompt)
    if answer is None:
        st.info("Add a Gemini API key to use the AI features. Locally: set the "
                "GEMINI_API_KEY environment variable. On Streamlit Cloud: add it "
                "under App settings -> Secrets as GEMINI_API_KEY. "
                "Get a free key at aistudio.google.com.")
    return answer


PERSONALITY_PROMPTS = {
    "Friendly Bot": "Act like a friendly assistant and respond warmly to: {}",
    "Professional Bot": "Act like a professional business assistant and answer formally: {}",
    "Funny Bot": "Add a touch of humor and act like a fun chatbot. User asked: {}",
}


def chatbot():
    st.subheader("💬 BizBrain AI Chatbot")
    bot_type = st.selectbox("Choose your chatbot personality:", list(PERSONALITY_PROMPTS))

    user_input = st.text_input("You:", key="text_input")
    if st.button("Send") and user_input:
        st.write("You:", user_input)
        answer = gemini_or_key_notice(PERSONALITY_PROMPTS[bot_type].format(user_input))
        if answer:
            st.write("BizBrain AI:", answer)


CONTENT_PROMPTS = {
    "Formal Letter": "Write a formal letter regarding: {}",
    "Formal Email": "Compose a professional email about: {}",
    "Story Creation": "Create a short and engaging story based on: {}",
    "Blog Writing": "Write an informative and well-structured blog post on: {}",
    "Social Media Post": "Generate a catchy and engaging social media post about: {}",
}


def content_generator():
    st.subheader("✍️ AI Content Generator")
    content_type = st.radio("Select content type:", list(CONTENT_PROMPTS))
    content_input = st.text_area("Enter the topic / purpose / keywords:")

    if st.button("Generate") and content_input:
        answer = gemini_or_key_notice(CONTENT_PROMPTS[content_type].format(content_input))
        if answer:
            st.subheader("📝 Generated Output")
            st.write(answer)


def image_text_tool():
    uploaded_images = st.file_uploader(
        "Upload image(s) to extract text", type=["png", "jpg", "jpeg"],
        accept_multiple_files=True)
    if not uploaded_images:
        return
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        st.error("pytesseract and Pillow are required for image text extraction.")
        return
    for uploaded_file in uploaded_images:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)
        with st.spinner("Extracting text..."):
            try:
                text = pytesseract.image_to_string(image)
            except pytesseract.TesseractNotFoundError:
                st.error("Tesseract is not installed on this machine. See the README "
                         "for how to install it (one line on Streamlit Cloud).")
                return
        st.success("Text extracted:")
        st.text_area(f"Text from {uploaded_file.name}", text, height=200)


def pdf_text_tool():
    uploaded_pdfs = st.file_uploader("Upload PDF(s) to extract text", type=["pdf"],
                                     accept_multiple_files=True)
    if not uploaded_pdfs:
        return
    import fitz  # PyMuPDF
    for pdf_file in uploaded_pdfs:
        with st.spinner(f"Extracting text from {pdf_file.name}..."):
            text = ""
            try:
                with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                    for page in doc:
                        text += page.get_text()
            except Exception as e:
                st.error(f"Failed to read {pdf_file.name}: {e}")
                continue
        st.success(f"Text extracted from {pdf_file.name}:")
        st.text_area(f"Text from {pdf_file.name}", text, height=300)


def csv_tool():
    uploaded_csv = st.file_uploader("Upload a CSV file to analyze", type=["csv"])
    if not uploaded_csv:
        return
    try:
        df = pd.read_csv(uploaded_csv, encoding_errors="ignore")
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return
    st.write("📋 Uploaded CSV data:")
    st.dataframe(df)
    st.write("Quick summary:")
    st.dataframe(df.describe(include="all").transpose())

    query = st.text_input("Ask a question about the CSV data:", key="csv_query")
    if st.button("Analyze CSV") and query:
        sample = df.head(20).to_string()
        answer = gemini_or_key_notice(
            f"Here is a sample of a CSV dataset (first 20 rows):\n\n{sample}\n\n"
            f"Answer this question about the data: {query}")
        if answer:
            st.write("BizBrain AI:", answer)


TOOLS = {
    "Image to Text": "image",
    "PDF to Text": "pdf",
    "CSV Data Analysis": "csv",
    "Notes to Quiz": "quiz",
    "Exam Planner": "planner",
    "Deadline Tracker": "deadlines",
    "Resume & Job Match": "resume",
}


def student_toolkit():
    st.subheader("📚 Student Productivity Toolkit")
    tool = st.radio("Choose a feature:", list(TOOLS))
    kind = TOOLS[tool]
    if kind == "image":
        image_text_tool()
    elif kind == "pdf":
        pdf_text_tool()
    elif kind == "csv":
        csv_tool()
    elif kind == "quiz":
        notes_to_quiz()
    elif kind == "planner":
        exam_planner()
    elif kind == "deadlines":
        deadline_tracker()
    else:
        resume_matcher()


def main():
    st.title("🧠 BizBrain AI")
    user_name = st.text_input("Enter your name:", key="name")
    if user_name:
        st.caption(f"Hi {user_name} 👋")

    selected = st.radio("Choose a tool:",
                        ["Student Productivity Toolkit", "AI Content Generator", "BizBrain AI Chatbot"],
                        horizontal=True)
    st.markdown("---")
    if selected == "Student Productivity Toolkit":
        student_toolkit()
    elif selected == "AI Content Generator":
        content_generator()
    else:
        chatbot()




def notes_to_quiz():
    st.write("Paste your notes (or upload a PDF/TXT) and get a quick quiz to revise from.")
    uploaded = st.file_uploader("Upload notes (PDF or TXT)", type=["pdf", "txt"], key="quiz_file")
    notes = st.text_area("...or paste notes here:", height=150, key="quiz_notes")

    if uploaded is not None:
        if uploaded.type == "application/pdf":
            import fitz
            with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
                notes = "".join(page.get_text() for page in doc)
        else:
            notes = uploaded.read().decode("utf-8", errors="ignore")
        st.caption(f"Loaded {len(notes)} characters from {uploaded.name}.")

    if st.button("Make quiz") and notes.strip():
        prompt = (
            "Create 5 multiple choice questions from these notes for a student revising. "
            "Give 4 options each, then list the correct answers at the end.\n\n"
            + notes[:6000])
        answer = gemini_or_key_notice(prompt)
        if answer:
            st.markdown(answer)


def exam_planner():
    st.write("Plan revision days up to your exam. Weak topics automatically get extra time.")
    subjects_raw = st.text_input("Subjects (comma separated):", key="plan_subjects")
    weak_raw = st.text_input("Weak topics (comma separated, optional):", key="plan_weak")
    exam_date = st.date_input("Exam date:", key="plan_date")
    hours = st.slider("Study hours per day:", 1, 12, 4, key="plan_hours")

    if st.button("Make plan"):
        subjects = [s.strip() for s in subjects_raw.split(",") if s.strip()]
        weak = [w.strip() for w in weak_raw.split(",") if w.strip()]
        if not subjects:
            st.warning("Add at least one subject.")
            return
        rows = make_study_plan(subjects, weak, exam_date, hours)
        if rows is None:
            st.warning("Exam date must be in the future.")
            return
        st.dataframe(pd.DataFrame(rows), hide_index=True)


def deadline_tracker():
    st.write("Paste a syllabus, circular or email and pull out the deadlines.")
    text = st.text_area("Paste text here:", height=150, key="deadline_text")
    if st.button("Extract deadlines") and text.strip():
        prompt = (
            "Extract every deadline, due date, exam date or submission date from this text. "
            "Reply with one line each in the exact format: Task - Date (like 12 Jan 2026). "
            "No other words.\n\n" + text[:6000])
        answer = gemini_or_key_notice(prompt)
        if answer:
            rows = parse_deadlines(answer)
            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True)
            else:
                st.write(answer)


def resume_matcher():
    st.write("Compare your resume with a job post and see which keywords are missing.")
    resume = st.text_area("Your resume (paste text):", height=150, key="match_resume")
    jd = st.text_area("Job description (paste text):", height=150, key="match_jd")
    if st.button("Match") and resume.strip() and jd.strip():
        score, missing = resume_match(resume, jd)
        st.metric("Keyword match", f"{score}%")
        if missing:
            st.write("Keywords in the job post that your resume doesn't mention:")
            st.write(", ".join(missing[:40]))
        else:
            st.success("Your resume covers every keyword in this job post.")

if __name__ == "__main__":
    main()
