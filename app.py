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
from fpdf import FPDF
import tempfile

# 1. Setup
load_dotenv()

# Get keys from .env
google_key = os.getenv("GEMINI_API_KEY")
hf_key = os.getenv("HUGGINGFACE_API_KEY")

# Stop if keys are missing
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
    response = requests.post(API_URL, headers=headers, json=payload)
        
    # Check if Hugging Face actually gave us a successful "OK" status (200)
    if response.status_code == 200:
        try:
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            # Catch the scenario where HF sends a 200 OK but it is not a picture
            print(f"Failed to open image. Raw API response: {response.text[:200]}")
            return None
    else:
        # Catch actual HTTP errors
        print(f"Hugging Face Error ({response.status_code}): {response.text}")
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
    
# Generate PDF from Story Data
def create_pdf(story_data, seed):
    """Compiles the story text and images into a landscape PDF."""
    pdf = FPDF(orientation='L', unit='mm', format='A4') # L = Landscape
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Clean AI text of weird characters for the PDF Compiler
    def safe_text(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    # Cover Page
    pdf.add_page()
    cover_prompt = story_data.get('cover_prompt', '')
    cover_seed = story_data.get('cover_seed', seed)
    cover_img = generate_image(cover_prompt, cover_seed)
    
    if cover_img:
        # Save cover image to a temporary hidden file for FPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            cover_img.save(tmp.name)
            pdf.image(tmp.name, x=78, y=20, w=140)
            tmp_path = tmp.name
        os.remove(tmp_path)
        
    pdf.set_y(170)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 10, safe_text(story_data['title']), ln=True, align='C')

    # Story Pages
    for page in story_data['pages']:
        pdf.add_page()
        
        # Add image to the left side
        img_prompt = page.get('full_image_prompt', page['image_prompt'])
        page_seed = page.get('image_seed', seed)
        page_img = generate_image(img_prompt, page_seed)
        if page_img:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                page_img.save(tmp.name)
                pdf.image(tmp.name, x=15, y=30, w=120) 
                tmp_path = tmp.name
            os.remove(tmp_path)
            
        # Add text to the right side
        pdf.set_xy(145, 40)
        pdf.set_font("Arial", '', 14)
        pdf.multi_cell(135, 8, safe_text(page['story_text']))
        
        # Add page number to the bottom right
        pdf.set_y(180)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, f"Page {page['page_number']}", ln=True, align='R')

    # Return the raw PDF bytes for Streamlit to download
    return pdf.output(dest='S').encode('latin-1')


# 2. Prompt engineering
def get_system_prompt(num_pages):
    """Generates the system prompt dynamically based on the requested page count."""
    return f"""
You are a professional children's book author and illustrator. 
I will give you a topic. You must generate a {num_pages}-page story.
You must output the result in strict JSON format. 
Do not add any markdown formatting (like ```json). Just the raw JSON.

Structure:
{{
  "title": "Story Title",
  "character_design": "A strict 1-sentence physical description of the main character (e.g., 'A 10-year-old boy with messy brown hair, wearing a red t-shirt and blue jeans.').",
  "pages": [
    {{
      "page_number": 1,
      "story_text": "The narrative text for the page. Write a fully developed, engaging paragraph of 4 to 6 sentences. Focus on descriptive storytelling rather than just a short rhyme.",
      "image_prompt": "Describe the background and action for this scene. DO NOT describe the character's physical appearance here. Include style keywords like 'watercolor'."    
    }}
  ]
}}
(Make sure the "pages" array contains exactly {num_pages} page objects)
"""

st.set_page_config(page_title="AI Storybook", page_icon="🎨")

# 3. Sidebar & Session State
if 'story_seed' not in st.session_state:
    st.session_state.story_seed = random.randint(1, 1000000)

if 'story_data' not in st.session_state:
    st.session_state.story_data = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = -1

