from curl_cffi import requests
import re

def main():
    base_url = "http://libgen.lc/scimag/?q=10.1103/PhysRevLett.88.174102"
    session = requests.Session()
    
    try:
        r = session.get(base_url, impersonate="chrome", timeout=15)
        html = r.text
        
        link_match = re.search(r"href=['\"](http://libgen\.lc/scimag/[^'\"]+fp=-3)['\"]", html)
        if link_match:
            redirect_url = link_match.group(1)
            r2 = session.get(redirect_url, impersonate="chrome", timeout=15)
            html2 = r2.text
            print("Lines containing 'iframe':")
            for line in html2.splitlines():
                if 'iframe' in line.lower():
                    print(line)
        else:
            print("No redirect link found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
