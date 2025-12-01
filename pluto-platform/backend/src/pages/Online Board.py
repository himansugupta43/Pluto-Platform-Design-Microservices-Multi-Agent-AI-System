import io
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# Constants
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# Supported languages and their codes
SUPPORTED_LANGUAGES = {
    "English": "en"
}

# Language dictionaries
LANGUAGES = {
    "en": {
        "page_title": "🖌️ HTP Online Drawing Board",
        "drawing_settings": "🎨 Drawing Settings",
        "drawing_mode_label": "Drawing Mode:",
        "stroke_width_label": "Stroke Width:",
        "stroke_color_label": "Stroke Color:",
        "bg_color_label": "Background Color:",
        "instructions_title": "📋 Instructions",
        "instructions": """
            - Use this drawing board if you don't have paper and pencil available.
            - **Important Note**: It's recommended to use paper and pencil if possible for the best results.
            ### How to Use:
            1. Use the tools on the sidebar to draw your picture.
            2. When finished, click the **Download Drawing** button on the sidebar to save your drawing.
            3. Upload the saved image for analysis in the main test.
            """,
        "download_button": "💾 Download Drawing",
        "download_filename": "htp_drawing.png",
        "download_help": "Save your drawing as a PNG image.",
        "reminder_title": "⭕ Reminder",
        "reminder": """
            - After drawing, don't forget to download your image.
            - Return to the main test page to upload and analyze your drawing.
            """,
        "language_label": "Language:"
    }
}

# Helper function to get text based on current language
def get_text(key):
    return LANGUAGES[st.session_state['language_code']][key]

# Helper function to convert numpy array to bytes
def numpy_to_bytes(array, format="PNG"):
    if array.dtype != np.uint8:
        array = (array * 255).astype(np.uint8)
    image = Image.fromarray(array)
    byte_io = io.BytesIO()
    image.save(byte_io, format=format)
    return byte_io.getvalue()

def main():
    # Page Configuration
    st.set_page_config(
        page_title="PsyDraw: HTP Online Drawing Board",
        page_icon="🖌️",
        layout="wide"
    )

    # Initialize session state variables
    if 'language' not in st.session_state:
        st.session_state['language'] = 'English'
    if 'language_code' not in st.session_state:
        st.session_state['language_code'] = SUPPORTED_LANGUAGES[st.session_state['language']]

    # Sidebar
    st.sidebar.image("assets/logo2.png", use_column_width=True)
    st.sidebar.markdown("## " + get_text("drawing_settings"))

    # Language Selection
    language = st.sidebar.selectbox(
        get_text("language_label"),
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state['language'])
    )
    if language != st.session_state['language']:
        st.session_state['language'] = language
        st.session_state['language_code'] = SUPPORTED_LANGUAGES[language]
        st.rerun()
        
    # Drawing Settings
    drawing_mode = st.sidebar.selectbox(
        get_text("drawing_mode_label"),
        ("freedraw", "line", "rect", "circle"),
        help=get_text("drawing_mode_label")
    )
    stroke_width = st.sidebar.slider(get_text("stroke_width_label"), 1, 25, 3)
    stroke_color = st.sidebar.color_picker(get_text("stroke_color_label"), "#000000")
    bg_color = st.sidebar.color_picker(get_text("bg_color_label"), "#FFFFFF")

    # Main Content
    st.title(get_text("page_title"))

    # Instructions
    with st.expander(get_text("instructions_title"), expanded=True):
        st.markdown(get_text("instructions"))

    # Chinese removed — English only
}
    # Reminder
    with st.expander(get_text("reminder_title"), expanded=True):
        st.markdown(get_text("reminder"))

if __name__ == "__main__":
    main()