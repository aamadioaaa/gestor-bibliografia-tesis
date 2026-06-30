from curl_cffi import requests
import urllib.parse
import re
import json
import hashlib
import base64
import os
import time
import ssl

def solve_altcha(challenge_data):
    algorithm = challenge_data.get('algorithm', 'SHA-256')
    challenge = challenge_data.get('challenge')
    salt = challenge_data.get('salt')
    max_number = challenge_data.get('maxNumber', challenge_data.get('maxnumber', 1000000))
    
    if algorithm != 'SHA-256':
        return None
        
    for number in range(max_number + 1):
        data = f"{salt}{number}".encode('utf-8')
        h = hashlib.sha256(data).hexdigest()
        if h == challenge:
            payload = {
                "algorithm": algorithm,
                "challenge": challenge,
                "number": number,
                "salt": salt,
                "signature": challenge_data.get('signature')
            }
            payload_json = json.dumps(payload)
            payload_b64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
            return payload_b64
    return None

def find_doi_via_crossref(reference_text):
    """
    Busca en CrossRef usando el texto plano de la referencia.
    Utiliza una verificación de coincidencia muy estricta para evitar falsos positivos.
    """
    query = re.sub(r'^[\[\]\d\.\s]+', '', reference_text)
    query = re.sub(r'https?://\S+', '', query).strip()
    
    if len(query) < 15:
        return None
        
    url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows=1"
    try:
        r = requests.get(url, impersonate="chrome", timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get('message', {}).get('items', [])
            if items:
                best_match = items[0]
                doi = best_match.get('DOI')
                
                title_list = best_match.get('title', [])
                if title_list and doi:
                    title = title_list[0].lower()
                    
                    # Coincidencia estricta de palabras
                    ref_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
                    title_words = set(re.findall(r'\b\w{4,}\b', title))
                    
                    intersection = ref_words.intersection(title_words)
                    min_match = min(4, len(title_words)) if title_words else 0
                    
                    # El 50% de las palabras del título o al menos 4 palabras clave deben coincidir
                    if len(intersection) >= min_match and (len(title_words) == 0 or len(intersection) / len(title_words) >= 0.5):
                        print(f"  [CrossRef] DOI verificado encontrado: {doi} (Título: {title_list[0]})")
                        return doi
                    else:
                        print(f"  [CrossRef] Coincidencia descartada (Falso positivo probable). Ref: '{query[:40]}' vs Encontrado: '{title[:40]}'")
    except Exception as e:
        print(f"  [CrossRef] Error al consultar: {e}")
    return None

def download_via_web_search(reference_text, dest_path):
    """
    Busca en DuckDuckGo HTML links directos de PDF para la referencia y los descarga.
    """
    query = re.sub(r'^[\[\]\d\.\s]+', '', reference_text)
    query = re.sub(r'https?://\S+', '', query).strip()
    query = re.sub(r'\[(?:pdf|html|online|epub)\]', '', query, flags=re.IGNORECASE).strip()
    
    if len(query) < 15:
        return False
        
    search_query = f"{query} filetype:pdf"
    print(f"  [Búsqueda Web] Buscando en DuckDuckGo: {search_query[:60]}...")
    
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        if r.status_code == 200:
            uddg_links = re.findall(r'uddg=([^&"\']+)', r.text)
            pdf_urls = []
            
            for link in uddg_links:
                decoded_url = urllib.parse.unquote(link)
                if decoded_url.lower().endswith('.pdf') or '.pdf?' in decoded_url.lower():
                    pdf_urls.append(decoded_url)
                    
            # Fallback
            if not pdf_urls:
                all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', r.text)
                for href in all_hrefs:
                    if 'uddg=' in href:
                        clean_url = href.split('uddg=')[-1].split('&')[0]
                        decoded_url = urllib.parse.unquote(clean_url)
                        if '.pdf' in decoded_url.lower():
                            pdf_urls.append(decoded_url)
            
            # Quitar duplicados
            seen = set()
            pdf_urls = [x for x in pdf_urls if not (x in seen or seen.add(x))]
            
            # Descargar el primer PDF que responda con éxito
            for pdf_url in pdf_urls[:3]:
                print(f"  [Búsqueda Web] Intentando descargar: {pdf_url}")
                try:
                    r_pdf = requests.get(pdf_url, impersonate="chrome", timeout=20, verify=False)
                    if r_pdf.status_code == 200 and r_pdf.content.startswith(b'%PDF'):
                        with open(dest_path, 'wb') as f:
                            f.write(r_pdf.content)
                        print("  [Búsqueda Web] ¡PDF descargado con éxito!")
                        return True
                except Exception as dl_err:
                    print(f"    Fallo de descarga: {dl_err}")
    except Exception as e:
        print(f"  [Búsqueda Web] Error de búsqueda: {e}")
    return False

def get_metadata_by_doi(doi):
    """
    Busca los metadatos oficiales del DOI en CrossRef y retorna (author, year, title) normalizados.
    """
    import unicodedata
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    try:
        r = requests.get(url, impersonate="chrome", timeout=10)
        if r.status_code == 200:
            data = r.json()
            work = data.get('message', {})
            
            # Author
            authors = work.get('author', [])
            first_author = "Author"
            if authors:
                first_author = authors[0].get('family', authors[0].get('given', 'Author'))
                
            # Year
            created = work.get('created', {})
            date_parts = created.get('date-parts', [[None]])
            year = "n.d."
            if date_parts and date_parts[0][0]:
                year = str(date_parts[0][0])
            else:
                issued = work.get('issued', {})
                date_parts = issued.get('date-parts', [[None]])
                if date_parts and date_parts[0][0]:
                    year = str(date_parts[0][0])
            
            # Title
            title_list = work.get('title', [])
            title = "Title"
            if title_list:
                title = title_list[0]
                
            # Normalizar
            def to_ascii_clean(s):
                s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
                return re.sub(r'[^a-zA-Z0-9\s_-]', '', s)
                
            author_clean = to_ascii_clean(first_author).strip()
            author_words = author_clean.split()
            author_val = "".join(w.capitalize() for w in author_words[:2]) if author_words else "Author"
            
            title_clean = to_ascii_clean(title).strip()
            title_words = title_clean.split()[:5]
            title_val = "_".join(w.capitalize() for w in title_words) if title_words else "Title"
            
            return author_val, year, title_val
    except Exception as e:
        print(f"  [CrossRef Metadata] Error al consultar metadatos: {e}")
    return None

def download_unpaywall(doi, dest_path):
    """
    Intenta descargar el PDF desde Unpaywall (Open Access).
    """
    url = f"https://api.unpaywall.org/v2/{doi}?email=research_group@univ.edu"
    try:
        r = requests.get(url, impersonate="chrome", timeout=10)
        if r.status_code == 200:
            data = r.json()
            best_oa_location = data.get('best_oa_location')
            if best_oa_location and best_oa_location.get('url_for_pdf'):
                pdf_url = best_oa_location.get('url_for_pdf')
                print(f"  [Unpaywall] Encontrado PDF libre: {pdf_url}")
                
                # Fetch PDF
                r_pdf = requests.get(pdf_url, impersonate="chrome", timeout=25, verify=False)
                if r_pdf.status_code == 200 and r_pdf.content.startswith(b'%PDF'):
                    with open(dest_path, 'wb') as f:
                        f.write(r_pdf.content)
                    return True
    except Exception as e:
        print(f"  [Unpaywall] Error o timeout: {e}")
    return False

def download_europepmc(doi, dest_path):
    """
    Busca el PMCID asociado al DOI en Europe PMC y descarga el PDF renderizado.
    """
    search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&format=json"
    try:
        r = requests.get(search_url, impersonate="chrome", timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get('resultList', {}).get('result', [])
            if results:
                pmcid = results[0].get('pmcid')
                if pmcid:
                    render_url = f"https://europepmc.org/articles/{pmcid}?pdf=render"
                    print(f"  [Europe PMC] Encontrado PMCID: {pmcid}. Intentando descargar render...")
                    
                    r_pdf = requests.get(render_url, impersonate="chrome", timeout=30)
                    if r_pdf.status_code == 200 and r_pdf.content.startswith(b'%PDF'):
                        with open(dest_path, 'wb') as f:
                            f.write(r_pdf.content)
                        return True
    except Exception as e:
        print(f"  [Europe PMC] Error o timeout: {e}")
    return False

def download_scihub_ren(doi, dest_path):
    """
    Descarga del mirror sci-hub.ren usando curl-cffi y resolución de captcha Altcha.
    """
    mirror = "https://sci-hub.ren/"
    url = mirror + doi
    session = requests.Session()
    
    try:
        response = session.get(url, impersonate="chrome", timeout=15)
        html = response.text
        
        # Captcha Check
        if "captcha" in html.lower() or "verification" in html.lower():
            widget_match = re.search(r'challengeurl\s*=\s*["\']([^"\']+)["\']', html)
            solution_id_match = re.search(r'/captcha/solution/(\d+)', html)
            
            if widget_match and solution_id_match:
                challenge_path = widget_match.group(1)
                solution_id = solution_id_match.group(1)
                challenge_url = urllib.parse.urljoin(mirror, challenge_path)
                solution_url = urllib.parse.urljoin(mirror, f"/captcha/solution/{solution_id}")
                
                res_chall = session.get(challenge_url, impersonate="chrome", timeout=10)
                challenge_data = res_chall.json()
                
                solution_b64 = solve_altcha(challenge_data)
                if solution_b64:
                    post_data = {"captcha": solution_b64}
                    res_sol = session.post(solution_url, json=post_data, impersonate="chrome", timeout=10)
                    if res_sol.json().get('success'):
                        response = session.get(url, impersonate="chrome", timeout=15)
                        html = response.text
                    else:
                        return False
            else:
                return False
                
        # Parse PDF Link
        pdf_match = re.search(r'src\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']', html, re.IGNORECASE)
        if pdf_match:
            pdf_path = pdf_match.group(1)
            if '#' in pdf_path:
                pdf_path = pdf_path.split('#')[0]
            if pdf_path.startswith('//'):
                pdf_url = 'https:' + pdf_path
            else:
                pdf_url = urllib.parse.urljoin(mirror, pdf_path)
                
            headers = {'Referer': url}
            pdf_res = session.get(pdf_url, headers=headers, impersonate="chrome", timeout=30)
            
            if pdf_res.status_code == 200 and pdf_res.content.startswith(b'%PDF'):
                with open(dest_path, 'wb') as f:
                    f.write(pdf_res.content)
                return True
                
    except Exception as e:
        print(f"  [Sci-Hub.ren] Error: {e}")
    return False

def download_reference(reference_text, doi=None, dest_path=None):
    """
    Orquesta la descarga priorizando la búsqueda web por título de PDF,
    y luego usando APIs con DOI verificado estrictamente.
    Retorna (success, source, found_doi, metadata)
    """
    # 1. Intentar primero búsqueda directa en la web por el nombre/texto de la referencia
    if reference_text:
        if download_via_web_search(reference_text, dest_path):
            # Si tiene éxito, intentamos resolver el DOI para los metadatos oficiales del renombrado
            found_doi = doi if doi else find_doi_via_crossref(reference_text)
            metadata = get_metadata_by_doi(found_doi) if found_doi else None
            return True, "Direct Web Search", found_doi, metadata
            
    # 2. Si falla la búsqueda web o no tiene PDF directo, proceder con DOI
    found_doi = doi
    if not found_doi and reference_text:
        found_doi = find_doi_via_crossref(reference_text)
        
    if not found_doi:
        return False, "None", None, None
        
    # Obtener metadatos oficiales
    metadata = get_metadata_by_doi(found_doi)
    
    # Intentar descargar usando el DOI secuencialmente
    # Unpaywall
    if download_unpaywall(found_doi, dest_path):
        return True, "Unpaywall (Open Access)", found_doi, metadata
        
    # Europe PMC
    if download_europepmc(found_doi, dest_path):
        return True, "Europe PMC PMCID Render", found_doi, metadata
        
    # Sci-Hub.ren
    if download_scihub_ren(found_doi, dest_path):
        return True, "Sci-Hub.ren", found_doi, metadata
        
    return False, "None", found_doi, metadata