with st.sidebar:
    st.header("How to use")
    st.write("1. Enter a topic.")
    st.write("2. Click 'Generate Storybook'.")
    st.write("3. Click on Image Prompt to edit image to your liking.")
    st.write("4. Click on Story Text to edit story to your liking.")
    st.write("5. Press CTRL + Enter to apply changes.")
    st.write("6. Click on ▶ button to play audio.")
    st.write("7. Click on Next Page ➡️ to navigate.")
    st.divider()
    if st.button("🔄 Start a New Book", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("Storybook Creator")

# User input
col_input1, col_input2 = st.columns([3, 1])
with col_input1:
    user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")
with col_input2:
    # Add a number input to let the user select pages
    selected_pages = st.number_input("Number of pages", min_value=1, max_value=10, value=3)

# 4. Generation logic
if st.button("Generate Storybook"):
    if not user_topic:
        st.warning("Please enter a topic first.")
    else:
        st.session_state.story_seed = random.randint(1, 1000000)
        st.session_state.current_page = -1
        with st.spinner("Writing story and painting pictures... (This may take 30s)"):
            try:
                # Generate dynamic prompt based on user's page count
                dynamic_prompt = get_system_prompt(selected_pages)
                
                # Generate text using Gemini
                full_prompt = f"{dynamic_prompt}\n\nTOPIC: {user_topic}"
                response = model.generate_content(full_prompt)
                
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                
                # Save to memory instead of just a variable
                st.session_state.story_data = json.loads(clean_text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

# 5. Display Logic
# Display story if it exists in memory
if st.session_state.story_data:
    story_data = st.session_state.story_data
    
    st.divider()
    
    # Grab the master character description and total pages
    character_context = story_data.get('character_design', '')
    total_pages = len(story_data['pages'])
    
    # Pagination Logic
    current_index = st.session_state.current_page
    
    if current_index == -1:
        # Cover Page Logic
        # Use columns to keep the cover centered and not stretched too wide
        spacer1, cover_col, spacer2 = st.columns([1, 2, 1])
        
        with cover_col:
            with st.container(border=True):
                
                # Initialize permanent cover prompt if it does not exist
                if 'cover_prompt' not in story_data:
                    story_data['cover_prompt'] = f"{character_context} A beautiful storybook cover illustration for the story '{story_data['title']}'. Vibrant colors."
                
                # Assign a specific seed for the cover page
                if 'cover_seed' not in story_data:
                    story_data['cover_seed'] = st.session_state.story_seed
                
                widget_key = "img_edit_cover"
                current_prompt = st.session_state.get(widget_key, story_data['cover_prompt'])
                
                with st.spinner("Painting cover image..."):
                    real_image = generate_image(current_prompt, story_data['cover_seed'])
                    if real_image:
                        st.image(real_image, use_container_width=True)
                    else:
                        st.error("Image generation failed (Check API quota).")
                
                # Regenerate Button for Cover 
                if st.button("🔄 Regenerate Image", use_container_width=True):
                    story_data['cover_seed'] = random.randint(1, 1000000)
                    st.rerun()

                # Editable Title beneath the image
                edited_title = st.text_input("Edit Book Title:", value=story_data['title'], key="title_edit")
                story_data['title'] = edited_title     
                           
                # PDF Export Feature
                st.write("") 
                col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1]) # 3 columns to center the buttons
                
                with col_dl2:
                    # Compile the book
                    if st.button("🛠️ Compile to PDF", use_container_width=True):
                        with st.spinner("Assembling your book..."):
                            pdf_bytes = create_pdf(story_data, st.session_state.story_seed)
                            st.session_state.pdf_data = pdf_bytes
                            
                    # Show download button only after compilation is done
                    if 'pdf_data' in st.session_state:
                        st.success("PDF Ready!")
                        st.download_button(
                            label="⬇️ Download Your Storybook",
                            data=st.session_state.pdf_data,
                            file_name=f"{story_data['title'].replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                # Render the widget and update permanent memory
                edited_cover = st.text_area("Edit cover prompt:", value=story_data['cover_prompt'], key=widget_key, height=100)
                story_data['cover_prompt'] = edited_cover


    else:
        # Story Page Logic
        page = story_data['pages'][current_index]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.container(border=True):
                # Initialize permanent full prompt if it does not exist
                if 'full_image_prompt' not in page:
                    # Defensive fallback in case the AI hallucinates and forgets the key
                    fallback_prompt = "A beautiful storybook illustration."
                    base_prompt = page.get('image_prompt', fallback_prompt)
                    page['full_image_prompt'] = f"{character_context} {base_prompt}"

                # Assign a specific seed for this page
                if 'image_seed' not in page:
                    page['image_seed'] = st.session_state.story_seed
                
                widget_key = f"img_edit_{page['page_number']}"
                current_prompt = st.session_state.get(widget_key, page['full_image_prompt'])
                
                with st.spinner("Painting image..."):
                    real_image = generate_image(current_prompt, page['image_seed'])
                    if real_image:
                        st.image(real_image)
                    else:
                        st.error("Image generation failed (Check API quota).")
                
                # Regenerate Button
                if st.button("🔄 Regenerate Image", key=f"regen_{page['page_number']}", use_container_width=True):
                    page['image_seed'] = random.randint(1, 1000000)
                    st.rerun()
                
                # Render widget and update permanent memory
                edited_prompt = st.text_area("Edit the full image prompt:", value=page['full_image_prompt'], key=widget_key, height=170)
                page['full_image_prompt'] = edited_prompt

        with col2:
            with st.container(border=True):
                edited_text = st.text_area(
                    "Edit your story text here:", 
                    value=page['story_text'], 
                    key=f"edit_{page['page_number']}", 
                    height=485
                )
                
                page['story_text'] = edited_text
                
                audio_bytes = generate_audio(edited_text)
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3')
                else:
                    st.error("Audio generation failed.")      

                st.markdown(f"<div style='text-align: right; color: gray;'><b>pg {page['page_number']}</b></div>", unsafe_allow_html=True)

    st.divider()
    
    # Navigation Buttons
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        # Show "Previous" if user past the cover page
        if current_index > -1:
            if st.button("⬅️ Previous Page"):
                st.session_state.current_page -= 1
                st.rerun()
                
    with nav_col3:
        # Show "Next" if user not on the last page
        if current_index < total_pages - 1:
            if st.button("Next Page ➡️"):
                st.session_state.current_page += 1
                st.rerun()
        # Show "Go to Front" if user on the last page
        elif current_index == total_pages - 1:
            if st.button("🔄 Go to Front"):
                st.session_state.current_page = -1  # -1 is our cover page
                st.rerun()