import base64
import os
from io import BytesIO

import requests
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from PIL import Image

from src.model_langchain import HTPModel

# Constants
MAX_IMAGE_SIZE = (800, 800)

# Supported languages and their codes
SUPPORTED_LANGUAGES = {
    "English": "en"
}

# Example
SAMPLE_IMAGES = {
    "example1": "example/example1.jpg",
    "example2": "example/example2.jpg",
    "example3": "example/example3.jpg",
    "example4": "example/example4.jpg",
}

# Language dictionaries
LANGUAGES = {
    "en": {
        "app_title": "🏡 House-Tree-Person Projective Drawing Test",
        "welcome_message": "Welcome to the House-Tree-Person (HTP) projective drawing test application.",
        "instructions_title": "📋 Test Instructions",
        "instructions": """
            **Please read the following instructions carefully:**

            1. **Fill the API Key**: Fill the API Key in the sidebar to authenticate with the Google Gemini API.
            2. **Drawing Requirements**: On a piece of white paper, use a pencil to draw a picture that includes a **house**, **trees**, and a **person**.
            3. **Be Creative**: Feel free to draw as you like. There are no right or wrong drawings.
            4. **No Aids**: Do not use rulers, erasers, or any drawing aids.
            5. **Take Your Time**: There is no time limit. Take as much time as you need.
            6. **Upload the Drawing**: Once you've completed your drawing, take a clear photo or scan it, and upload it using the sidebar.
            7. **Sample Drawings**: We have prepared sample drawings from publicly available internet data for you to explore. You can find them in the sidebar.
            
            **Note**: All information collected in this test will be kept strictly confidential.
        """,
        "upload_prompt": "👉 Please upload your drawing using the sidebar.",
        "analysis_complete": "✅ **Analysis Complete!** You can download the full report from the sidebar.",
        "analysis_summary": "🔍 Analysis Summary:",
        "image_uploaded": "⚠️ Image uploaded. Click **Start Analysis** in the sidebar to proceed.",
        "disclaimer": """
            **Disclaimer**:
            - This test is for reference only and cannot replace professional psychological diagnosis.
            - If you feel uncomfortable or experience emotional fluctuations during the test, please stop immediately and consider seeking help from a professional.
            """,
        "model_settings": "🍓 Model Settings",
        "analysis_settings": "🔧 Analysis Settings",
        "report_language": "Report Language:",
        "upload_drawing": "🖼️ Upload Your Drawing:",
        "start_analysis": "🚀 Start Analysis",
        "reset": "♻️ Reset",
        "download_report": "⬇️ Download Report",
        "download_help": "Download the analysis report as a text file.",
        "uploaded_drawing": "📷 Your Uploaded Drawing",
        "error_no_image": "Please upload an image first.",
        "analyzing_image": "Analyzing image, please wait...",
        "error_analysis": "Error during analysis: ",
        "session_reset": "Session has been reset. You can now upload a new image.",
        "sample_drawings": "📊 Sample Drawings",
        "load_sample": "Load Sample {}",
        "sample_loaded": "Sample {} loaded. Click 'Start Analysis' to analyze.",
        "error_no_api_key": "❌ Please enter your API key in the sidebar before starting the analysis.",
        "ai_disclaimer": "NOTE: AI-generated content, for reference only. Not a substitute for medical diagnosis.",
    }
}

# Helper function to get text based on current language
def get_text(key):
    return LANGUAGES[st.session_state['language_code']][key]

# Helper functions
def pil_to_base64(image: Image.Image, format: str = "JPEG") -> str:
    """Convert PIL image to base64 string."""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
def resize_image(image: Image.Image, max_size: tuple = MAX_IMAGE_SIZE) -> Image.Image:
    """Resize image if it exceeds max_size."""
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size)
    return image

def analyze_image(model) -> None:
    """Perform image analysis and update session state."""
    if st.session_state['image_data'] is None:
        st.error(get_text("error_no_image"))
        return

    inputs = {
        "image_path": st.session_state['image_data'],
        "language": st.session_state['language_code']
    }

    try:
        with st.spinner(get_text("analyzing_image")):
            response = model.workflow(**inputs)
            st.session_state['analysis_result'] = response
    except requests.RequestException as e:
        st.error(f"{get_text('error_analysis')}{str(e)}")

def reset_session() -> None:
    """Reset session state."""
    for key in ['image_data', 'image_display', 'analysis_result']:
        if key in st.session_state:
            del st.session_state[key]
    st.success(get_text("session_reset"))

def export_report() -> None:
    if st.session_state.get('analysis_result'):
        if st.session_state["analysis_result"]['classification'] is True:
            signal = st.session_state['analysis_result'].get('signal', '')
            final_report = st.session_state['analysis_result'].get('final', '').replace("<output>", "").replace("</output>", "")
            disclaimer = get_text("ai_disclaimer")
            export_data = f"{disclaimer}\n\n{signal}\n\n{final_report}"
        else:
            signal = st.session_state['analysis_result'].get('fix_signal', '')
            disclaimer = get_text("ai_disclaimer")
            export_data = f"{disclaimer}\n\n{signal}"
            
        st.sidebar.download_button(
            label=get_text("download_report"),
            data=export_data,
            file_name=f"HTP_Report_{st.session_state['language_code']}.txt",
            mime="text/plain",
            help=get_text("download_help")
        )

