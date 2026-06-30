import os
import urllib.request
import ssl
import json

def download_file_ssl_disabled(url, filepath):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Create SSL context that ignores verification errors
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
        print(f"  Error downloading {url}: {e}")
        return False

def main():
    dest_dir = r"C:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    
    # Let's retry item 40 (FDA 510(k) review memorandum)
    url_40 = "https://www.accessdata.fda.gov/cdrh_docs/pdf23/K233537.pdf"
    path_40 = os.path.join(dest_dir, "40_U_2024_510k_review_memorandum_K233537_Labeling.pdf")
    
    print("Retrying item 40 with SSL verification disabled...")
    if download_file_ssl_disabled(url_40, path_40):
        print("Success for Item 40!")
    else:
        print("Failed for Item 40.")

if __name__ == '__main__':
    main()
