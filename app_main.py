import streamlit as st
import env_vars

import core_logic as cl
import ui_components as ui
from security_logic import mask_df


st.set_page_config(layout='wide', page_title="LakeBot")

dark_mode = False
ui.inject_styles(dark_mode)
ui.render_sidebar()


@st.cache_data
def load_data_cached():
    return cl.load_data(env_vars.lakehouse_config)

@st.cache_data
def get_masked_data_cached(ingest_data, user_prompt):
    return mask_df(ingest_data, user_prompt)


with st.spinner('Estableciendo conexión...'):
    ingest_data = load_data_cached()

ui.ensure_session_state()
ui.render_title()

col1, col2 = st.columns([3, 4], gap="large")

with col1:
    prompt = ui.render_prompt_input()
    thinking_placeholder = ui.render_thinking_placeholder()

    if st.button("Generar Respuesta"):
        if prompt:
            with st.spinner(""):
                ui.show_thinking(thinking_placeholder)
                
                # Get masked data based on user prompt
                masked_data = get_masked_data_cached(ingest_data, prompt)
                
                # Create agent with masked data
                masked_agent = cl.init_agent(env_vars.openaikey, masked_data)
                
                prompt_final = cl.build_prompt(prompt)
                try:
                    response, elapsed_time = cl.run_agent(masked_agent, prompt_final)
                    ui.add_history_entry(prompt, response, elapsed_time)
                except Exception as e:
                    st.error(f"Error al generar la respuesta: {e}")
            ui.clear_thinking(thinking_placeholder)
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
                    code = cl.extract_code_from_response(response)
                    if code is not None:
                        cleaned_code = cl.clean_matplotlib_code(code)
                        try:
                            # Use masked data for chart generation
                            masked_data = get_masked_data_cached(ingest_data, item["prompt"])
                            fig = cl.generate_plot(cleaned_code, masked_data)
                            if fig:
                                st.pyplot(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al generar la gráfica: {e}")
                    else:
                        formatted = cl.format_as_bullet_list_text(response)
                        formatted_html = formatted.replace('\n', '<br>')
                        ui.render_response_list(formatted_html)
    else:
        for item in st.session_state["history"]:
            response = item["response"]
            code = cl.extract_code_from_response(response)
            if code is not None:
                cleaned_code = cl.clean_matplotlib_code(code)
                try:
                    # Use masked data for chart generation
                    masked_data = get_masked_data_cached(ingest_data, item["prompt"])
                    fig = cl.generate_plot(cleaned_code, masked_data)
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error al generar la gráfica: {e}")
            else:
                formatted = cl.format_as_bullet_list_text(response)
                formatted_html = formatted.replace('\n', '<br>')
                ui.render_response_list(formatted_html)


