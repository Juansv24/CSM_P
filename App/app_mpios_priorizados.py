
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure the page
st.set_page_config(
    page_title="Ficha Municipal",
    page_icon="📋",
    layout="wide"
)

def mostrar_paginacion_coincidencias(rec_code):
    """Mostrar controles de paginación para coincidencias de una recomendación específica"""
    pagina_actual = st.session_state.get(f'pagina_actual_coincidencias_{rec_code}', 1)
    total_paginas = st.session_state.get(f'total_paginas_coincidencias_{rec_code}', 1)

    if total_paginas <= 1:
        return

    st.markdown("---")

    # Crear columnas para centrar la paginación
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Crear botones de paginación
        cols = st.columns([1, 1, 3, 1, 1])

        # Botón anterior
        with cols[0]:
            if st.button("◀", disabled=(pagina_actual <= 1), key=f"prev_page_coincidencias_{rec_code}"):
                st.session_state[f'pagina_actual_coincidencias_{rec_code}'] = max(1, pagina_actual - 1)
                st.rerun()

        # Números de página como botones
        with cols[2]:
            # Mostrar páginas como botones (máximo 5 páginas visibles)
            paginas_a_mostrar = []

            if total_paginas <= 5:
                paginas_a_mostrar = list(range(1, total_paginas + 1))
            else:
                if pagina_actual <= 3:
                    paginas_a_mostrar = [1, 2, 3, 4, 5]
                elif pagina_actual >= total_paginas - 2:
                    paginas_a_mostrar = list(range(total_paginas - 4, total_paginas + 1))
                else:
                    paginas_a_mostrar = list(range(pagina_actual - 2, pagina_actual + 3))

            # Crear mini-columnas para cada número de página
            mini_cols = st.columns(len(paginas_a_mostrar))

            for i, pagina in enumerate(paginas_a_mostrar):
                with mini_cols[i]:
                    if pagina == pagina_actual:
                        st.markdown(
                            f"<div style='background: #007bff; color: white; text-align: center; padding: 4px; border-radius: 4px; margin: 2px;'>{pagina}</div>",
                            unsafe_allow_html=True)
                    else:
                        if st.button(str(pagina), key=f"page_coincidencias_{rec_code}_{pagina}"):
                            st.session_state[f'pagina_actual_coincidencias_{rec_code}'] = pagina
                            st.rerun()

        # Botón siguiente
        with cols[4]:
            if st.button("▶", disabled=(pagina_actual >= total_paginas), key=f"next_page_coincidencias_{rec_code}"):
                st.session_state[f'pagina_actual_coincidencias_{rec_code}'] = min(total_paginas, pagina_actual + 1)
                st.rerun()

# Load and cache data
@st.cache_data
def load_data():
    """Load the pickle file and return the DataFrame"""
    try:
        df = pd.read_pickle('Data/Similitudes Jerárquicas Final Econ 2.pkl')
        return df
    except FileNotFoundError:
        st.error("Archivo no encontrado. Verifique que existe 'Data/Similitudes Jerárquicas Final Econ 2.pkl'")
        return None
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return None


