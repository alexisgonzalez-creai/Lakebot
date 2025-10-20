import time
import re
import ast
import urllib
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from langchain.chat_models import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent


plt.switch_backend('Agg')


def create_engine_from_config(config: dict):
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
    return create_engine(connection_uri)


def load_data(config: dict) -> pd.DataFrame:
    engine = create_engine_from_config(config)
    ingest = pd.read_sql_query("SELECT * FROM fact_headcountattrition", engine)
    return ingest


def init_agent(openaikey: str, ingest_data: pd.DataFrame):
    chat = ChatOpenAI(openai_api_key=openaikey, model_name='gpt-4', temperature=0.0)
    agent = create_pandas_dataframe_agent(
        chat, ingest_data, verbose=True,
        allow_dangerous_code=True,
        handle_parsing_errors=True
    )
    return agent


def detect_requires_chart(prompt: str) -> bool:
    keywords = [
        "grafica", "graficar", "grafico", "histograma", "distribución",
        "diagrama", "curva", "scatter", "barras", "línea", "boxplot"
    ]
    return any(word in prompt.lower() for word in keywords)


def detect_list_format(prompt: str) -> bool:
    keywords = ["lista", "agrupación", "grupo", "total por", "cantidad por", "por bpo"]
    return any(word in prompt.lower() for word in keywords)


def build_prompt(prompt: str) -> str:
    prompt_final = prompt
    if detect_requires_chart(prompt):
        prompt_final += (
            "\nDevuelve exclusivamente código en Python con Matplotlib para generar la gráfica solicitada en varios colores"
            "\nNo uses plt.show() ni st.pyplot().\n"
        )
    else:
        if detect_list_format(prompt):
            prompt_final += (
                "\nPor favor, entrega la respuesta en formato de lista simple:"
                "\n- México: 17562 empleados"
                "\n- Argentina: 1726 empleados"
                "\n(No usar tablas markdown, no usar arrays Python)\n"
            )
        else:
            prompt_final += ("\nResponde en lenguaje claro, sin cursivas ni negritas.\n")
    return prompt_final


def run_agent(agent, prompt_final: str) -> Tuple[str, float]:
    start_time = time.time()
    response = agent.run(prompt_final)
    elapsed_time = time.time() - start_time
    return response, elapsed_time


def extract_code_from_response(response: str) -> Optional[str]:
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
        return extracted_code
    return None


def clean_matplotlib_code(code: str) -> str:
    return re.sub(r"plt\\.show\\\(\\\)|st\\.pyplot\\\(.*?\\\)", "", code)


def generate_plot(code: str, ingest_data: pd.DataFrame):
    local_vars = {'df': ingest_data}
    exec(
        """
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
ax = plt.gca()
if len(ax.get_xticklabels()) > 6:
    plt.xticks(rotation=45)
if len(ax.get_yticklabels()) > 6:
    plt.yticks(rotation=45)
plt.tight_layout()
""",
        globals(), local_vars
    )
    fig = plt.gcf()
    return fig


def format_as_bullet_list_text(response: str) -> str:
    try:
        parsed = ast.literal_eval(response)
        if isinstance(parsed, list):
            items = parsed
        else:
            items = response.strip().splitlines()
    except Exception:
        items = response.strip().splitlines()
    formatted = "\n".join([f"- {str(item).strip()}" for item in items if str(item).strip()])
    return formatted


