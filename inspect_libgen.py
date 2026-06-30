from curl_cffi import requests

def main():
    url = "http://libgen.lc/scimag/?q=10.1103/PhysRevLett.88.174102"
    try:
        r = requests.get(url, impersonate="chrome", timeout=15)
        with open("libgen_lc.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Successfully saved HTML to libgen_lc.html")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
