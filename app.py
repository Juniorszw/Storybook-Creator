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

st.title("Storybook Creator: Feature Prototype")

# User Input
user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")

if st.button("Generate"):
    st.success("API Key found! Ready to generate.")