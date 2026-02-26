import streamlit as st
import google.generativeai as genai
import os
import json
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import random
from gtts import gTTS

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
@st.cache_data
def generate_image(prompt, seed):
    """
    Sends the text prompt to Hugging Face and returns the actual image.
    """
    payload = {"inputs": prompt,
        "parameters": {"seed": seed}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        image_bytes = response.content
        # Convert raw data into an image file
        image = Image.open(BytesIO(image_bytes))
        return image
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Generate Audio from Text
@st.cache_data
def generate_audio(text):
    """
    Converts the story text into speech and returns it as audio bytes.
    """
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        print(f"Error generating audio: {e}")
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
  "character_design": "A strict 1-sentence physical description of the main character (e.g., 'A 10-year-old boy with messy brown hair, wearing a red t-shirt and blue jeans.').",
  "pages": [
    {
      "page_number": 1,
"story_text": "The narrative text for the page. Write a fully developed, engaging paragraph of 4 to 6 sentences. Focus on descriptive storytelling rather than just a short rhyme.",
      "image_prompt": "Describe the background and action for this scene. DO NOT describe the character's physical appearance here. Include style keywords like 'watercolor'."    }
  ]
}
"""

st.set_page_config(page_title="AI Storybook Phase 3", page_icon="🎨")

# 3. Sidebar & Session State
if 'story_seed' not in st.session_state:
    st.session_state.story_seed = random.randint(1, 1000000)

if 'story_data' not in st.session_state:
    st.session_state.story_data = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

with st.sidebar:
    st.header("How to use")
    st.write("1. Enter a topic.")
    st.write("2. Click 'Generate'.")
    st.info("Phase 3 Active: Real Image Generation Enabled! 🎨")

st.title("Storybook Creator: Multimodal Build")

# User Input
user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")

# 4. GENERATION LOGIC (Data Fetching Only)
if st.button("Generate Storyboard"):
    if not user_topic:
        st.warning("Please enter a topic first.")
    else:
        st.session_state.story_seed = random.randint(1, 1000000) 
        with st.spinner("Writing story and painting pictures... (This may take 30s)"):
            try:
                # STEP A: GENERATE TEXT (Gemini)
                full_prompt = f"{SYSTEM_PROMPT}\n\nTOPIC: {user_topic}"
                response = model.generate_content(full_prompt)
                
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                
                # SAVE TO MEMORY INSTEAD OF JUST A VARIABLE
                st.session_state.story_data = json.loads(clean_text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

# 5. DISPLAY LOGIC (Interactive UI)
# If a story exists in memory, display it
if st.session_state.story_data:
    story_data = st.session_state.story_data
    
    st.success(f"Generated: {story_data['title']}")
    st.divider()
    
    # Grab the master character description and total pages
    character_context = story_data.get('character_design', '')
    total_pages = len(story_data['pages'])
    
    # PAGINATION LOGIC 
    # Instead of a loop, we only grab the page the user is currently on
    current_index = st.session_state.current_page
    page = story_data['pages'][current_index]
    
    with st.container():
        st.subheader(f"Page {page['page_number']} of {total_pages}")
        
        # Left side = Image (col1), Right side = Text (col2)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info("🎨 Image Settings")
            initial_full_prompt = f"{character_context} {page['image_prompt']}"
            widget_key = f"img_edit_{page['page_number']}"
            current_prompt = st.session_state.get(widget_key, initial_full_prompt)
            
            with st.spinner("Painting image..."):
                real_image = generate_image(current_prompt, st.session_state.story_seed)
                if real_image:
                    st.image(real_image)
                else:
                    st.error("Image generation failed (Check API quota).")
            
            st.text_area("Edit the full image prompt:", value=initial_full_prompt, key=widget_key, height=200)
            
        with col2:
            st.markdown(f"### 📖 Story")
            
            edited_text = st.text_area(
                "Edit your story text here:", 
                value=page['story_text'], 
                key=f"edit_{page['page_number']}", 
                height=300
            )
            
            audio_bytes = generate_audio(edited_text)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
            else:
                st.error("Audio generation failed.")
                
    st.divider()
    
    # NAVIGATION BUTTONS
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        # Only show "Previous" if we are not on the first page
        if current_index > 0:
            if st.button("⬅️ Previous Page"):
                st.session_state.current_page -= 1
                st.rerun()
                
    with nav_col3:
        # Only show "Next" if we are not on the last page
        if current_index < total_pages - 1:
            if st.button("Next Page ➡️"):
                st.session_state.current_page += 1
                st.rerun()