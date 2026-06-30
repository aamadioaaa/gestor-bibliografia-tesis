from curl_cffi import requests
import re
import urllib.parse

def main():
    base_url = "http://libgen.lc/scimag/?q=10.1103/PhysRevLett.88.174102"
    session = requests.Session()
    
    try:
        r = session.get(base_url, impersonate="chrome", timeout=15)
        html = r.text
        
        link_match = re.search(r"href=['\"](http://libgen\.lc/scimag/[^'\"]+fp=-3)['\"]", html)
        if link_match:
            redirect_url = link_match.group(1)
            print(f"Redirect URL: {redirect_url}")
            
            r2 = session.get(redirect_url, impersonate="chrome", timeout=15)
            html2 = r2.text
            print(f"Results size: {len(html2)}")
            
            # Find all links
            links = re.findall(r'href=["\'](https?://[^"\']+(?:/scimag/|ads\.php\?doi=)[^"\']+)["\']', html2)
            print("Found links:")
            for link in set(links):
                print(f"  - {link}")
        else:
            print("No redirect link found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
