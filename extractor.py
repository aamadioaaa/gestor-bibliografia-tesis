import re
import os
import json
import docx
from pypdf import PdfReader

def extract_text_from_docx(file_path):
    """Extrae todos los párrafos de un archivo .docx en una lista de strings."""
    doc = docx.Document(file_path)
    return [p.text for p in doc.paragraphs if p.text.strip()]

def extract_text_from_pdf(file_path):
    """Extrae el texto de un archivo .pdf por páginas y luego lo divide por líneas."""
    reader = PdfReader(file_path)
    lines = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            for line in text.splitlines():
                if line.strip():
                    lines.append(line.strip())
    return lines

def find_bibliography_section(lines):
    """
    Encuentra la sección de bibliografía/referencias en la lista de líneas.
    Retorna la lista de líneas desde la sección de bibliografía hasta el final.
    """
    keywords = [
        'bibliografia', 'bibliografía', 'referencias', 'references', 
        'bibliography', 'trabajos citados', 'obras citadas'
    ]
    
    found_idx = -1
    for idx, line in enumerate(lines):
        clean_line = re.sub(r'[^a-zA-ZáéíóúññÁÉÍÓÚ]', '', line.lower()).strip()
        # Verificar si la línea coincide con alguna palabra clave exacta o inicia con ella
        if any(clean_line == kw or clean_line.startswith(kw) for kw in keywords):
            found_idx = idx
            
    if found_idx != -1:
        print(f"Sección de bibliografía encontrada en la línea {found_idx}: '{lines[found_idx]}'")
        return lines[found_idx + 1:]
    else:
        print("No se encontró una cabecera de bibliografía clara. Procesando todo el documento.")
        return lines

def clean_doi(text):
    """Extrae y limpia un DOI del texto de una referencia."""
    if not text:
        return None
    # Regex estándar para DOI
    doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', text, re.IGNORECASE)
    if doi_match:
        doi = doi_match.group(1).strip()
        # Limpiar caracteres sobrantes al final
        while doi and doi[-1] in ['.', ',', ';', ')', ']', '>']:
            doi = doi[:-1]
        return doi
    return None

def extract_metadata(ref_text):
    """Extrae metadatos aproximados (autor, año, título) de una referencia."""
    import unicodedata
    
    # 1. Limpiar lista numerada inicial
    clean_ref = re.sub(r'^\[\d+\]\s*', '', ref_text)
    clean_ref = re.sub(r'^\d+\s*[\.\-]\s*', '', clean_ref)
    clean_ref = clean_ref.strip()
    
    # 2. Buscar año en paréntesis (ej: 2018, n.d., etc.)
    year_match = re.search(r'\((19\d{2}|20\d{2}|n\.d\.-?[a-z]?)(?:,\s*[A-Za-z]+\s*\d*)?\)', clean_ref)
    if year_match:
        year = year_match.group(1)
        authors_part = clean_ref[:year_match.start()].strip()
        rest = clean_ref[year_match.end():].strip()
    else:
        year = "n.d."
        # Buscar año sin paréntesis como fallback
        year_match_no_p = re.search(r'\b(19\d{2}|20\d{2})\b', clean_ref)
        if year_match_no_p:
            year = year_match_no_p.group(1)
            authors_part = clean_ref[:year_match_no_p.start()].strip()
            rest = clean_ref[year_match_no_p.end():].strip()
        else:
            authors_part = "Author"
            rest = clean_ref
            
    # Limpiar autores
    author = authors_part.strip().strip('.').strip(',').strip()
    if not author or len(author) < 2:
        author = "Author"
        
    # Extraer título del resto
    parts = [p.strip() for p in rest.split('.') if p.strip()]
    title = "Title"
    for part in parts:
        if part.startswith('http') or 'doi.org' in part or len(part) < 5 or part.lower().startswith('doi:'):
            continue
        title = part
        break
        
    if title == "Title" and len(rest) > 10:
        title = rest[:50]
        
    # Normalizar para nombres de archivo limpios (quitar acentos, CamelCase)
    def to_ascii_clean(s):
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
        return re.sub(r'[^a-zA-Z0-9\s_-]', '', s)
        
    author_clean = to_ascii_clean(author).strip()
    author_words = author_clean.split()
    author_val = "".join(w.capitalize() for w in author_words[:2]) if author_words else "Author"
    
    title_clean = to_ascii_clean(title).strip()
    title_words = title_clean.split()[:5] # Máximo 5 palabras
    title_val = "_".join(w.capitalize() for w in title_words) if title_words else "Title"
    
    return author_val, year, title_val

def group_pdf_lines_into_references(lines):
    """
    Agrupa las líneas de un PDF en referencias individuales basándose en patrones de inicio.
    """
    references = []
    current_ref = []
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        # Detectar si la línea inicia una nueva referencia:
        # 1. Inicia con corchetes: [1] o [12]
        # 2. Inicia con números seguidos de punto: 1. o 12.
        # 3. Empieza con año en paréntesis: (2002)
        # 4. Empieza con un formato de nombre APA clásico: Apellido, N.
        is_new = (
            re.match(r'^\[\d+\]', line_strip) or
            re.match(r'^\d+\s*[\.\-]\s', line_strip) or
            re.match(r'^\([12]\d{3}\)', line_strip) or
            re.match(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s+[A-Z]\.', line_strip)
        )
        
        if is_new and current_ref:
            references.append(" ".join(current_ref))
            current_ref = [line_strip]
        else:
            current_ref.append(line_strip)
            
    if current_ref:
        references.append(" ".join(current_ref))
        
    return references

def process_file_to_references(file_path):
    """
    Procesa un archivo .docx o .pdf y retorna una lista de diccionarios con
    las referencias estructuradas.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.docx':
        lines = extract_text_from_docx(file_path)
        bib_lines = find_bibliography_section(lines)
        # En Word, cada párrafo de la bibliografía suele ser una referencia completa
        raw_references = bib_lines
    elif ext == '.pdf':
        lines = extract_text_from_pdf(file_path)
        bib_lines = find_bibliography_section(lines)
        raw_references = group_pdf_lines_into_references(bib_lines)
    else:
        raise ValueError(f"Extensión de archivo no soportada: {ext}")
        
    structured_references = []
    for idx, ref in enumerate(raw_references):
        ref_text = ref.strip()
        if not ref_text or len(ref_text) < 15:
            continue
            
        doi = clean_doi(ref_text)
        author, year, title = extract_metadata(ref_text)
        
        # Normalizar el nombre de archivo de salida
        safe_author = re.sub(r'[^a-zA-Z0-9]', '', author)
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title)[:30].strip('_')
        filename = f"{idx+1:02d}_{safe_author}_{year}_{safe_title}.pdf"
        
        structured_references.append({
            'index': idx + 1,
            'reference_text': ref_text,
            'doi': doi,
            'author': author,
            'year': year,
            'title': title,
            'filename': filename,
            'status': 'Failed',  # Estado inicial
            'source': 'None'
        })
        
    return structured_references

if __name__ == '__main__':
    # Test rápido con la tesis si existe
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    files = [f for f in os.listdir(parent_dir) if f.endswith('.docx') and 'Walter_Dino_rev' in f]
    if files:
        tesis_path = os.path.join(parent_dir, files[0])
        print(f"Probando extractor con {tesis_path}...")
        refs = process_file_to_references(tesis_path)
        print(f"Extracción completada. Encontradas {len(refs)} referencias.")
        if refs:
            print("Ejemplo de primera referencia extraída:")
            print(json.dumps(refs[0], indent=2))
