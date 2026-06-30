import os
import re
import urllib.request
import urllib.parse
import json
import time
import ssl
import webbrowser

def parse_line(line):
    line = line.strip()
    if not line:
        return None
        
    index_match = re.match(r'^\[\d+\]\s*(\d+)\.\s*(.*)', line)
    if not index_match:
        return None
        
    index = int(index_match.group(1))
    content = index_match.group(2)
    
    year_match = re.search(r'\((19\d{2}|20\d{2}|n\.d\.-?[a-z]?)(?:,\s*[A-Za-z]+\s*\d*)?\)', content)
    if year_match:
        year = year_match.group(1)
        authors_part = content[:year_match.start()].strip()
        rest = content[year_match.end():].strip()
    else:
        year = "unknown"
        authors_part = "unknown"
        rest = content
        
    author_name = "Author"
    if authors_part and authors_part != "unknown":
        first_author = authors_part.split('.')[0].strip()
        first_author = first_author.split(',')[0].strip()
        author_name = re.sub(r'[^a-zA-Z0-9]', '', first_author)
        if not author_name:
            author_name = "Author"
            
    doi_match = re.search(r'10\.\d{4,9}/[^\s]+', rest)
    doi = None
    if doi_match:
        doi = doi_match.group(0).rstrip('.,;)')
        
    url_match = re.search(r'https?://[^\s]+', rest)
    url = None
    if url_match:
        url = url_match.group(0).rstrip('.,;)')
        
    if index == 10 and "pdfhttps://" in line:
        url = "https://www.adces.org/docs/default-source/dana-files/adc-23842v3-revised-august-3-2020cd070ee4-83cd-472c-a990-892684a26df3.pdf"
        
    if url and 'doi.org/' in url:
        extracted_doi = url.split('doi.org/')[-1].strip().rstrip('.,;)')
        if extracted_doi:
            doi = extracted_doi
            
    parts = [p.strip() for p in rest.split('.') if p.strip()]
    title = "Title"
    for part in parts:
        if part.startswith('http') or 'doi.org' in part or len(part) < 5:
            continue
        title = part
        break
        
    title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    title_clean = "_".join(title_clean.split()[:5])
    
    filename = f"{index:02d}_{author_name}_{year}_{title_clean}.pdf"
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    return {
        'index': index,
        'author': author_name,
        'year': year,
        'title': title,
        'doi': doi,
        'url': url,
        'filename': filename
    }

def extract_scihub_pdf_url(html, base_url):
    embed_match = re.search(r'<embed[^>]+src=["\']([^"\']+)["\']', html)
    if embed_match:
        url = embed_match.group(1)
        if url.startswith('//'):
            return 'https:' + url
        return urllib.parse.urljoin(base_url, url)
        
    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    if iframe_match:
        url = iframe_match.group(1)
        if url.startswith('//'):
            return 'https:' + url
        return urllib.parse.urljoin(base_url, url)
        
    onclick_match = re.search(r'onclick\s*=\s*["\']location\.href\s*=\s*[\'"]([^\'"]+)[\'"]', html)
    if onclick_match:
        url = onclick_match.group(1)
        if url.startswith('//'):
            return 'https:' + url
        return urllib.parse.urljoin(base_url, url)
        
    return None

def download_file(url, filepath):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20, context=context) as response:
            content_type = response.info().get_content_type()
            if 'html' in content_type:
                return False
            with open(filepath, 'wb') as f:
                f.write(response.read())
            return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def check_captcha(html):
    html_lower = html.lower()
    indicators = [
        'captcha', 'robot', 'робота', 'verificación', 'verification', 
        'altcha-widget', 'just a moment', 'cloudflare'
    ]
    for ind in indicators:
        if ind in html_lower:
            return True
    return False

def try_download_scihub(doi, dest_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    context = ssl._create_unverified_context()
    mirrors = [
        'https://sci-hub.ru/',
        'https://sci-hub.st/',
        'https://sci-hub.se/'
    ]
    
    for mirror in mirrors:
        url = mirror + doi
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15, context=context) as response:
                html = response.read().decode('utf-8', errors='ignore')
                if check_captcha(html):
                    # We got blocked by captcha on this mirror
                    continue
                    
                pdf_url = extract_scihub_pdf_url(html, mirror)
                if pdf_url:
                    print(f"  Found PDF URL: {pdf_url}")
                    if download_file(pdf_url, dest_path):
                        return True
        except Exception:
            pass
    return False

