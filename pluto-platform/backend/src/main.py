import streamlit as st
from PIL import Image
import pandas as pd

def get_text(key):
    return translations[st.session_state.language][key]

translations = {
    "English": {
        "title": "PsyDraw: A Multi-Agent Multimodal System for Mental Health Detection in Left-Behind Children",
        "introduction": "Introduction of HTP Test",
        "introduction_content": "The House-Tree-Person (HTP) test is a projective psychological assessment tool applicable to both children and adults aged 3 and above. This test aims to provide insights into an individual's personality, emotions, and attitudes through the analysis of drawings. In the HTP test procedure, participants are instructed to draw a house, a tree, and a person. Researchers analyze HTP drawings to evaluate cognitive, emotional, and social functioning, interpreting depicted elements as reflections of hidden emotions, desires, and internal conflicts not easily discerned through direct methods.",
        "available_features": """
        We provide the necessary **API key** and **base URL** for **PsyDraw** in the ***supplementary materials***.
        
        **Available Features:**
        - **Batch Analysis**: Analyze multiple HTP drawings in bulk
        - **HTP Test**: Take the House-Tree-Person test online
        - **Online Board**: Use our digital drawing tool to create HTP drawings
        """,
        "batch_analysis": "Batch Analysis: Analyze multiple HTP drawings in bulk",
        "htp_test": "HTP Test: Take the House-Tree-Person test online",
        "online_board": "Online Board: Use our digital drawing tool to create HTP drawings",
        "contact_admin": "Please contact the administrator for access to these features.",
        "github_link": "Visit our GitHub repository for more information and updates.",
        "abstract": "Abstract",
        "abstract_content": """
    Left-behind children face severe mental health challenges due to parental migration for work. \
    The House-Tree-Person (HTP) test, a psychological assessment method with higher child participation and cooperation, requires expert interpretation, limiting its application in resource-scarce areas. \
    To address this, we propose **PsyDraw**, a multi-agent system based on Multimodal Large Language Models for automated analysis of HTP drawings and assessment of children's mental health status.  \
    The system's workflow comprises two main stages: feature extraction and analysis, and report generation, accomplished by multiple collaborative agents.  \
    We evaluate the system on HTP drawings from 290 primary school students, with the generated mental health reports evaluated by class teachers.  \
    Results show that 71.03% of the analyses are rated as **Match**, 26.21% as **Generally Match**, and only 2.41% as **Not Match**. \
    These findings demonstrate the potential of PsyDraw in automating HTP test analysis, offering an innovative solution to the shortage of professional personnel in mental health assessment for left-behind children.         
    """,
        "system_workflow": "The Workflow of PsyDraw",
        "key_features": "Key Features",
        "automated_analysis": "Automated Analysis",
        "multi_agent_system": "Multi-Agent System",
        "scalable_solution": "Scalable Solution",
        "evaluation_results": "Evaluation Results",
        "matching_rates": "Matching rates of results with teacher feedback.",
        "participants_note": "Note: All test participants were primary school students. This study was conducted with proper authorization from relevant personnel.",
        "limitations": "Limitations",
        "limitation_content": """
    PsyDraw is designed for early detection of mental health issues among left-behind children in resource-limited areas. However, it is not a substitute for professional medical advice. Key limitations include:

    1. Cultural context: Currently validated only with Chinese children.
    2. Data protection: Requires stringent mechanisms to ensure privacy and ethical compliance.
    3. Potential biases: As an MLLM-based tool, it may harbor inherent biases.
    4. Long-term effectiveness: Not yet confirmed through longitudinal studies.
    5. Subtle cues: May miss nuances that human professionals can identify in face-to-face interactions.
    6. Technological constraints: Efficacy may be limited by infrastructure and user capabilities.
    """,
        "case_study": "Case Study",
        "footer": "© 2024 PsyDraw. All rights reserved.",
    }
}


def sidebar():  
    with st.sidebar:
        st.image("assets/logo2.png", use_column_width=True)
        st.title("House-Tree-Person Test")

        st.write("## Language")
        st.session_state.language = "English"
            
        st.subheader(get_text("introduction"))
        st.write(get_text("introduction_content"))

def main_page():
    st.title(get_text('title'))

    st.info(get_text('available_features'))

    st.write(f"## {get_text('abstract')}")
    st.write(get_text('abstract_content'))

    st.write(f"## {get_text('system_workflow')}")
    st.image("assets/workflow.png", use_column_width=True)

    st.write(f"## {get_text('evaluation_results')}")
    results_data = {
        "Category": ["Matching", "Generally Matching", "Not Matching"],
        "Total (%)": [71.03, 26.21, 2.41],
        "Warn. (%)": [58.89, 35.56, 4.44],
        "Obs. (%)": [76.50, 22.00, 1.50]
    }
    df = pd.DataFrame(results_data)
    st.table(df)
    st.caption("Table: Matching rates of results with teacher feedback.")
    st.write(get_text('participants_note'))
    
    st.write(f"## {get_text('limitations')}")
    st.write(get_text('limitation_content'))

    st.write(f"## {get_text('case_study')}")
    col1, col2 = st.columns(2)
    with col1:
        case1 = Image.open("assets/case_study1.png")
        st.image(case1, use_column_width=True)
    with col2:
        case2 = Image.open("assets/case_study2.png")
        st.image(case2, use_column_width=True)

    # 页脚
    st.markdown("---")
    st.write(get_text('footer'))

def main() -> None:
    # 页面配置
    st.set_page_config(page_title="PsyDraw", page_icon=":house::evergreen_tree:", layout="wide")

    if 'language' not in st.session_state:
        st.session_state.language = "English"
        
    sidebar()
    main_page()

if __name__ == "__main__":
    main()
    