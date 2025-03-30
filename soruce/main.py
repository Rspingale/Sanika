import os
import time
import pygame
from gtts import gTTS
import streamlit as st
import speech_recognition as sr
from googletrans import LANGUAGES, Translator
import asyncio
import concurrent.futures
import base64

# Set page configuration
st.set_page_config(
    page_title="Real-Time Language Translator",
    page_icon="🌐",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Color palette */
    :root {
        --primary: #3F51B5;
        --primary-light: #C5CAE9;
        --primary-dark: #303F9F;
        --accent: #FF4081;
        --text-primary: #212121;
        --text-secondary: #757575;
        --background: #FAFAFA;
        --card-bg: #FFFFFF;
        --success: #4CAF50;
        --error: #F44336;
    }
    
    body {
        background-color: var(--background);
        color: var(--text-primary);
    }
    
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: var(--primary-dark);
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(to right, #000000, #192b8e);
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .sub-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: var(--primary-dark);
        margin-bottom: 1rem;
    }
    
    .language-selector {
        background-color: var(--card-bg);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary);
    }
    
    .translator-container {
        background-color: var(--card-bg);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--accent);
    }
    
    .button-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 1.5rem 0;
    }
    
    .stButton>button {
        border-radius: 5px;
        font-weight: 500;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:first-child {
        background-color: var(--success);
        color: white;
    }
    
    .stButton>button:last-child {
        background-color: var(--error);
        color: white;
    }
    
    .stButton>button:hover {
        opacity: 0.9;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        background-color:#1e2240;
        border-radius: 10px;
        margin-top: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stSelectbox > div > div {
        background-color: var(--card-bg);
    }
    
    /* Fix for selectbox text color */
    .stSelectbox label {
        color: #000000 !important;
    }
    
    .stSelectbox div[data-baseweb="select"] div {
        color: #000000 !important;
    }
    
    .stSelectbox div[data-baseweb="select"] div[aria-selected="true"] {
        color: #000000 !important;
    }
    
    .stSelectbox span {
        color: #000000 !important;
    }
    
    .output-area {
        background-color: var(--background);
        padding: 1.5rem;
        border-radius: 10px;
        min-height: 200px;
        border: 1px solid #E0E0E0;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
        color: #000000 !important;
        font-size: 1.1rem;
    }
    
    .translation-text {
        color: #000000 !important;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    
    .original-text {
        color: var(--primary-dark);
        font-weight: 500;
    }
    
    .translated-text {
        color: var(--accent);
        font-weight: 500;
    }
    
    .attribution {
        font-style: italic;
        color: var(--text-secondary);
        margin-top: 0.5rem;
    }
    
    /* Status indicators */
    .status-listening {
        color: var(--primary);
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    .status-processing {
        color: var(--accent);
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    .status-translating {
        color: var(--primary-dark);
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    .status-error {
        color: var(--error);
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    /* Project description */
    .project-description {
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: var(--card-bg);
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        color: #000000;
    }
    
    .project-description p {
        color: #000033;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    
    /* Force black text in the output area */
    .output-area p {
        color: #000000 !important;
    }
    
    .output-area div {
        color: #000000 !important;
    }
    
    .language-code-display {
        text-align: center;
        color: #000033 !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

isTranslateOn = False

# Use standard Translator
translator = Translator()
pygame.mixer.init()  # Initialize the mixer module.

# Create a mapping between language names and language codes
language_mapping = {name: code for code, name in LANGUAGES.items()}

# Add Hindi and Marathi explicitly if they're not already in the mapping
if 'hindi' not in language_mapping.values():
    language_mapping['Hindi'] = 'hi'
if 'marathi' not in language_mapping.values():
    language_mapping['Marathi'] = 'mr'

def get_language_code(language_name):
    return language_mapping.get(language_name, language_name)

# Synchronous translation function
def sync_translate(text, src, dest):
    # Create a new translator instance for each call to avoid issues
    t = Translator()
    # Get the translation result
    translation = t.translate(text, src=src, dest=dest)
    # If it's a coroutine, we need to run it in an event loop
    if asyncio.iscoroutine(translation):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the coroutine to completion
            result = loop.run_until_complete(translation)
        finally:
            loop.close()
        return result
    else:
        # If it's not a coroutine, return it directly
        return translation

# Make translator_function async but use synchronous translate
async def translator_function(spoken_text, from_language, to_language):
    # Use a ThreadPoolExecutor to run the synchronous function
    with concurrent.futures.ThreadPoolExecutor() as executor:
        translated = await asyncio.get_event_loop().run_in_executor(
            executor, 
            sync_translate, 
            spoken_text, 
            from_language, 
            to_language
        )
    return translated

def text_to_voice(text_data, to_language):
    myobj = gTTS(text=text_data, lang='{}'.format(to_language), slow=False)
    myobj.save("cache_file.mp3")
    audio = pygame.mixer.Sound("cache_file.mp3")  # Load a sound.
    audio.play()
    os.remove("cache_file.mp3")

# Make main_process async
async def main_process(output_placeholder, from_language, to_language):
    global isTranslateOn
    
    while isTranslateOn:
        rec = sr.Recognizer()
        with sr.Microphone() as source:
            output_placeholder.markdown("<div class='output-area'><div class='translation-text'><span class='status-listening'>Listening...</span></div></div>", unsafe_allow_html=True)
            rec.pause_threshold = 1
            audio = rec.listen(source, phrase_time_limit=10)
        
        try:
            output_placeholder.markdown("<div class='output-area'><div class='translation-text'><span class='status-processing'>Processing...</span></div></div>", unsafe_allow_html=True)
            spoken_text = rec.recognize_google(audio, language='{}'.format(from_language))
            print(f"Recognized text: {spoken_text}")
            
            output_placeholder.markdown("<div class='output-area'><div class='translation-text'><span class='status-translating'>Translating...</span></div></div>", unsafe_allow_html=True)
            translated_text = await translator_function(spoken_text, from_language, to_language)
            
            # Check if translated_text is a coroutine
            if asyncio.iscoroutine(translated_text):
                translated_text = await translated_text
            
            # Display both original and translated text with improved styling
            output_placeholder.markdown(
                f"""<div class='output-area'>
                    <div class='translation-text'>
                        <p><span class='original-text'>Original ({from_language}):</span> {spoken_text}</p>
                        <p><span class='translated-text'>Translated ({to_language}):</span> {translated_text.text}</p>
                    </div>
                </div>""", 
                unsafe_allow_html=True
            )
            print(f"Translated text: {translated_text.text}")
            
            # Convert translated text to speech
            text_to_voice(translated_text.text, to_language)
    
        except sr.UnknownValueError:
            print("Could not understand audio")
            output_placeholder.markdown(
                "<div class='output-area'><div class='translation-text'><span class='status-error'>Could not understand audio. Please try again.</span></div></div>", 
                unsafe_allow_html=True
            )
        except Exception as e:
            print(f"Error: {e}")
            output_placeholder.markdown(
                f"<div class='output-area'><span class='status-error'>Error: {e}</span></div>", 
                unsafe_allow_html=True
            )
            import traceback
            traceback.print_exc()

# UI layout with enhanced styling
# logo_path = "path/to/your/image.png"


# Corrected path (use raw string `r""` to avoid escape issues)
logo_path = r"C:\Users\rupes\Desktop\JCEI_logo.png"

# Convert image to Base64
with open(logo_path, "rb") as img_file :
    encoded_image = base64.b64encode(img_file.read()).decode("utf-8")


# Display the logo with the header (Centered)
st.markdown(
    f"""
    <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
        <img src="data:image/png;base64,{encoded_image}" width="120"/>
        <h1 style="margin-top: 10px;">Real-Time Language Translator</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# Project description
st.markdown("""
<div class="project-description">
    <p>This application allows you to translate speech in real-time between multiple languages.</p>
    <p>Simply select your source and target languages, click "Start", and begin speaking!</p>
</div>
""", unsafe_allow_html=True)

# Create a list of languages with Hindi and Marathi at the top for easy access
language_list = list(LANGUAGES.values())
# Move Hindi and Marathi to the top if they exist
if 'hindi' in language_list:
    language_list.remove('hindi')
    language_list.insert(0, 'hindi')
if 'marathi' in language_list:
    language_list.remove('marathi')
    language_list.insert(1, 'marathi')

# Language selection in columns
# st.markdown("<div class='language-selector'>", unsafe_allow_html=True)
st.markdown("<h2 class='sub-header'>Select Languages</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    from_language_name = st.selectbox("Source Language:", language_list)
with col2:
    to_language_name = st.selectbox("Target Language:", language_list)

# Convert language names to language codes
from_language = get_language_code(from_language_name)
to_language = get_language_code(to_language_name)

# Remove the language code display from here
st.markdown("</div>", unsafe_allow_html=True)

# Move the language code display to the translator container if needed
# st.markdown("<div class='translator-container'>", unsafe_allow_html=True)
st.markdown("<h2 class='sub-header'>Translation Output</h2>", unsafe_allow_html=True)

# Output placeholder
output_placeholder = st.empty()
output_placeholder.markdown("<div class='output-area'>Click 'Start' to begin translation</div>", unsafe_allow_html=True)

# Button styling with custom HTML
st.markdown("<div class='button-container'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    start_button = st.button("Start", key="start")
with col2:
    stop_button = st.button("Stop", key="stop")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Check if "Start" button is clicked
if start_button:
    if not isTranslateOn:
        isTranslateOn = True
        # Run the async function with asyncio
        asyncio.run(main_process(output_placeholder, from_language, to_language))

# Check if "Stop" button is clicked
if stop_button:
    isTranslateOn = False

# Footer with attribution
st.markdown("""
<div class='footer'>
    <h3>About This Project</h3>
    <p>This Real-Time Language Translator was developed by JCOE students for Project Based Learning Subject.</p>
    <p class='attribution'>Created by: <strong>Sanika Sarode</strong> and <strong>Prajwal Kanade</strong></p>
    <p>© 2023 JCOE - All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)