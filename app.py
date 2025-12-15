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

# 2. PROMPT ENGINEERING (Basic)
SYSTEM_PROMPT = """
You are a professional children's book author.
Generate a 3-page story topic provided by the user.
Output strict JSON format.

Structure:
{
  "title": "Story Title",
  "pages": [
    {
      "page_number": 1,
      "story_text": "The narrative text for this page.",
      "image_prompt": "A detailed image description."
    }
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