# UI components
def sidebar(model) -> None:
    """Render sidebar components."""
    st.sidebar.image("assets/logo2.png", use_column_width=True)
    
    st.sidebar.markdown(f"## {get_text('sample_drawings')}")
    col1, col2 = st.sidebar.columns(2)
    for idx, (sample_name, sample_path) in enumerate(SAMPLE_IMAGES.items()):
        col = col1 if idx % 2 == 0 else col2
        with col:
            if st.button(get_text("load_sample").format(idx+1), key=f"load_sample_{idx}"):
                with open(sample_path, "rb") as f:
                    image = Image.open(f)
                    image = resize_image(image)
                    st.session_state['image_data'] = pil_to_base64(image)
                    st.session_state['image_display'] = image
                    st.session_state['current_sample'] = sample_name

    st.sidebar.markdown(f"## {get_text('analysis_settings')}")
    # Language Selection
    language = st.sidebar.selectbox(
        get_text("report_language"),
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state['language']),
        help=get_text("report_language")
    )
    if language != st.session_state['language']:
        # Update language in session state
        st.session_state['language'] = language
        st.session_state['language_code'] = SUPPORTED_LANGUAGES[language]
        st.rerun()
        
    # Image Upload
    uploaded_file = st.sidebar.file_uploader(
        get_text("upload_drawing"),
        type=["jpg", "jpeg", "png"],
        help=get_text("upload_drawing")
    )
    if uploaded_file:
        image = Image.open(uploaded_file)
        image = resize_image(image)
        st.session_state['image_data'] = pil_to_base64(image)
        st.session_state['image_display'] = image  # For displaying in main content
    
    st.sidebar.markdown(f"## {get_text('model_settings')}")
    api_key = st.sidebar.text_input("Google Gemini API Key", help="API Key for authentication", type="password")
    st.session_state.api_key = api_key
    
    # Buttons
    st.sidebar.markdown("---")
    if st.sidebar.button(get_text("start_analysis")):
        if not st.session_state.api_key:
            st.error(get_text("error_no_api_key"))
        else:
            analyze_image(model)

    if st.sidebar.button(get_text("reset")):
        reset_session()

    export_report()

def main_content() -> None:
    """Render main content area."""
    st.title(get_text("app_title"))
    st.write(get_text("welcome_message"))

    # Instructions
    with st.expander(get_text('instructions_title'), expanded=True):
        st.markdown(get_text("instructions"))

    # Display Uploaded Image or Placeholder
    if st.session_state.get('image_display'):
        st.image(
            st.session_state['image_display'],
            caption=get_text("uploaded_drawing"),
            use_column_width=True
        )
    else:
        st.info(get_text("upload_prompt"))

    # Display Analysis Results
    if st.session_state.get('analysis_result'):
        st.success(get_text("analysis_complete"))
        with st.expander(get_text("analysis_summary"), expanded=True):
            if st.session_state['analysis_result']['classification'] is False:
                st.write(
                    st.session_state['analysis_result'].get('fix_signal', get_text('error_no_image'))
                )
            else:
                st.write(st.session_state['analysis_result'].get('signal', get_text('error_no_image')))
    elif st.session_state.get('image_data') and not st.session_state.get('analysis_result'):
        st.warning(get_text("image_uploaded"))

    # Footer
    st.markdown("---")
    st.markdown(get_text("disclaimer"))

# Main app
def main() -> None:
    """Main application entry point."""
    st.set_page_config(page_title="PsyDraw: HTP Test", page_icon="🏡", layout="wide")
        
    # Initialize session state variables if not present
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = os.getenv("GOOGLE_API_KEY") or "" 
    if 'language' not in st.session_state:
        st.session_state['language'] = 'English'
    if 'language_code' not in st.session_state:
        st.session_state['language_code'] = SUPPORTED_LANGUAGES[st.session_state['language']]
    for key in ['image_data', 'image_display', 'analysis_result']:
        if key not in st.session_state:
            st.session_state[key] = None
            
    # Initialize model
    MULTIMODAL_MODEL = "gemini-2.5-flash"
    TEXT_MODEL = "gemini-2.5-flash"
    
    text_model = ChatGoogleGenerativeAI(
        model=TEXT_MODEL,
        temperature=0.2,
        google_api_key=st.session_state.api_key,
    )
    multimodal_model = ChatGoogleGenerativeAI(
        model=MULTIMODAL_MODEL,
        temperature=0.2,
        google_api_key=st.session_state.api_key,
    )
    model = HTPModel(
        text_model=text_model,
        multimodal_model=multimodal_model,
        use_cache=True,
    )

    sidebar(model)
    main_content()

if __name__ == "__main__":
    main()