def main():
    biblio_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\bibliography.txt"
    dest_dir = r"C:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    report_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\download_report.json"
    
    with open(biblio_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    parsed_items = []
    for line in lines:
        item = parse_line(line)
        if item:
            parsed_items.append(item)
            
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        report_dict = {item['index']: item for item in report_data}
    else:
        report_dict = {}

    print("=== INICIANDO DESCARGA INTERACTIVA CON CONTROL DE CAPTCHAS ===")
    print("El script se detendrá si detecta un CAPTCHA, abrirá Sci-Hub en tu navegador y esperará a que lo resuelvas.")
    
    new_downloads = 0
    
    for item in parsed_items:
        idx = item['index']
        filename = item['filename']
        dest_path = os.path.join(dest_dir, filename)
        
        # Check if already successfully downloaded
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            continue
            
        # We need to try downloading this DOI
        if not item['doi']:
            continue
            
        print(f"\n[{idx}/43] Procesando: {item['author']} ({item['year']}) - {item['title'][:60]}...")
        
        # Try downloading automatically first
        print("  Intentando descarga automatica desde Sci-Hub...")
        if try_download_scihub(item['doi'], dest_path):
            print("  [OK] Descargado con exito!")
            report_dict[idx] = {
                'index': idx,
                'status': 'Success',
                'filename': filename,
                'doi': item['doi'],
                'source': 'Sci-Hub Interactive'
            }
            new_downloads += 1
            time.sleep(2)
            continue
            
        # If it failed, it is likely due to captcha. Let's do the interactive loop
        mirror_to_use = 'https://sci-hub.ru/'
        sci_hub_url = mirror_to_use + item['doi']
        print(f"  [ALERTA] CAPTCHA DETECTADO o error de conexion. Abriendo mirror: {sci_hub_url}")
        
        # Open in default browser
        webbrowser.open(sci_hub_url)
        
        # Prompt the user
        print("-" * 60)
        print(" ACCIÓN REQUERIDA:")
        print(" 1. Se ha abierto la página de Sci-Hub en tu navegador.")
        print(" 2. Resuelve el CAPTCHA (si aparece) hasta que veas el artículo en pantalla.")
        print(" 3. Una vez resuelto, regresa a esta consola y presiona ENTER.")
        print(" (Escribe 's' y ENTER si deseas saltar este artículo)")
        print("-" * 60)
        
        user_input = input("Presiona ENTER para continuar o 's' para saltar: ").strip().lower()
        if user_input == 's':
            print("  Artículo saltado.")
            continue
            
        # Try again now that the user has solved the captcha (IP should be cleared)
        print("  Reintentando descarga después de la validación del usuario...")
        # Give a small 2s pause
        time.sleep(2)
        
        if try_download_scihub(item['doi'], dest_path):
            print("  [OK] Descargado con exito tras resolver captcha!")
            report_dict[idx] = {
                'index': idx,
                'status': 'Success',
                'filename': filename,
                'doi': item['doi'],
                'source': 'Sci-Hub Interactive (Captcha Solved)'
            }
            new_downloads += 1
        else:
            print("  [ERROR] No se pudo descargar automaticamente. Se requiere descarga manual.")
            
        time.sleep(2)
        
    # Save the updated report
    updated_report = [report_dict[k] for k in sorted(report_dict.keys())]
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(updated_report, f, indent=4)
        
    # Regenerate dashboard
    print("\nRegenerando panel de control...")
    os.system(f"python c:\\Users\\aru_a\\OneDrive\\1.Doctorado\\9.Tesis\\Capítulo_3\\Codigo\\generate_dashboard.py")
    
    print("\n" + "=" * 40)
    print(f"PROCESO TERMINADO. Nuevas descargas: {new_downloads}")
    print("=" * 40)

if __name__ == '__main__':
    main()
