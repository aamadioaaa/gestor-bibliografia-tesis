import os
import re
import urllib.request
import urllib.parse
import urllib.error
import json
import time

def parse_line(line):
    line = line.strip()
    if not line:
        return None
        
    # Match [line_num] index.
    index_match = re.match(r'^\[\d+\]\s*(\d+)\.\s*(.*)', line)
    if not index_match:
        return None
        
    index = int(index_match.group(1))
    content = index_match.group(2)
    
    # Try to find year
    year_match = re.search(r'\((19\d{2}|20\d{2}|n\.d\.-?[a-z]?)(?:,\s*[A-Za-z]+\s*\d*)?\)', content)
    if year_match:
        year = year_match.group(1)
        authors_part = content[:year_match.start()].strip()
        rest = content[year_match.end():].strip()
    else:
        year = "unknown"
        authors_part = "unknown"
        rest = content
        
    # Extract clean author name (first author's last name)
    author_name = "Author"
    if authors_part and authors_part != "unknown":
        first_author = authors_part.split('.')[0].strip()
        first_author = first_author.split(',')[0].strip()
        author_name = re.sub(r'[^a-zA-Z0-9]', '', first_author)
        if not author_name:
            author_name = "Author"
            
    # Extract DOI
    doi_match = re.search(r'10\.\d{4,9}/[^\s]+', rest)
    doi = None
    if doi_match:
        doi = doi_match.group(0).rstrip('.,;)')
        
    # Extract URL
    url_match = re.search(r'https?://[^\s]+', rest)
    url = None
    if url_match:
        url = url_match.group(0).rstrip('.,;)')
        
    # Handle broken URL in reference 10
    if index == 10 and "pdfhttps://" in line:
        url = "https://www.adces.org/docs/default-source/dana-files/adc-23842v3-revised-august-3-2020cd070ee4-83cd-472c-a990-892684a26df3.pdf"
        
    if url and 'doi.org/' in url:
        extracted_doi = url.split('doi.org/')[-1].strip().rstrip('.,;)')
        if extracted_doi:
            doi = extracted_doi
            
    # Try to extract title: it starts after the year and ends before the journal (or first period)
    parts = [p.strip() for p in rest.split('.') if p.strip()]
    title = "Title"
    for part in parts:
        if part.startswith('http') or 'doi.org' in part or len(part) < 5:
            continue
        title = part
        break
        
    # Clean up title for filename
    title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    title_clean = "_".join(title_clean.split()[:5])  # limit to 5 words
    
    filename = f"{index:02d}_{author_name}_{year}_{title_clean}.pdf"
    filename = re.sub(r'[\\/*?:"<>|]', '', filename) # strip invalid chars
    
    return {
        'index': index,
        'author': author_name,
        'year': year,
        'title': title,
        'doi': doi,
        'url': url,
        'filename': filename,
        'raw': line
    }

def download_file(url, filepath):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            # Check content type if possible
            info = response.info()
            content_type = info.get_content_type()
            # If it's HTML, it might be an error page or a captcha page
            if 'html' in content_type:
                # Let's inspect a bit of it
                content = response.read(1000)
                if b'robot' in content.lower() or b'captcha' in content.lower():
                    print("  Blocked by captcha/verification.")
                    return False
                print(f"  Warning: Content-Type is HTML, not PDF. URL: {url}")
                return False
                
            # Download PDF
            with open(filepath, 'wb') as f:
                f.write(response.read())
            return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

def try_unpaywall(doi):
    email = "aru_a.doctorado@gmail.com"
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('is_oa', False):
                best_loc = data.get('best_oa_location')
                if best_loc:
                    pdf_url = best_loc.get('url_for_pdf')
                    if pdf_url:
                        return pdf_url
    except Exception as e:
        pass
    return None

def try_europepmc(doi):
    query = f"doi:{doi}"
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(query)}&format=json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get('resultList', {}).get('result', [])
            if results:
                pmcid = results[0].get('pmcid')
                if pmcid:
                    return f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/pdf"
    except Exception as e:
        pass
    return None

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

