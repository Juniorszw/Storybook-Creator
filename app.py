import streamlit as st

st.title("Storybook Creator: Feature Prototype")

# User Input
user_topic = st.text_input("What should the story be about?", placeholder="e.g., A brave robot")

if st.button("Generate"):
    st.write(f"You requested a story about: {user_topic}")