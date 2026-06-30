from curl_cffi import requests
import re
import urllib.parse

def main():
    base_url = "http://libgen.lc/scimag/?q=10.1103/PhysRevLett.88.174102"
    session = requests.Session()
    
    try:
        # Step 1: Get the redirect page
        r = session.get(base_url, impersonate="chrome", timeout=15)
        html = r.text
        
        # Extract link
        link_match = re.search(r"href=['\"](http://libgen\.lc/scimag/[^'\"]+fp=-3)['\"]", html)
        if link_match:
            redirect_url = link_match.group(1)
            print(f"Following redirect to: {redirect_url}")
            
            # Step 2: Get the results page
            r2 = session.get(redirect_url, impersonate="chrome", timeout=15)
            html2 = r2.text
            print(f"Results page loaded. Size: {len(html2)}")
            
            with open("libgen_results.html", "w", encoding="utf-8") as f:
                f.write(html2)
            print("Saved results to libgen_results.html")
        else:
            print("Could not find redirect link in HTML.")
            # Let's save the original HTML just in case
            with open("libgen_orig.html", "w", encoding="utf-8") as f:
                f.write(html)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
