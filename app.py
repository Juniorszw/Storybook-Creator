import streamlit as st
import google.generativeai as genai
import os
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# 1. SETUP: Load Environment Variables
load_dotenv()

# Get keys from .env
google_key = os.getenv("GEMINI_API_KEY")
hf_key = os.getenv("HUGGINGFACE_API_KEY")

# Safety Check: Stop if keys are missing
if not google_key:
    st.error("GEMINI_API_KEY not found! Please check your .env file.")
    st.stop()

if not hf_key:
    st.error("HUGGINGFACE_API_KEY not found! Please check your .env file.")
    st.stop()

# Configure Gemini
genai.configure(api_key=google_key)
model = genai.GenerativeModel('gemini-flash-latest')

# Configure Hugging Face (SDXL Model)
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {hf_key}"}

# Generate Image from Text 
def generate_image(prompt):
    """
    Sends the text prompt to Hugging Face and returns the actual image.
    """
    payload = {"inputs": prompt}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        image_bytes = response.content
        # Convert raw data into an image file
        image = Image.open(BytesIO(image_bytes))
        return image
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# 2. PROMPT ENGINEERING
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
      "story_text": "The narrative text (rhyming couplets suitable for children).",
      "image_prompt": "A highly detailed description of the visual scene for an AI image generator. Include style keywords like 'watercolor', 'warm lighting'."
    },
    ... (repeat for 3 pages)
  ]
}
"""

st.set_page_config(page_title="AI Storybook Phase 3", page_icon="🎨")

# 3. Sidebar
with st.sidebar:
    st.header("How to use")
    st.write("1. Enter a topic.")
    st.write("2. Click 'Generate'.")
    st.info("Phase 3 Active: Real Image Generation Enabled! 🎨")

st.title("Storybook Creator: Multimodal Build")

# User Input
user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")

# 4. GENERATION LOGIC
if st.button("Generate Storyboard"):
    if not user_topic:
        st.warning("Please enter a topic first.")
    else:
        with st.spinner("Writing story and painting pictures... (This may take 30s)"):
            try:
                # STEP A: GENERATE TEXT (Gemini) 
                full_prompt = f"{SYSTEM_PROMPT}\n\nTOPIC: {user_topic}"
                response = model.generate_content(full_prompt)
                
                # Clean JSON
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                story_data = json.loads(clean_text)
                
                st.success(f"Generated: {story_data['title']}")
                st.divider()
                
                # STEP B: GENERATE IMAGES (Hugging Face)
                for page in story_data['pages']:
                    with st.container():
                        st.subheader(f"Page {page['page_number']}")
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.info("🎨 Generating Art...")
                            
                            # CALL THE NEW FUNCTION HERE
                            real_image = generate_image(page['image_prompt'])
                            
                            if real_image:
                                st.image(real_image, caption=page['image_prompt'])
                            else:
                                st.error("Image generation failed (Check API quota).")
                        
                        with col2:
                            st.markdown(f"### 📖 Story")
                            st.write(page['story_text'])
                            st.caption("🔊 Audio Pending")
                        
                    st.divider()

            except Exception as e:
                st.error(f"An error occurred: {e}")