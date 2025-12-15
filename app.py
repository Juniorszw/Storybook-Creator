import streamlit as st
import google.generativeai as genai
import os
import json
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

# 4. GENERATION LOGIC
if st.button("Generate Storyboard"):
    if not user_topic:
        st.warning("Please enter a topic first.")
    else:
        with st.spinner("Orchestrating narrative and visual prompts..."):
            try:
                # Call Gemini API
                model = genai.GenerativeModel('gemini-flash-latest')
                full_prompt = f"{SYSTEM_PROMPT}\n\nTOPIC: {user_topic}"
                
                response = model.generate_content(full_prompt)
                
                # Parse JSON (Cleaning the output)
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                
                try:
                    story_data = json.loads(clean_text)
                except json.JSONDecodeError:
                    st.error("The AI returned invalid JSON. Please try again.")
                    st.stop()
                
# 5. DISPLAY RESULTS
                st.success(f"Generated: {story_data['title']}")
                st.divider()
                
                # Loop through the pages and display them
                for page in story_data['pages']:
                    with st.container():
                        st.subheader(f"Page {page['page_number']}")
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.warning("Image Prompt")
                            st.caption(page['image_prompt'])
                            # Placeholder image - Proof that we have a slot ready for Stable Diffusion
                            st.image("https://placehold.co/400x300?text=Stable+Diffusion+Pending", use_container_width=True)
                        
                        with col2:
                            st.success("Story Text")
                            st.write(f"### {page['story_text']}")
                            st.caption("Audio Integration Pending")
                        
                    st.divider()

                # Show the raw JSON to prove "Structure Compliance" for the report
                with st.expander("View Raw JSON (Technical Output)"):
                    st.json(story_data)

            except Exception as e:
                st.error(f"An error occurred: {e}")