def try_scihub(doi):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
    }
    mirrors = [
        'https://sci-hub.ru/',
        'https://sci-hub.st/',
        'https://sci-hub.se/'
    ]
    for mirror in mirrors:
        url = mirror + doi
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                if 'robot' in html.lower() or 'captcha' in html.lower() or 'verificación' in html.lower():
                    continue  # Blocked by captcha on this mirror
                    
                pdf_url = extract_scihub_pdf_url(html, mirror)
                if pdf_url:
                    return pdf_url
        except Exception as e:
            pass
    return None

def main():
    biblio_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\bibliography.txt"
    dest_dir = r"C:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created destination directory: {dest_dir}")
    else:
        print(f"Destination directory already exists: {dest_dir}")
        
    with open(biblio_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    parsed_items = []
    for line in lines:
        item = parse_line(line)
        if item:
            parsed_items.append(item)
            
    print(f"Successfully parsed {len(parsed_items)} bibliography entries.")
    
    results = []
    
    for item in parsed_items:
        idx = item['index']
        filename = item['filename']
        dest_path = os.path.join(dest_dir, filename)
        
        print(f"\n[{idx}/43] Processing: {item['author']} ({item['year']}) - {item['title'][:60]}...")
        
        # Check if already exists
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            print(f"  Already exists: {filename}")
            results.append({
                'index': idx,
                'status': 'Success (Already Existed)',
                'filename': filename,
                'doi': item['doi'],
                'source': 'Local Cache'
            })
            continue
            
        success = False
        source_used = ""
        
        # Method 1: Direct PDF download
        if item['url'] and item['url'].lower().endswith('.pdf'):
            print(f"  Attempting direct PDF download from: {item['url']}")
            if download_file(item['url'], dest_path):
                success = True
                source_used = "Direct Link"
                print("  Success!")
                
        # Method 2: Unpaywall (Open Access DOI)
        if not success and item['doi']:
            print("  Attempting Unpaywall API...")
            pdf_url = try_unpaywall(item['doi'])
            if pdf_url:
                print(f"  Unpaywall found OA PDF: {pdf_url}")
                if download_file(pdf_url, dest_path):
                    success = True
                    source_used = "Unpaywall (Open Access)"
                    print("  Success!")
                    
        # Method 3: Europe PMC
        if not success and item['doi']:
            print("  Attempting Europe PMC API...")
            pdf_url = try_europepmc(item['doi'])
            if pdf_url:
                print(f"  Europe PMC found PDF: {pdf_url}")
                if download_file(pdf_url, dest_path):
                    success = True
                    source_used = "Europe PMC"
                    print("  Success!")
                    
        # Method 4: Sci-Hub
        if not success and item['doi']:
            print("  Attempting Sci-Hub mirrors...")
            pdf_url = try_scihub(item['doi'])
            if pdf_url:
                print(f"  Sci-Hub mirror found PDF: {pdf_url}")
                if download_file(pdf_url, dest_path):
                    success = True
                    source_used = "Sci-Hub"
                    print("  Success!")
                    
        if success:
            results.append({
                'index': idx,
                'status': 'Success',
                'filename': filename,
                'doi': item['doi'],
                'source': source_used
            })
        else:
            print("  Failed to download automatically.")
            results.append({
                'index': idx,
                'status': 'Failed',
                'filename': filename,
                'doi': item['doi'],
                'source': 'None'
            })
            
        # Polite sleep to avoid hitting APIs too hard
        time.sleep(1.5)
        
    # Write execution report
    report_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\download_report.json"
    with open(report_path, 'w', encoding='utf-8') as rf:
        json.dump(results, rf, indent=4)
        
    print("\n" + "=" * 40)
    print("DOWNLOAD TASK COMPLETE")
    success_count = sum(1 for r in results if 'Success' in r['status'])
    print(f"Success: {success_count} / {len(results)}")
    print(f"Report saved to: {report_path}")
    print("=" * 40)

if __name__ == '__main__':
    main()
