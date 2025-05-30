# main.py

from langchain.chat_models import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
import pandas as pd
import streamlit as st
import env_vars
import styles
import time
import matplotlib.pyplot as plt
import re
import ast
from sqlalchemy import create_engine
import urllib

plt.switch_backend('Agg')

# Config inicial
st.set_page_config(layout='wide', page_title="LakeBot")

# --- SIDEBAR ---
st.sidebar.title("🤖 LakeBot")
st.sidebar.markdown("**LakeBot**")
st.sidebar.markdown("")

# --- BOTÓN PARA LIMPIAR DASHBOARD ---
if st.sidebar.button("🧹 Limpiar Dashboard"):
    st.session_state["history"] = []
    st.session_state["dashboard_mode"] = False

# --- MODO CLARO ---
dark_mode = False

# --- CARGA CSS ---
styles.inject_custom_css(dark_mode)

# --- CONEXIÓN A LAKEHOUSE ---
@st.cache_data
def load_data():
    config = env_vars.lakehouse_config
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['username']};"
        f"PWD={config['password']};"
        f"Authentication=ActiveDirectoryPassword;"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    connection_uri = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
    engine = create_engine(connection_uri)
    ingest = pd.read_sql_query("SELECT * FROM fact_headcountattrition", engine)
    return ingest

with st.spinner('Estableciendo conexión...'):
    ingest_data = load_data()

# --- LANGCHAIN AGENT ---
openaikey = env_vars.openaikey
chat = ChatOpenAI(openai_api_key=openaikey, model_name='gpt-4', temperature=0.0)
agent = create_pandas_dataframe_agent(
    chat, ingest_data, verbose=True,
    allow_dangerous_code=True,
    handle_parsing_errors=True
)

# --- FUNCIONES AUXILIARES ---
def generate_plot(code):
    local_vars = {'df': ingest_data}
    try:
        exec("""
import matplotlib.pyplot as plt
plt.figure(figsize=(7,5))
plt.rcParams.update({
    'axes.titlesize': 7,
    'axes.labelsize': 7,
    'xtick.labelsize': 6,
    'ytick.labelsize': 6
})
""" + code + """
# Ajuste automático después del código de gráfica
ax = plt.gca()  # Obtener ejes actuales
if len(ax.get_xticklabels()) > 6:
    plt.xticks(rotation=45)
if len(ax.get_yticklabels()) > 6:
    plt.yticks(rotation=45)
plt.tight_layout()
""", globals(), local_vars)
        fig = plt.gcf()
        return fig
    except Exception as e:
        st.error(f"Error al generar la gráfica: {e}")
        return None




def format_as_bullet_list(response):
    """Convierte la respuesta a una lista de bullets si aplica"""
    try:
        # Si es lista de Python en texto, evalúa
        parsed = ast.literal_eval(response)
        if isinstance(parsed, list):
            items = parsed
        else:
            items = response.strip().splitlines()
    except Exception:
        # Si no se puede evaluar, tratamos como texto normal separado por líneas
        items = response.strip().splitlines()
    
    # Armar la lista bonita
    formatted = "\n".join([f"- {item.strip()}" for item in items if item.strip()])
    return formatted.replace('\n', '<br>')

def is_markdown_table(text):
    """Detecta si el texto es una tabla markdown real."""
    lines = text.strip().splitlines()
    return (
        len(lines) >= 2
        and lines[0].strip().startswith("|")
        and lines[1].strip().startswith("|")
    )

# --- ESTADO INICIAL ---
if "dashboard_mode" not in st.session_state:
    st.session_state["dashboard_mode"] = False
if "history" not in st.session_state:
    st.session_state["history"] = []

# --- TÍTULO PRINCIPAL ---
st.markdown("<div class='title'>LakeBot</div>", unsafe_allow_html=True)

# --- INTERFAZ PRINCIPAL ---
col1, col2 = st.columns([3, 4], gap="large")

