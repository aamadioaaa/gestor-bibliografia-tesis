import os
import re

def main():
    para_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\extracted_paragraphs.txt"
    with open(para_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Search for paragraph indexes containing "Bibliografía" or "Bibliografia"
    # typically at the end of the file. Let's look from the end or look for exact matches of the header.
    matches = []
    for line in lines:
        match = re.search(r'^\[(\d+)\]\s*(Bibliograf.a|Referencias|REFERENCIAS|BIBLIOGRAF.A)\s*$', line, re.IGNORECASE)
        if match:
            idx = int(match.group(1))
            matches.append((idx, line.strip()))
            
    print(f"Found headers: {matches}")
    
    # If we found any headers, let's write out paragraphs starting from that index.
    if matches:
        start_idx = matches[-1][0]  # Let's take the last one or the one that seems correct.
        print(f"Extracting bibliography from paragraph index {start_idx} to the end...")
        bib_lines = lines[start_idx:]
        bib_out = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\bibliography.txt"
        with open(bib_out, 'w', encoding='utf-8') as out_f:
            out_f.writelines(bib_lines)
        print(f"Saved bibliography to {bib_out}")
    else:
        # Search for any line containing "Bibliografía" or "Bibliografia" and print its context
        print("No exact header found. Searching for partial matches...")
        for i, line in enumerate(lines):
            if "bibliograf" in line.lower() or "referencias" in line.lower():
                print(f"Partial match: {line.strip()[:100]}")

if __name__ == '__main__':
    main()
