import json
import os

def main():
    report_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\download_report.json"
    
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Update item 40 (which is 0-indexed index 39 in array or matches "index": 40)
        updated = False
        for item in data:
            if item['index'] == 40:
                item['status'] = 'Success'
                item['source'] = 'Direct Link (SSL bypassed)'
                item['filename'] = '40_U_2024_510k_review_memorandum_K233537_Labeling.pdf'
                updated = True
                break
                
        if updated:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print("Successfully updated download_report.json with Item 40 status!")
        else:
            print("Item 40 not found in report.")
    else:
        print("Report file not found.")

if __name__ == '__main__':
    main()
