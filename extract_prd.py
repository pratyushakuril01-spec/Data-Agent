import zipfile
import xml.etree.ElementTree as ET
import os

docx_path = r"C:\Users\lenovo\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\E0E3C0D902E8029BC73F5007C44B386CFBF89D19\transfers\2026-36\GAATA_Prompt_Templates_for_ChatGPT.docx"
output_path = r"c:\Users\lenovo\Desktop\Ghost Audit Agent\PRD.md"

with zipfile.ZipFile(docx_path, 'r') as z:
    xml_content = z.read('word/document.xml')

root = ET.fromstring(xml_content)

# Namespace for Word
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

paragraphs = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    texts = [t.text for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
    if texts:
        paragraphs.append("".join(texts))

content = "\n\n".join(paragraphs)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully extracted {len(paragraphs)} paragraphs to {output_path}")
