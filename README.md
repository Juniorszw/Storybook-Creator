# Storybook Creator 🎨

## Step 1: Prerequisites
Before running my application locally, please ensure you have the following installed and configured:
* **Python 3.10** or higher
* A **Google Gemini API Key** (Available via Google AI Studio)
* A **Hugging Face API Key** (Available via Hugging Face account settings. *Note: I deposited credits into my account, thus I have more image generation chances.*)

## Step 2: Installation
First, clone or extract the project repository and navigate into the root directory using your terminal. I highly recommend creating a Python virtual environment to prevent dependency conflicts with your local machine:

```bash
# Create the virtual environment 
python -m venv venv 

# Activate the virtual environment (Windows) 
venv\Scripts\activate 

# Activate the virtual environment (Mac/Linux) 
source venv/bin/activate
```

Next, install all required Python packages using the provided pip command:
```bash
pip install streamlit google-generativeai requests Pillow python-dotenv gTTS fpdf
```

## Step 3: Environment Variables (.env Setup)
This application communicates with enterprise Generative AI models and requires secure API keys to function. Do not hardcode your keys into the `app.py` file.

1. In the root directory of the project, create a new file named exactly `.env`.
2. Open the `.env` file and add your API credentials exactly like this:

```text
GEMINI_API_KEY=your_gemini_api_key_here 
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
```

*Note: The `python-dotenv` library will securely load these keys at runtime. If the keys are missing, the application’s defensive programming will safely halt execution and display an error alert.*

## Step 4: Running the Application
Once the dependencies are installed and the `.env` file is securely configured, you can launch the application’s presentation layer.

Run this command in your terminal:
```bash
streamlit run app.py
```

The Streamlit framework will initialize the local server and automatically open a new tab in your default web browser (hosted at `http://localhost:8501`).

## Step 5: User Guide
1. **Enter a Topic:** Type a short narrative concept into the main text box. (e.g., *A brave robot exploring the forest*)
2. **Select Length:** Utilize the numeric slider to dictate the length of the book (from 1 to 10 pages).
3. **Generate:** Click **Generate Storybook** and allow the orchestration layer to process the asynchronous API calls.
4. **Co-Create (User-in-the-Loop):** Edit the generated narrative text directly within the text areas to personalize the story. Click the **Regenerate Image** button beneath any specific illustration to reroll the latent noise seed and generate a new visual variation for that page.
5. **Listen & Export:** Utilize the embedded audio player to hear the Text-to-Speech narration, and click **Compile to PDF** to download your finalized storybook.
