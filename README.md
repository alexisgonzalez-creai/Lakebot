# Lakebot
Es una aplicación de chatbot conversacional desarrollada en Streamlit que:

  -Se conecta a una base de datos tipo Lakehouse (SQL Server con ODBC y autenticación Azure AD) para cargar información.

  -Utiliza LangChain + OpenAI GPT-4 para interpretar consultas del usuario y generar respuestas.

  -Permite hacer preguntas sobre los datos cargados (tipo analítica descriptiva).

  -Puede generar automáticamente tablas y gráficas (con Matplotlib) en respuesta a lo que pide el usuario.

  -Tiene un modo "Dashboard" para acumular respuestas y gráficos si el usuario quiere construir algo más complejo.

En resumen: Es un chatbot de analítica de datos que convierte preguntas naturales en consultas, respuestas y visualizaciones sobre un dataset corporativo.
