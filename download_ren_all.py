from curl_cffi import requests
import json
import re
import urllib.parse
import os
import time

def solve_altcha(challenge_data):
    # In case we hit Altcha on sci-hub.ren (though it didn't show up in our test)
    algorithm = challenge_data.get('algorithm', 'SHA-256')
    challenge = challenge_data.get('challenge')
    salt = challenge_data.get('salt')
    max_number = challenge_data.get('maxNumber', challenge_data.get('maxnumber', 1000000))
    
    if algorithm != 'SHA-256':
        return None
        
    print(f"  [PoW] Resolving Altcha challenge (max: {max_number})...")
    import hashlib
    import base64
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

def download_paper_from_ren(doi, dest_path):
    mirror = "https://sci-hub.ren/"
    url = mirror + doi
    session = requests.Session()
    
    try:
        response = session.get(url, impersonate="chrome", timeout=15)
        html = response.text
        
        # Captcha / Altcha resolution
        if "captcha" in html.lower() or "verification" in html.lower():
            print("  [Captchas] Detectado control de robot. Intentando resolver...")
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
                        print("  [Captchas] Resuelto con exito. Recargando...")
                        response = session.get(url, impersonate="chrome", timeout=15)
                        html = response.text
                    else:
                        print("  [Error] Solucion no aceptada.")
                        return False
            else:
                print("  [Error] No se pudo extraer informacion del captcha.")
                return False
                
        # Parse PDF URL
        pdf_match = re.search(r'src\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']', html, re.IGNORECASE)
        if pdf_match:
            pdf_path = pdf_match.group(1)
            if '#' in pdf_path:
                pdf_path = pdf_path.split('#')[0]
            if pdf_path.startswith('//'):
                pdf_url = 'https:' + pdf_path
            else:
                pdf_url = urllib.parse.urljoin(mirror, pdf_path)
                
            print(f"  Descargando PDF desde: {pdf_url}")
            headers = {'Referer': url}
            pdf_res = session.get(pdf_url, headers=headers, impersonate="chrome", timeout=30)
            
            if pdf_res.status_code == 200 and pdf_res.content.startswith(b'%PDF'):
                with open(dest_path, 'wb') as f:
                    f.write(pdf_res.content)
                print(f"  [OK] Guardado en: {os.path.basename(dest_path)}")
                return True
            else:
                print(f"  [Error] La descarga no contiene un PDF valido (status: {pdf_res.status_code}, bytes: {len(pdf_res.content)})")
                return False
        else:
            print("  [Info] No se encontro tag de PDF de Sci-Hub para este DOI.")
            return False
            
    except Exception as e:
        print(f"  [Error] Excepcion en la descarga: {e}")
        return False

def main():
    report_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\download_report.json"
    dest_dir = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    
    if not os.path.exists(report_path):
        print(f"No se encuentra el reporte en {report_path}")
        return
        
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
        
    pending = [item for item in report if item['status'] == 'Failed' and item['doi'] is not None]
    print(f"=== INICIANDO DESCARGA AUTOMATICA EN LOTE VIA SCI-HUB.REN ({len(pending)} PENDIENTES) ===")
    
    success_count = 0
    for idx, item in enumerate(pending):
        filename = item['filename']
        doi = item['doi']
        dest_path = os.path.join(dest_dir, filename)
        
        print(f"\n[{idx+1}/{len(pending)}] DOI: {doi} -> {filename}")
        
        if download_paper_from_ren(doi, dest_path):
            # Update item status in report list
            for r_item in report:
                if r_item['index'] == item['index']:
                    r_item['status'] = 'Success'
                    r_item['source'] = 'Sci-Hub Ren Automatic'
            success_count += 1
            # Save progress incrementally
            with open(report_path, 'w', encoding='utf-8') as f_out:
                json.dump(report, f_out, indent=4)
                
            # Sleep 3 seconds to avoid rate limiting
            time.sleep(3)
        else:
            # Sleep 1 second on failure
            time.sleep(1)
            
    print(f"\n=== PROCESO TERMINADO. DESCARGAS EXITOSAS: {success_count}/{len(pending)} ===")

if __name__ == '__main__':
    main()
