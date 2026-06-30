import streamlit as st
import os
import re
import json
import time
import webbrowser
import extractor
import downloader
import subprocess

def select_folder_modern(initial_dir):
    """
    Abre la ventana de diálogo moderna del Explorador de Windows usando Tkinter.
    Se asegura de traer la ventana al frente (topmost) y forzar el foco en pantalla.
    """
    import tkinter as tk
    from tkinter import filedialog
    try:
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes('-topmost', True)
        root.focus_force()
        folder_path = filedialog.askdirectory(
            initialdir=initial_dir if os.path.exists(initial_dir) else None,
            title="Seleccionar carpeta de descarga"
        )
        root.destroy()
        if folder_path:
            return os.path.normpath(folder_path)
    except Exception as e:
        print(f"Error al abrir selector de carpetas: {e}")
    return None

# Page config
st.set_page_config(
    page_title="Gestor Universal de Bibliografía",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Modern color system & variables */
    :root {
        --primary-gradient: linear-gradient(135deg, #00c6ff, #0072ff);
        --card-bg: #1f293d;
        --text-color: #f1f5f9;
        --border-color: #38bdf8;
    }
    
    /* Global styles */
    .stApp {
        background-color: #0f172a;
        color: #f1f5f9;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #0284c7, #0369a1);
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .header-title {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .header-subtitle {
        color: #e0f2fe;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Stat cards */
    .stat-card {
        background: #1e293b;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #38bdf8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stat-number {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38bdf8;
        margin-bottom: 0.2rem;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Input & Button modifications */
    div.stButton > button {
        background: linear-gradient(135deg, #0284c7, #0284c7);
        color: white;
        border: none;
        padding: 0.6rem 1.8rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0369a1, #0284c7);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.4);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Main layout
st.markdown("""
<div class="header-card">
    <div class="header-title">📚 Gestor Universal de Bibliografía</div>
    <div class="header-subtitle">Carga tus capítulos o artículos científicos en Word o PDF, edita sus DOIs e inicia descargas en lote evadiendo firewalls automáticamente.</div>
</div>
""", unsafe_allow_html=True)

# Sidebar configurations
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Detectar si estamos en local (con GUI) o en la nube (sin GUI/headless)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()
        HAS_GUI = True
    except Exception:
        HAS_GUI = False
        
    import tempfile
    if HAS_GUI:
        default_dir = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    else:
        default_dir = os.path.join(tempfile.gettempdir(), "biblio_downloads")
        
    if 'dest_dir' not in st.session_state:
        st.session_state.dest_dir = default_dir
        
    st.markdown("**Carpeta de destino:**")
    
    # Siempre permitimos escribir o ver la ruta en una caja de texto
    dest_dir = st.text_input(
        "Ruta de Descarga Local", 
        value=st.session_state.dest_dir,
        label_visibility="collapsed"
    )
    st.session_state.dest_dir = dest_dir
    
    if HAS_GUI:
        # En local, agregamos el botón de examinar carpetas
        if st.button("📁 Examinar carpeta", use_container_width=True, help="Selecciona la carpeta en tu computadora"):
            folder_path = select_folder_modern(st.session_state.dest_dir if st.session_state.dest_dir else default_dir)
            if folder_path:
                st.session_state.dest_dir = folder_path
                st.rerun()
    else:
        st.info("☁️ **Servidor en la Nube**: El selector de carpetas visual está desactivado. Escribe la ruta de descarga arriba si lo deseas (se guardará en el servidor y podrás descargar el archivo `.zip` al finalizar).")
        
    dest_dir = st.session_state.dest_dir
    
    if dest_dir:
        if not os.path.exists(dest_dir):
            st.warning("⚠️ La ruta no existe en el servidor. Se creará al descargar.")
        else:
            st.success("✓ Carpeta válida.")
            
    st.markdown("---")
    st.markdown("### 💡 Instrucciones")
    st.markdown("""
    1. **Sube tu archivo** (.docx o .pdf).
    2. La app buscará la sección de **Bibliografía/Referencias** y extraerá los artículos.
    3. Edita o completa los **DOIs** en la tabla si faltan.
    4. Haz clic en **Iniciar Descargas**.
    """)

# Session State Initializations
if 'references' not in st.session_state:
    st.session_state.references = None
if 'download_logs' not in st.session_state:
    st.session_state.download_logs = []
if 'downloading' not in st.session_state:
    st.session_state.downloading = False

# File uploader
uploaded_file = st.file_uploader("Cargar documento de origen (.docx o .pdf)", type=["docx", "pdf"])

if uploaded_file is not None:
    # Save file temporarily to read it
    temp_filename = f"temp_upload_{uploaded_file.name}"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success(f"✓ Archivo cargado con éxito: {uploaded_file.name}")
    
    # Process button
    if st.button("🔍 Extraer Bibliografía"):
        with st.spinner("Buscando referencias y buscando DOIs..."):
            try:
                refs = extractor.process_file_to_references(temp_filename)
                st.session_state.references = refs
                st.session_state.download_logs = []
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

# Display stats and editor if references are loaded
if st.session_state.references:
    refs_data = st.session_state.references
    
    # Stats
    total_refs = len(refs_data)
    with_doi = sum(1 for r in refs_data if r['doi'] is not None)
    without_doi = total_refs - with_doi
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{total_refs}</div>
            <div class="stat-label">Referencias Totales</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card" style="border-left-color: #10b981;">
            <div class="stat-number" style="color: #10b981;">{with_doi}</div>
            <div class="stat-label">Con DOI (Listos)</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card" style="border-left-color: #f59e0b;">
            <div class="stat-number" style="color: #f59e0b;">{without_doi}</div>
            <div class="stat-label">Sin DOI / Manuales</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### ✏️ Edición de Referencias Extraídas")
    st.info("Puedes modificar los campos directamente en la tabla (por ejemplo, agregar un DOI que falte o corregir el nombre del archivo).")
    
    # Edit in Data Editor
    edited_df = st.data_editor(
        refs_data,
        column_order=["index", "author", "year", "title", "doi", "filename", "status", "source"],
        column_config={
            "index": st.column_config.NumberColumn("Índice", disabled=True, width="small"),
            "author": st.column_config.TextColumn("Autor/Editor", width="medium"),
            "year": st.column_config.TextColumn("Año", width="small"),
            "title": st.column_config.TextColumn("Título", width="large"),
            "doi": st.column_config.TextColumn("DOI (Copiar/Editar)", width="medium"),
            "filename": st.column_config.TextColumn("Archivo PDF de Salida", width="medium"),
            "status": st.column_config.TextColumn("Estado", disabled=True),
            "source": st.column_config.TextColumn("Origen de Descarga", disabled=True),
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Save changes back to session state (convert DataFrame to list of dicts)
    import pandas as pd
    if isinstance(edited_df, pd.DataFrame):
        st.session_state.references = edited_df.to_dict(orient='records')
    else:
        st.session_state.references = edited_df
    
    # Action buttons
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        start_download = st.button("🚀 Iniciar Descargas en Lote", disabled=st.session_state.downloading)
        
    # Download Process
    if start_download:
        st.session_state.downloading = True
        
        # Create output dir if not exists
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_block = st.empty()
        
        logs = []
        success_count = 0
        
        for i, item in enumerate(st.session_state.references):
            index = item['index']
            doi = item.get('doi')
            filename = item['filename']
            dest_path = os.path.join(dest_dir, filename)
            
            status_text.text(f"Procesando [{i+1}/{total_refs}]: {filename}")
            progress_bar.progress((i + 1) / total_refs)
            
            logs.append(f"[{index}] Procesando referencia: {filename}")
            log_block.code("\n".join(logs), language="text")
            
            # Run download pipeline (will search CrossRef if DOI is missing)
            success, source, found_doi, metadata = downloader.download_reference(item['reference_text'], doi, dest_path)
            
            if found_doi and found_doi != doi:
                st.session_state.references[i]['doi'] = found_doi
                logs.append(f"  [CrossRef] DOI encontrado: {found_doi}")
                
            # If metadata was successfully retrieved from CrossRef, rename the file cleanly
            if metadata:
                official_author, official_year, official_title = metadata
                new_filename = f"{index:02d}_{official_author}_{official_year}_{official_title}.pdf"
                
                if new_filename != filename:
                    st.session_state.references[i]['filename'] = new_filename
                    st.session_state.references[i]['author'] = official_author
                    st.session_state.references[i]['year'] = official_year
                    st.session_state.references[i]['title'] = official_title
                    
                    if success and os.path.exists(dest_path):
                        new_dest_path = os.path.join(dest_dir, new_filename)
                        try:
                            if os.path.exists(new_dest_path):
                                os.remove(new_dest_path)
                            os.rename(dest_path, new_dest_path)
                            logs.append(f"  [Info] Archivo renombrado a: {new_filename}")
                        except Exception as rename_err:
                            print(f"Error renaming file: {rename_err}")
                
            if success:
                st.session_state.references[i]['status'] = 'Success'
                st.session_state.references[i]['source'] = source
                success_count += 1
                logs.append(f"  ✓ EXITO! Descargado de {source}")
                time.sleep(2)
            else:
                st.session_state.references[i]['status'] = 'Failed'
                st.session_state.references[i]['source'] = 'None'
                logs.append("  ✗ Fallido (no se pudo descargar o resolver).")
                time.sleep(1)
                
            log_block.code("\n".join(logs), language="text")
            
        st.session_state.downloading = False
        status_text.success(f"🎉 Descarga completa! Exitosas: {success_count} de {with_doi} artículos con DOI.")
        st.balloons()
        
        # Re-render list
        st.rerun()

# Downloaded files opener list
if st.session_state.references:
    st.markdown("### 📂 Artículos Descargados")
    
    # Filter downloaded files
    success_refs = [r for r in st.session_state.references if r['status'] == 'Success']
    
    if success_refs:
        # 1. Botón para descargar todo en un archivo ZIP
        import io
        import zipfile
        
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for item in success_refs:
                    filename = item['filename']
                    full_path = os.path.join(dest_dir, filename)
                    if os.path.exists(full_path):
                        zip_file.write(full_path, filename)
            
            st.download_button(
                label="📥 Descargar todos los artículos (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="articulos_descargados.zip",
                mime="application/zip",
                use_container_width=True
            )
        except Exception as zip_err:
            st.error(f"No se pudo crear el archivo ZIP: {zip_err}")
            
        st.write("---")
        
        # 2. Lista de artículos con acciones individuales
        for item in success_refs:
            filename = item['filename']
            full_path = os.path.join(dest_dir, filename)
            
            if os.path.exists(full_path):
                col_name, col_action = st.columns([5, 1.5])
                col_name.markdown(f"**{item['index']}.** {filename} _(Descargado de {item['source']})_")
                
                # Acción condicional según el entorno
                if HAS_GUI:
                    # En local, permite abrir el archivo directamente en el visor del sistema
                    if col_action.button("📄 Abrir", key=f"open_{item['index']}", use_container_width=True):
                        try:
                            os.startfile(full_path)
                        except AttributeError:
                            webbrowser.open(full_path)
                else:
                    # En la nube, permite descargar el archivo PDF de forma individual
                    with open(full_path, "rb") as f_pdf:
                        pdf_data = f_pdf.read()
                    col_action.download_button(
                        label="📥 Descargar",
                        data=pdf_data,
                        file_name=filename,
                        mime="application/pdf",
                        key=f"dl_single_{item['index']}",
                        use_container_width=True
                    )
            else:
                st.warning(f"El archivo {filename} no se encuentra en el servidor temporal.")
    else:
        st.info("Aún no has descargado ningún artículo en este lote. Edita los DOIs e inicia la descarga.")
