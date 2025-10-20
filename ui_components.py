import streamlit as st
import styles


def inject_styles(dark_mode: bool):
    styles.inject_custom_css(dark_mode)


def render_sidebar():
    st.sidebar.title("🤖 LakeBot")
    st.sidebar.markdown("**LakeBot**")
    st.sidebar.markdown("")
    if st.sidebar.button("🧹 Limpiar Dashboard"):
        st.session_state["history"] = []
        st.session_state["dashboard_mode"] = False


def render_title():
    st.markdown("<div class='title'>LakeBot</div>", unsafe_allow_html=True)


def render_prompt_input() -> str:
    return st.text_area("Escribe tu consulta:", key="prompt", help="Ingresa tu pregunta aquí")


def render_thinking_placeholder() -> "streamlit.DeltaGenerator":
    return st.empty()


def show_thinking(thinking_placeholder):
    thinking_placeholder.markdown(
        """
        <div style="text-align: center; padding: 20px;">
            <img src="https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif" alt="Pensando..." width="120">
            <p style="font-size: 18px; color: #666;">Preparando respuesta...</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clear_thinking(thinking_placeholder):
    thinking_placeholder.empty()


def ensure_session_state():
    if "dashboard_mode" not in st.session_state:
        st.session_state["dashboard_mode"] = False
    if "history" not in st.session_state:
        st.session_state["history"] = []


def add_history_entry(prompt: str, response: str, elapsed_time: float):
    st.session_state["history"].append({
        "prompt": prompt,
        "response": response,
        "elapsed_time": elapsed_time
    })


def render_response_list(response: str):
    st.markdown(f"""
        <div class='response-container'>
            <div class='response-text'>
                {response}
            </div>
        </div>
    """, unsafe_allow_html=True)