def main():
    """Main function to run the Streamlit app"""

    # Load data
    df = load_data()
    if df is None:
        st.stop()

    # Sidebar for filters
    st.sidebar.markdown("### 🔧 Configuración de Filtros")

    # Department filter
    departments = sorted(df['dpto'].unique())
    selected_department = st.sidebar.selectbox(
        "Departamento:",
        options=['Todos'] + departments,
        index=0
    )

    # Municipality filter
    if selected_department == 'Todos':
        municipalities = sorted(df['mpio'].unique())
    else:
        municipalities = sorted(df[df['dpto'] == selected_department]['mpio'].unique())

    selected_municipality = st.sidebar.selectbox(
        "Municipio:",
        options=['Todos'] + municipalities,
        index=0
    )

    # Sentence similarity threshold
    sentence_threshold = st.sidebar.slider(
        "Umbral de Similitud de Oraciones:",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        help="Filtro para mostrar solo oraciones con similitud igual o superior al valor seleccionado"
    )

    # Policy filter
    include_policy_only = st.sidebar.checkbox(
        "Solo secciones de política pública",
        value=True,
        help="Filtrar para incluir solo contenido clasificado como política pública"
    )

    # Filter data
    filtered_df = df.copy()

    # Apply policy filter FIRST
    if include_policy_only:
        filtered_df = filtered_df[
            (filtered_df['predicted_class'] == 'Incluida') |
            ((filtered_df['predicted_class'] == 'Excluida') & (filtered_df['prediction_confidence'] < 0.8))
            ]

    # Apply department filter
    if selected_department != 'Todos':
        filtered_df = filtered_df[filtered_df['dpto'] == selected_department]

    # Apply municipality filter
    if selected_municipality != 'Todos':
        filtered_df = filtered_df[filtered_df['mpio'] == selected_municipality]

    # Apply sentence similarity filter (LAST)
    high_quality_sentences = filtered_df[filtered_df['sentence_similarity'] >= sentence_threshold]

    # ==================================================
    # HEADER SECTION - PDF Style
    # ==================================================

    if selected_municipality != 'Todos':
        muni_info = filtered_df.iloc[0]
        municipality_name = selected_municipality
        department_name = muni_info['dpto']

        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1f77b4 0%, #17a2b8 100%); 
                    color: white; 
                    padding: 2rem; 
                    border-radius: 15px; 
                    margin-bottom: 2rem;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="margin: 0.5rem 0 0 0; font-size: 3rem; font-weight: 700;">{municipality_name} </h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.5rem; opacity: 0.9;">{department_name}, Colombia</p>
        </div>
        """, unsafe_allow_html=True)

        # Descripción de funcionalidad
        with st.expander("ℹ️ Acerca de este Dashboard", expanded=False):
            st.markdown("""
                ### 📋 Ficha Municipal - Análisis de Implementación de Recomendaciones

                Este dashboard permite analizar el nivel de mención de las recomendaciones de política pública 
                en los planes de desarrollo (PDD) de los municipios y departamentos de Colombia mediante técnicas de similitud semántica.

                **Funcionalidades principales:**
                - **Filtrado:** Seleccione departamento y municipio para análisis específico
                - **Umbral de similitud:** Ajuste el nivel mínimo de coincidencia entre recomendaciones y texto municipal (entre más alto más calidad tendrán las coincidencias)
                - **Ranking:** Compare el desempeño relativo entre municipios
                - **Análisis detallado:** Explore recomendaciones específicas y oraciones relacionadas

                **Cómo interpretar los resultados:**
                - Mayor similitud (0 - 1) indica una coincidencia de mejor calidad entre el texto del PDD y las recomendaciones
                - El ranking se basa en el número total de recomendaciones implementadas

                """)

        # ==================================================
        # SECTION 1: BASIC INFORMATION
        # ==================================================

        st.markdown("### 📊 Información Básica")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            mpi_score = muni_info.get('IPM_2018', 'N/A')
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; border-left: 4px solid #6c757d;">
                    <h4 style="margin: 0; color: #6c757d;">IPM 2018 
                        <span title="Índice de Pobreza Multidimensional 2018: Mide la pobreza considerando múltiples dimensiones como educación, salud, trabajo, etc. Valores más altos indican mayor pobreza." 
                              style="cursor: help; color: #007bff;">ⓘ</span>
                    </h4>
                    <h3 style="margin: 0.5rem 0 0 0; color: #333;">{mpi_score if pd.notna(mpi_score) else 'N/A'}</h3>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            pdet_status = muni_info.get('PDET', 'N/A')
            pdet_color = "#28a745" if pdet_status == 1 else "#dc3545" if pdet_status == 0 else "#6c757d"
            pdet_text = "SÍ" if pdet_status == 1 else "NO" if pdet_status == 0 else "N/A"
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; border-left: 4px solid {pdet_color};">
                    <h4 style="margin: 0; color: #6c757d;">PDET 
                        <span title="Programa de Desarrollo con Enfoque Territorial: Indica si el municipio está incluido en este programa para territorios afectados por el conflicto." 
                              style="cursor: help; color: #007bff;">ⓘ</span>
                    </h4>
                    <h3 style="margin: 0.5rem 0 0 0; color: {pdet_color};">{pdet_text}</h3>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            iica_cat = muni_info.get('Cat_IICA', 'N/A')
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; border-left: 4px solid #17a2b8;">
                    <h4 style="margin: 0; color: #6c757d;">Categoría IICA 
                        <span title="Índice de Incidencia del Conflicto Armado: Clasifica municipios según la incidencia del conflicto, tiene en cuenta dimensiones como acciones armadas, desplazamiento, cultivos de coca, entre otros." 
                              style="cursor: help; color: #007bff;">ⓘ</span>
                    </h4>
                    <h3 style="margin: 0.5rem 0 0 0; color: #333;">{iica_cat if pd.notna(iica_cat) else 'N/A'}</h3>
                </div>
                """, unsafe_allow_html=True)

        with col4:
            mdm_group = muni_info.get('Grupo_MDM', 'N/A')
            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; border-left: 4px solid #ffc107;">
                    <h4 style="margin: 0; color: #6c757d;">Grupo MDM 
                        <span title="Grupo de Capacidades Iniciales de la Medición de Desempeño Municipal: Las capacidades iniciales se definen como el nivel de recursos y las condiciones del municipio que delimitan el alcance de la gestión y la provisión de bienes y servicios." 
                              style="cursor: help; color: #007bff;">ⓘ</span>
                    </h4>
                    <h3 style="margin: 0.5rem 0 0 0; color: #333;">{mdm_group if pd.notna(mdm_group) else 'N/A'}</h3>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ==================================================
        # SECTION 2: IMPLEMENTATION ANALYSIS
        # ==================================================

        st.markdown("### 📈 Análisis de Implementación")

        # Calculate key metrics
        # Recommendations implemented (at least one sentence above threshold)
        implemented_recs = high_quality_sentences['recommendation_code'].nunique()

        # Priority recommendations implemented
        priority_implemented = high_quality_sentences[
            high_quality_sentences['recommendation_priority_label'].isin(['Alta', 'High'])
        ]['recommendation_code'].nunique()

        # Calculate ranking
        ranking_data = df.copy()
        if include_policy_only:
            ranking_data = ranking_data[
                (ranking_data['predicted_class'] == 'Incluida') |
                ((ranking_data['predicted_class'] == 'Excluida') & (ranking_data['prediction_confidence'] < 0.8))
                ]

        ranking_data = ranking_data.groupby(['mpio', 'dpto']).agg({
            'recommendation_code': lambda x: len(set(x[df.loc[x.index, 'sentence_similarity'] >= sentence_threshold]))
        }).reset_index()
        ranking_data.columns = ['Municipio', 'Departamento', 'Recomendaciones_Implementadas']
        ranking_data = ranking_data.sort_values('Recomendaciones_Implementadas', ascending=False)
        ranking_data['Ranking'] = range(1, len(ranking_data) + 1)

        # Get totals
        total_municipalities = len(ranking_data)
        total_recommendations = df['recommendation_code'].nunique()

        current_ranking = ranking_data[ranking_data['Municipio'] == selected_municipality]
        ranking_position = current_ranking['Ranking'].iloc[0] if not current_ranking.empty else "N/A"

        col1, col2, col3 = st.columns(3)

        with col1:
            ranking_text = f"#{ranking_position}/{total_municipalities}" if ranking_position != "N/A" else "N/A"
            st.markdown(f"""
                <div style="background-color: #fff3e0; padding: 1.5rem; border-radius: 10px; text-align: center;">
                    <h2 style="margin: 0; color: #EF6C00; font-size: 2.5rem;">{ranking_text}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: #EF6C00; font-weight: 500;">Ranking</p>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            recs_text = f"{implemented_recs}/{total_recommendations}"
            st.markdown(f"""
                <div style="background-color: #e3f2fd; padding: 1.5rem; border-radius: 10px; text-align: center;">
                    <h2 style="margin: 0; color: #1976d2; font-size: 2.5rem;">{recs_text}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: #1976d2; font-weight: 500;">Recomendaciones Implementadas</p>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div style="background-color: #e8f5e8; padding: 1.5rem; border-radius: 10px; text-align: center;">
                    <h2 style="margin: 0; color: #388e3c; font-size: 2.5rem;">{priority_implemented}</h2>
                    <p style="margin: 0.5rem 0 0 0; color: #388e3c; font-weight: 500;">Prioritarias Implementadas</p>
                </div>
                """, unsafe_allow_html=True)

        # Top 5 Recommendations by Frequency Chart
        st.markdown(" ")
        st.markdown(" ")

        if not high_quality_sentences.empty:
            st.markdown("### Top 5 Recomendaciones más Frecuentes")
            freq_analysis = high_quality_sentences.groupby('recommendation_code').agg({
                'sentence_similarity': 'count',
                'recommendation_text': 'first'
            }).reset_index()
            freq_analysis.columns = ['Código', 'Frecuencia', 'Texto']
            freq_analysis = freq_analysis.sort_values('Frecuencia', ascending=False).head(5)

            if not freq_analysis.empty:
                fig_freq = px.bar(
                    freq_analysis,
                    x='Frecuencia',
                    y='Código',
                    orientation='h',
                    title='Número de Oraciones por Recomendación',
                    labels={'Frecuencia': 'Número de Oraciones', 'Código': 'Código de Recomendación'},
                    color='Frecuencia',
                    color_continuous_scale='blues',
                    hover_data={'Texto': True, 'Frecuencia': True}
                )
                fig_freq.update_layout(
                    height=400,
                    showlegend=False,
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_freq, use_container_width=True)

        # Implementation Heatmap by Topic
        if not high_quality_sentences.empty and 'recommendation_topic' in high_quality_sentences.columns:
            st.markdown("#### Implementación por Tema")

            topic_analysis = high_quality_sentences.groupby('recommendation_topic')[
                'recommendation_code'].nunique().reset_index()
            topic_analysis.columns = ['Tema', 'Recomendaciones_Implementadas']
            topic_analysis = topic_analysis.sort_values('Recomendaciones_Implementadas', ascending=False)

            if not topic_analysis.empty:
                fig_heatmap = px.bar(
                    topic_analysis,
                    x='Recomendaciones_Implementadas',
                    y='Tema',
                    orientation='h',
                    title='Recomendaciones Implementadas por Tema',
                    labels={'Recomendaciones_Implementadas': 'Número de Recomendaciones', 'Tema': ''},
                    color='Recomendaciones_Implementadas',
                    color_continuous_scale='viridis'
                )
                fig_heatmap.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=50, t=80, b=50),
                    coloraxis_showscale = False
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

        st.markdown("---")

        # ==================================================
        # SECTION 3: HIERARCHICAL ANALYSIS WITH TABS
        # ==================================================

        st.markdown("---")
        st.markdown("### 🔍  Análisis detallado de recomendaciones")

        if not high_quality_sentences.empty:
            # Recommendation selector (keep original dropdown functionality)
            available_recommendations = high_quality_sentences['recommendation_code'].unique().tolist()

            selected_rec_code = st.selectbox(
                "Seleccione una recomendación:",
                options=available_recommendations,
                format_func=lambda
                    x: f"{x} - {high_quality_sentences[high_quality_sentences['recommendation_code'] == x]['recommendation_text'].iloc[0][:60]}...",
                key="detailed_rec_select",
                label_visibility="collapsed"  # <- This hides the label but keeps it for accessibility
            )

            if selected_rec_code:
                rec_data = high_quality_sentences[
                    high_quality_sentences['recommendation_code'] == selected_rec_code].copy()

                # Show recommendation text
                rec_text = rec_data['recommendation_text'].iloc[0]
                st.markdown("**Texto de la Recomendación:**")
                st.info(rec_text)

                # Hierarchical navigation tabs
                tab = st.segmented_control(
                    "Nivel de análisis:",
                    ["📝 Párrafos", "💬 Oraciones"],
                    selection_mode="single",
                    default="💬 Oraciones",
                    key="hierarchy_tabs"
                )

                # TAB 1: PARAGRAPH LEVEL
                if tab == "📝 Párrafos":
                    st.markdown("**Análisis por Párrafos:**")

                    # Group by paragraph and calculate paragraph-level similarity
                    paragraph_analysis = rec_data.groupby(['paragraph_id', 'paragraph_text']).agg({
                        'paragraph_similarity': 'first',
                        'page_number': 'first',
                        'sentence_similarity': ['count', 'mean', 'max'],
                        'predicted_class': lambda x: x.mode()[0] if not x.empty else 'N/A'
                    }).reset_index()

                    paragraph_analysis.columns = ['ID_Párrafo', 'Texto_Párrafo', 'Similitud_Párrafo', 'Página',
                                                  'Num_Oraciones', 'Similitud_Prom', 'Similitud_Max',
                                                  'Clasificación_ML']
                    paragraph_analysis = paragraph_analysis.sort_values('Similitud_Prom', ascending=False)

                    # PAGINATION FOR PARAGRAPHS
                    coincidencias_por_pagina = 5
                    total_coincidencias = len(paragraph_analysis)
                    total_paginas = max(1, (total_coincidencias - 1) // coincidencias_por_pagina + 1)

                    # Initialize current page for this recommendation's paragraphs
                    pagina_key = f'pagina_actual_coincidencias_{selected_rec_code}_parrafos'
                    if pagina_key not in st.session_state:
                        st.session_state[pagina_key] = 1

                    # Validate current page doesn't exceed total
                    if st.session_state[pagina_key] > total_paginas:
                        st.session_state[pagina_key] = 1

                    pagina_actual = st.session_state[pagina_key]

                    # Apply pagination
                    inicio = (pagina_actual - 1) * coincidencias_por_pagina
                    fin = inicio + coincidencias_por_pagina
                    paragraph_analysis_paginado = paragraph_analysis.iloc[inicio:fin]

                    # Store in session state for pagination controls
                    st.session_state[f'total_paginas_coincidencias_{selected_rec_code}_parrafos'] = total_paginas

                    # Show pagination info
                    st.write(
                        f"📋 Mostrando {len(paragraph_analysis_paginado)} de {total_coincidencias} párrafos (Página {pagina_actual} de {total_paginas})")

                    # Show paginated paragraphs
                    for idx, row in paragraph_analysis_paginado.iterrows():
                        with st.expander(
                                f"Párrafo {row['ID_Párrafo']} - Similitud Promedio: {row['Similitud_Prom']:.3f}",
                                expanded=idx == paragraph_analysis_paginado.index[0]):  # Only first expanded
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write("**Contenido del Párrafo:**")
                                # Truncate very long text
                                para_text = row['Texto_Párrafo'][:800] + "..." if len(
                                    row['Texto_Párrafo']) > 800 else row['Texto_Párrafo']
                                st.write(para_text)

                            with col2:
                                st.write("**Métricas:**")
                                st.write(f"**ID Página:** {row['Página']}")
                                st.write(f"**ID Párrafo:** {row['ID_Párrafo']}")
                                st.write(f"**Similitud Párrafo:** {row['Similitud_Párrafo']:.3f}")

                    # Show pagination controls for paragraphs
                    if total_paginas > 1:
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            cols = st.columns([1, 1, 3, 1, 1])

                            with cols[0]:
                                if st.button("◀", disabled=(pagina_actual <= 1),
                                             key=f"prev_page_parrafos_{selected_rec_code}"):
                                    st.session_state[pagina_key] = max(1, pagina_actual - 1)
                                    st.rerun()

                            with cols[2]:
                                paginas_a_mostrar = []
                                if total_paginas <= 5:
                                    paginas_a_mostrar = list(range(1, total_paginas + 1))
                                else:
                                    if pagina_actual <= 3:
                                        paginas_a_mostrar = [1, 2, 3, 4, 5]
                                    elif pagina_actual >= total_paginas - 2:
                                        paginas_a_mostrar = list(range(total_paginas - 4, total_paginas + 1))
                                    else:
                                        paginas_a_mostrar = list(range(pagina_actual - 2, pagina_actual + 3))

                                mini_cols = st.columns(len(paginas_a_mostrar))
                                for i, pagina in enumerate(paginas_a_mostrar):
                                    with mini_cols[i]:
                                        if pagina == pagina_actual:
                                            st.markdown(
                                                f"<div style='background: #007bff; color: white; text-align: center; padding: 4px; border-radius: 4px; margin: 2px;'>{pagina}</div>",
                                                unsafe_allow_html=True)
                                        else:
                                            if st.button(str(pagina),
                                                         key=f"page_parrafos_{selected_rec_code}_{pagina}"):
                                                st.session_state[pagina_key] = pagina
                                                st.rerun()

                            with cols[4]:
                                if st.button("▶", disabled=(pagina_actual >= total_paginas),
                                             key=f"next_page_parrafos_{selected_rec_code}"):
                                    st.session_state[pagina_key] = min(total_paginas, pagina_actual + 1)
                                    st.rerun()

                # TAB 2: SENTENCE LEVEL
                else:  # "💬 Oraciones"
                    st.markdown("**Análisis por Oraciones:**")

                    sentence_analysis = rec_data.sort_values('sentence_similarity', ascending=False)

                    # PAGINATION FOR SENTENCES
                    coincidencias_por_pagina = 5
                    total_coincidencias = len(sentence_analysis)
                    total_paginas = max(1, (total_coincidencias - 1) // coincidencias_por_pagina + 1)

                    # Initialize current page for this recommendation's sentences
                    pagina_key = f'pagina_actual_coincidencias_{selected_rec_code}_oraciones'
                    if pagina_key not in st.session_state:
                        st.session_state[pagina_key] = 1

                    # Validate current page doesn't exceed total
                    if st.session_state[pagina_key] > total_paginas:
                        st.session_state[pagina_key] = 1

                    pagina_actual = st.session_state[pagina_key]

                    # Apply pagination
                    inicio = (pagina_actual - 1) * coincidencias_por_pagina
                    fin = inicio + coincidencias_por_pagina
                    sentence_analysis_paginado = sentence_analysis.iloc[inicio:fin]

                    # Show pagination info
                    st.write(
                        f"📋 Mostrando {len(sentence_analysis_paginado)} de {total_coincidencias} oraciones (Página {pagina_actual} de {total_paginas})")

                    # Show paginated sentences
                    for idx, (_, row) in enumerate(sentence_analysis_paginado.iterrows()):
                        sentence_id = row.get('sentence_id_paragraph', f'S{idx + 1}')

                        with st.expander(f"Oración {sentence_id} - Similitud: {row['sentence_similarity']:.3f}",
                                         expanded=idx == 0):  # Only first expanded
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write("**Contenido:**")
                                st.write(row['sentence_text'])

                            with col2:
                                st.write("**Métricas:**")
                                if 'sentence_id' in row and pd.notna(row['sentence_id']):
                                    st.write(f"**ID Oración:** {row['sentence_id']}")
                                st.write(f"**ID Página:** {row['page_number']}")
                                st.write(f"**ID Párrafo:** {row.get('paragraph_id', 'N/A')}")
                                st.write(f"**Similitud Oración:** {row['sentence_similarity']:.3f}")
                                st.write(f"**Clasificación ML:** {row['predicted_class']}")

                    # Show pagination controls for sentences
                    if total_paginas > 1:
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            cols = st.columns([1, 1, 3, 1, 1])

                            with cols[0]:
                                if st.button("◀", disabled=(pagina_actual <= 1),
                                             key=f"prev_page_oraciones_{selected_rec_code}"):
                                    st.session_state[pagina_key] = max(1, pagina_actual - 1)
                                    st.rerun()

                            with cols[2]:
                                paginas_a_mostrar = []
                                if total_paginas <= 5:
                                    paginas_a_mostrar = list(range(1, total_paginas + 1))
                                else:
                                    if pagina_actual <= 3:
                                        paginas_a_mostrar = [1, 2, 3, 4, 5]
                                    elif pagina_actual >= total_paginas - 2:
                                        paginas_a_mostrar = list(range(total_paginas - 4, total_paginas + 1))
                                    else:
                                        paginas_a_mostrar = list(range(pagina_actual - 2, pagina_actual + 3))

                                mini_cols = st.columns(len(paginas_a_mostrar))
                                for i, pagina in enumerate(paginas_a_mostrar):
                                    with mini_cols[i]:
                                        if pagina == pagina_actual:
                                            st.markdown(
                                                f"<div style='background: #007bff; color: white; text-align: center; padding: 4px; border-radius: 4px; margin: 2px;'>{pagina}</div>",
                                                unsafe_allow_html=True)
                                        else:
                                            if st.button(str(pagina),
                                                         key=f"page_oraciones_{selected_rec_code}_{pagina}"):
                                                st.session_state[pagina_key] = pagina
                                                st.rerun()

                            with cols[4]:
                                if st.button("▶", disabled=(pagina_actual >= total_paginas),
                                             key=f"next_page_oraciones_{selected_rec_code}"):
                                    st.session_state[pagina_key] = min(total_paginas, pagina_actual + 1)
                                    st.rerun()

        else:
            st.info("No hay recomendaciones disponibles con el filtro actual.")

    else:
        # VISTA COMPARATIVA - SOLO LAS MÉTRICAS GENERALES
        st.markdown(f"""
                <div style="background: linear-gradient(90deg, #6c757d 0%, #495057 100%); 
                            color: white; 
                            padding: 2rem; 
                            border-radius: 15px; 
                            margin-bottom: 2rem;
                            text-align: center;">
                    <h1 style="margin: 0;">📊 Vista Comparativa</h1>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">
                        {f"Departamento: {selected_department}" if selected_department != 'Todos' else "Todos los municipios"}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Municipios", filtered_df['mpio'].nunique())
        with col2:
            st.metric("Departamentos", filtered_df['dpto'].nunique())
        with col3:
            st.metric("Recomendaciones", filtered_df['recommendation_code'].nunique())
        with col4:
            avg_similarity = filtered_df['sentence_similarity'].mean()
            st.metric("Similitud Promedio", f"{avg_similarity:.3f}")

        st.info("💡 Seleccione un municipio específico en la barra lateral para ver el reporte detallado.")

    # ==================================================
    # SECTION 4: RECOMMENDATIONS DICTIONARY
    # ==================================================

    st.markdown("---")
    st.markdown("### 📖 Diccionario de Recomendaciones")

    # Create recommendations dictionary from available data
    if selected_municipality != 'Todos':
        # Use filtered data for specific municipality
        dict_data = filtered_df
    else:
        # Use all data if viewing comparative mode
        dict_data = df
        if include_policy_only:
            dict_data = dict_data[
                (dict_data['predicted_class'] == 'Incluida') |
                ((dict_data['predicted_class'] == 'Excluida') & (dict_data['prediction_confidence'] < 0.8))
                ]

    # Get unique recommendations with their details
    recommendations_dict = dict_data.groupby('recommendation_code').agg({
        'recommendation_text': 'first',
        'recommendation_topic': 'first',
        'recommendation_priority': 'first',
        'sentence_similarity': ['count', 'mean', 'max'],
        'mpio': lambda x: x.nunique() if selected_municipality == 'Todos' else x.iloc[0]
    }).reset_index()

    recommendations_dict.columns = ['Código', 'Texto', 'Tema', 'Priorizado_GN', 'Total_Menciones',
                                    'Similitud_Promedio', 'Similitud_Máxima', 'Municipios_Implementan']
    recommendations_dict = recommendations_dict.sort_values('Código')


    # Get unique recommendations with their details
    recommendations_dict = dict_data.groupby('recommendation_code').agg({
        'recommendation_text': 'first',
        'recommendation_topic': 'first',
        'recommendation_priority': 'first',
        'sentence_similarity': ['count', 'mean', 'max'],
        'mpio': lambda x: x.nunique() if selected_municipality == 'Todos' else x.iloc[0]
    }).reset_index()

    recommendations_dict.columns = ['Código', 'Texto', 'Tema', 'Priorizado_GN', 'Total_Menciones',
                                    'Similitud_Promedio', 'Similitud_Máxima', 'Municipios_Implementan']
    recommendations_dict = recommendations_dict.sort_values('Código')

    # Search and filter options
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Buscar recomendación:",
            placeholder="Ingrese código o palabras clave...",
            help="Busque por código de recomendación o palabras en el texto"
        )

    with col2:
        if 'recommendation_topic' in dict_data.columns:
            available_topics = ['Todos'] + sorted(
                dict_data['recommendation_topic'].dropna().unique().tolist())
            selected_topic = st.selectbox(
                "Filtrar por tema:",
                options=available_topics,
                index=0
            )
        else:
            selected_topic = 'Todos'

    with col3:
        priority_filter = st.selectbox(
            "Prioridad GN:",
            options=['Todos', 'Solo priorizadas', 'Solo no priorizadas'],
            index=0
        )

    # Apply filters
    filtered_dict = recommendations_dict.copy()

    if search_term:
        mask = (
                filtered_dict['Código'].str.contains(search_term, case=False, na=False) |
                filtered_dict['Texto'].str.contains(search_term, case=False, na=False)
        )
        filtered_dict = filtered_dict[mask]

    if selected_topic != 'Todos':
        filtered_dict = filtered_dict[filtered_dict['Tema'] == selected_topic]

    if priority_filter == 'Solo priorizadas':
        filtered_dict = filtered_dict[filtered_dict['Priorizado_GN'] == 1]
    elif priority_filter == 'Solo no priorizadas':
        filtered_dict = filtered_dict[filtered_dict['Priorizado_GN'] == 0]

    # Display results count
    st.markdown(f"**Mostrando {len(filtered_dict)} de {len(recommendations_dict)} recomendaciones**")

    # Display recommendations
    if not filtered_dict.empty:
        for idx, row in filtered_dict.iterrows():
            with st.expander(f"**{row['Código']}** - {row['Texto'][:80]}...", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown("**Descripción completa:**")
                    st.write(row['Texto'])

                    if pd.notna(row['Tema']):
                        st.markdown(f"**Tema:** {row['Tema']}")

                with col2:
                    st.markdown("**Información:**")
                    st.write(f"**Código:** {row['Código']}")

                    if pd.notna(row['Priorizado_GN']):
                        priority_text = "Sí" if row['Priorizado_GN'] == 1 else "No"
                        priority_color = "🔴" if row['Priorizado_GN'] == 1 else "⚪"
                        st.write(f"**Priorizado por GN:** {priority_color} {priority_text}")

                    st.markdown("**Estadísticas:**")
                    if selected_municipality == 'Todos':
                        st.write(f"**Municipios que implementan:** {row['Municipios_Implementan']}")
                    st.write(f"**Total menciones:** {row['Total_Menciones']}")
                    st.write(f"**Similitud promedio:** {row['Similitud_Promedio']:.3f}")
                    st.write(f"**Similitud máxima:** {row['Similitud_Máxima']:.3f}")
    else:
        st.info("No se encontraron recomendaciones que coincidan con los criterios de búsqueda.")


if __name__ == "__main__":
    main()