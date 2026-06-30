import zipfile
import xml.etree.ElementTree as ET
import os
import sys

def docx_to_text(docx_path):
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text_content = []
    
    with zipfile.ZipFile(docx_path) as docx:
        xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            p_text = []
            for run in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                for text in run.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    if text.text:
                        p_text.append(text.text)
            text_content.append("".join(p_text))
            
    return text_content

if __name__ == '__main__':
    docx_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\03.Capítulo 3 - Analisis de los datos_Walter_Dino_rev.docx"
    paragraphs = docx_to_text(docx_path)
    print(f"Total paragraphs: {len(paragraphs)}")
    
    # Save all paragraphs to a text file for easy inspection
    out_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\extracted_paragraphs.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        for i, p in enumerate(paragraphs):
            f.write(f"[{i}] {p}\n")
    print(f"Saved all paragraphs to {out_path}")
