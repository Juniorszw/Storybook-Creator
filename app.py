import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. SETUP: Load Environment Variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API Key not found! Please check your .env file.")
    st.stop()

genai.configure(api_key=api_key)

# 2. PROMPT ENGINEERING (Advanced)
SYSTEM_PROMPT = """
You are a professional children's book author and illustrator. 
I will give you a topic. You must generate a 3-page story.
You must output the result in strict JSON format. 
Do not add any markdown formatting (like ```json). Just the raw JSON.

Structure:
{
  "title": "Story Title",
  "pages": [
    {
      "page_number": 1,
      "story_text": "The narrative text for this page (2-3 sentences, rhyming couplets suitable for children).",
      "image_prompt": "A highly detailed description of the visual scene for an AI image generator. Include style keywords like 'watercolor', 'warm lighting'."
    },
    ... (repeat for 3 pages)
  ]
}
"""

st.set_page_config(page_title="AI Storybook Prototype")

# 3. Sidebar for user instructions
with st.sidebar:
    st.header("How to use")
    st.write("1. Enter a topic for your story.")
    st.write("2. Click 'Generate'.")
    st.write("3. Review the AI-generated text.")
    st.divider()
    st.info("Note: Image and Audio generation features are coming in Phase 3.")

st.title("Storybook Creator: Feature Prototype")

# User Input
user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")

if st.button("Generate"):
    if user_topic:
        with st.spinner("Generating..."):
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(f"{SYSTEM_PROMPT}\n\nTOPIC: {user_topic}")
            st.write(response.text)