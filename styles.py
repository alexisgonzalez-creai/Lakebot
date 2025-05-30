# styles.py

import streamlit as st

def inject_custom_css(dark_mode=False):
    if dark_mode:
        background_style = "linear-gradient(135deg, #0a0f29, #0e1d4e, #143c91)"
        text_color = "#f5f5f5"
        box_color = "#121a3bdd"
        title_color = "#ffffff"
    else:
        background_style = "linear-gradient(135deg, #e0f0ff, #f5f9ff)"
        text_color = "#1a1a1a"
        box_color = "#ffffffdd"
        title_color = "#1f3bb3"

    st.markdown(f"""
        <style>
            body::before {{
                content: "";
                position: fixed;
                top: 0;
                left: 0;
                height: 100%;
                width: 100%;
                background: {background_style};
                z-index: -1;
            }}
            html, body {{
                height: 100%;
                background-color: transparent !important;
                font-family: Arial, sans-serif !important;
            }}
            [class^="stApp"] {{
                background-color: transparent !important;
            }}
            section[data-testid="stSidebar"] {{
                background-color: #ffffff !important;
            }}
            section[data-testid="stSidebar"] > div:first-child {{
                padding: 10px 15px;
            }}
            .title {{
                font-size: 48px;
                color: {title_color};
                margin: 30px 0 10px 30px;
                font-weight: 600;
            }}
            .stTextArea textarea {{
                font-size: 16px !important;
                height: 180px !important;
                border-radius: 16px !important;
                border: 1px solid #a3c1ff !important;
                background-color: #ffffff !important;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            }}
            .stButton>button {{
                background-color: #1f3bb3 !important;
                color: white !important;
                font-size: 16px !important;
                border-radius: 12px !important;
                padding: 10px 24px !important;
                box-shadow: 0 4px 12px rgba(31, 59, 179, 0.3) !important;
                transition: background-color 0.3s ease;
            }}
            .stButton>button:hover {{
                background-color: #2644d4 !important;
            }}
            .response-container {{
                background-color: {box_color};
                padding: 24px;
                border-radius: 18px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                margin-top: 20px;
                margin-bottom: 30px; /* <-- Espacio entre respuestas */
                border: 1px solid #ddd; /* <-- Borde gris suave */
            }}
            .response-text {{
                font-size: 17px;
                color: {text_color};
            }}
            .response-time {{
                color: #4e6ef2;
                font-size: 14px;
                margin-top: 10px;
            }}
            .chart-description {{
                margin-top: 14px;
                font-style: italic;
                color: {text_color};
            }}
        </style>
    """, unsafe_allow_html=True)
