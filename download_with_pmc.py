import os
import re
import urllib.request
import urllib.parse
import json
import time
import ssl

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

def get_pmcid(doi):
    query = f"doi:{doi}"
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(query)}&format=json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get('resultList', {}).get('result', [])
            if results:
                return results[0].get('pmcid')
    except Exception:
        pass
    return None

def download_pdf(url, filepath):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30, context=context) as response:
            content = response.read()
            if content.startswith(b'%PDF'):
                with open(filepath, 'wb') as f:
                    f.write(content)
                return True
            else:
                return False
    except Exception as e:
        print(f"    Error downloading {url}: {e}")
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
            
    # Load current report data
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        report_dict = {item['index']: item for item in report_data}
    else:
        report_dict = {}

    print("=== STARTING EUROPE PMC PMCID RENDER SEARCH ===")
    
    new_successes = 0
    
    for item in parsed_items:
        idx = item['index']
        filename = item['filename']
        dest_path = os.path.join(dest_dir, filename)
        
        # Check if already downloaded
        is_already_downloaded = False
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            is_already_downloaded = True
            
        if is_already_downloaded:
            # Update report status just in case
            report_dict[idx] = {
                'index': idx,
                'status': 'Success',
                'filename': filename,
                'doi': item['doi'],
                'source': report_dict.get(idx, {}).get('source', 'Direct Link')
            }
            continue
            
        # We need to try to download it
        if item['doi']:
            print(f"\n[{idx}] Searching Europe PMC for DOI: {item['doi']}...")
            pmcid = get_pmcid(item['doi'])
            if pmcid:
                print(f"  Found PMCID: {pmcid}")
                pmc_url = f"https://europepmc.org/articles/{pmcid}?pdf=render"
                print(f"  Attempting download from: {pmc_url}")
                if download_pdf(pmc_url, dest_path):
                    print("  SUCCESS!")
                    report_dict[idx] = {
                        'index': idx,
                        'status': 'Success',
                        'filename': filename,
                        'doi': item['doi'],
                        'source': 'Europe PMC PMCID Render'
                    }
                    new_successes += 1
                else:
                    print("  Failed to download PMC PDF.")
            else:
                print("  No PMCID found.")
            time.sleep(1.0)
            
    # Save the updated report
    updated_report = [report_dict[k] for k in sorted(report_dict.keys())]
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(updated_report, f, indent=4)
        
    print("\n" + "=" * 40)
    print(f"Render Search Complete. New files downloaded: {new_successes}")
    print("=" * 40)

if __name__ == '__main__':
    main()