with col1:
    prompt = st.text_area("Escribe tu consulta:", key="prompt", help="Ingresa tu pregunta aquí")

    thinking_placeholder = st.empty()

    if st.button("Generar Respuesta"):
        if prompt:
            with st.spinner(""):
                thinking_placeholder.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <img src="https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif" alt="Pensando..." width="120">
                        <p style="font-size: 18px; color: #666;">Preparando respuesta...</p>
                    </div>
                """, unsafe_allow_html=True)

                requires_chart = any(word in prompt.lower() for word in [
                    "grafica", "graficar", "grafico", "histograma", "distribución",
                    "diagrama", "curva", "scatter", "barras", "línea", "boxplot"
                ])
                prompt_final = prompt

                if requires_chart:
                    prompt_final += """
                    Devuelve exclusivamente código en Python con Matplotlib para generar la gráfica solicitada en varios colores
                    No uses plt.show() ni st.pyplot().
                    """
                else:
                    if any(word in prompt.lower() for word in ["lista", "agrupación", "grupo", "total por", "cantidad por", "por bpo"]):
                        prompt_final += """
                        Por favor, entrega la respuesta en formato de lista simple:
                        - México: 17562 empleados
                        - Argentina: 1726 empleados
                        (No usar tablas markdown, no usar arrays Python)
                        """
                    else:
                        prompt_final += """
                        Responde en lenguaje claro, sin cursivas ni negritas.
                        """

                try:
                    response = agent.run(prompt_final)
                    end_time = time.time()
                    elapsed_time = time.time() - end_time
                    st.session_state["history"].append({
                        "prompt": prompt,
                        "response": response,
                        "elapsed_time": elapsed_time
                    })
                except Exception as e:
                    st.error(f"Error al generar la respuesta: {e}")

            thinking_placeholder.empty()
        else:
            st.warning("Por favor, ingresa una pregunta.")

with col2:
    if st.session_state["dashboard_mode"]:
        for i in range(0, len(st.session_state["history"]), 2):
            colA, colB = st.columns(2, gap="small")
            batch = st.session_state["history"][i:i+2]
            for idx, item in enumerate(batch):
                response = item["response"]
                current_col = colA if idx == 0 else colB
                with current_col:
                    if (
                        "```python" in response
                        or response.strip().startswith("df.")
                        or response.strip().startswith("plt.")
                        or response.strip().startswith("import matplotlib")
                    ):
                        if "```python" in response:
                            code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
                            extracted_code = code_match.group(1).strip() if code_match else response.strip()
                        else:
                            extracted_code = response.strip()

                        cleaned_code = re.sub(r"plt\\.show\\(\\)|st\\.pyplot\\(.*?\\)", "", extracted_code)
                        fig = generate_plot(cleaned_code)
                        if fig:
                            st.pyplot(fig, use_container_width=True)
                    else:
                        formatted_html = format_as_bullet_list(response)
                        st.markdown(f"""
                            <div class='response-container'>
                                <div class='response-text'>
                                    {formatted_html}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
    else:
        for item in st.session_state["history"]:
            response = item["response"]
            if (
                "```python" in response
                or response.strip().startswith("df.")
                or response.strip().startswith("plt.")
                or response.strip().startswith("import matplotlib")
            ):
                if "```python" in response:
                    code_match = re.search(r"```python(.*?)```", response, re.DOTALL)
                    extracted_code = code_match.group(1).strip() if code_match else response.strip()
                else:
                    extracted_code = response.strip()

                cleaned_code = re.sub(r"plt\\.show\\(\\)|st\\.pyplot\\(.*?\\)", "", extracted_code)
                fig = generate_plot(cleaned_code)
                if fig:
                    st.pyplot(fig, use_container_width=True)
            else:
                formatted_html = format_as_bullet_list(response)
                st.markdown(f"""
                    <div class='response-container'>
                        <div class='response-text'>
                            {formatted_html}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
