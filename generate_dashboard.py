import json
import os
import re
import urllib.parse

def parse_line(line):
    line = line.strip()
    if not line:
        return None
        
    index_match = re.match(r'^\[\d+\]\s*(\d+)\.\s*(.*)', line)
    if not index_match:
        return None
        
    index = int(index_match.group(1))
    content = index_match.group(2)
    
    year_match = re.search(r'\((19\d{2}|20\d{2}|n\.d\.-?[a-z]?)(?:,\s*[A-Za-z]+\s*\d*)?\)', content)
    if year_match:
        year = year_match.group(1)
        authors_part = content[:year_match.start()].strip()
        rest = content[year_match.end():].strip()
    else:
        year = "unknown"
        authors_part = "unknown"
        rest = content
        
    # Extract clean authors
    authors = authors_part
    if authors.endswith('.'):
        authors = authors[:-1]
        
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
        
    if index == 10 and "pdfhttps://" in line:
        url = "https://www.adces.org/docs/default-source/dana-files/adc-23842v3-revised-august-3-2020cd070ee4-83cd-472c-a990-892684a26df3.pdf"
        
    if url and 'doi.org/' in url:
        extracted_doi = url.split('doi.org/')[-1].strip().rstrip('.,;)')
        if extracted_doi:
            doi = extracted_doi
            
    # Title extraction
    parts = [p.strip() for p in rest.split('.') if p.strip()]
    title = "Title"
    for part in parts:
        if part.startswith('http') or 'doi.org' in part or len(part) < 5:
            continue
        title = part
        break
        
    # Full citation text
    citation = content
    
    return {
        'index': index,
        'authors': authors,
        'year': year,
        'title': title,
        'doi': doi,
        'url': url,
        'citation': citation
    }

def main():
    biblio_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\bibliography.txt"
    report_path = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Codigo\download_report.json"
    dest_dir = r"C:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio"
    
    if not os.path.exists(biblio_path) or not os.path.exists(report_path):
        print("Required files not found!")
        return

    with open(biblio_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
        
    report_dict = {item['index']: item for item in report_data}
    
    parsed_items = []
    success_count = 0
    failed_count = 0
    
    for line in lines:
        item = parse_line(line)
        if item:
            idx = item['index']
            rep = report_dict.get(idx, {'status': 'Failed', 'filename': '', 'source': 'None'})
            
            # double check if file actually exists on disk in C:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_2\Biblio
            status = rep['status']
            filename = rep['filename']
            filepath = os.path.join(dest_dir, filename) if filename else ""
            
            if 'Success' in status and filename and os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                status = 'Success'
                success_count += 1
            else:
                status = 'Failed'
                failed_count += 1
                
            item['status'] = status
            item['filename'] = filename
            item['source'] = rep.get('source', 'None')
            parsed_items.append(item)
            
    print(f"Stats - Success: {success_count}, Failed: {failed_count}, Total: {len(parsed_items)}")
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestor de Bibliografía - Tesis Doctoral</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(20, 28, 48, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary: #4f46e5;
            --primary-hover: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --glass-blur: blur(16px);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(79, 70, 229, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.1) 0%, transparent 40%);
            background-attachment: fixed;
            min-height: 100vh;
            padding: 3rem 1.5rem;
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.8s ease;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 1.1rem;
            font-weight: 300;
        }}

        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
            animation: fadeInUp 0.8s ease;
        }}

        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: var(--glass-blur);
            border-radius: 1.25rem;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 30px rgba(79, 70, 229, 0.15);
        }}

        .stat-val {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }}

        .stat-val.success-text {{ color: var(--success); }}
        .stat-val.warning-text {{ color: var(--warning); }}
        .stat-val.primary-text {{ color: #a5b4fc; }}

        .stat-lbl {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Filters and Search */
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease;
        }}

        .search-container {{
            flex-grow: 1;
            max-width: 500px;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.85rem 1.25rem;
            border-radius: 50px;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.3s ease;
        }}

        .search-input:focus {{
            border-color: var(--primary-hover);
            box-shadow: 0 0 15px rgba(79, 70, 229, 0.2);
            background: rgba(20, 28, 48, 0.8);
        }}

        .filter-buttons {{
            display: flex;
            gap: 0.5rem;
        }}

        .btn-filter {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }}

        .btn-filter:hover, .btn-filter.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        /* Reference List */
        .reference-list {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            animation: fadeInUp 1s ease;
        }}

        .ref-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: var(--glass-blur);
            border-radius: 1.25rem;
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .ref-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: transparent;
            transition: all 0.3s ease;
        }}

        .ref-card.success-card::before {{ background: var(--success); }}
        .ref-card.failed-card::before {{ background: var(--warning); }}

        .ref-card:hover {{
            transform: scale(1.01);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 255, 255, 0.15);
        }}

        .ref-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 0.75rem;
        }}

        .ref-meta {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .index-badge {{
            background: rgba(255, 255, 255, 0.08);
            color: #a5b4fc;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
        }}

        .ref-author {{
            font-weight: 600;
            font-size: 0.95rem;
        }}

        .ref-year {{
            color: var(--text-muted);
            font-size: 0.95rem;
        }}

        .status-badge {{
            padding: 0.35rem 0.8rem;
            border-radius: 50px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .status-badge.success-badge {{
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .status-badge.failed-badge {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .ref-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 600;
            line-height: 1.4;
            color: #ffffff;
        }}

        .ref-citation {{
            color: var(--text-muted);
            font-size: 0.88rem;
            line-height: 1.5;
            background: rgba(0, 0, 0, 0.15);
            padding: 0.85rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }}

        /* Buttons and Actions */
        .ref-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 0.5rem;
        }}

        .btn-action {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.6rem 1.2rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
            outline: none;
        }}

        .btn-action.btn-open {{
            background: var(--success);
            color: white;
            border: none;
        }}

        .btn-action.btn-open:hover {{
            background: #059669;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
        }}

        .btn-action.btn-scihub {{
            background: #9a3412;
            color: white;
            border: none;
        }}

        .btn-action.btn-scihub:hover {{
            background: #c2410c;
            box-shadow: 0 0 10px rgba(194, 65, 12, 0.4);
        }}

        .btn-action.btn-copy {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border: 1px solid var(--border-color);
        }}

        .btn-action.btn-copy:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}

        .btn-action.btn-link {{
            background: var(--primary);
            color: white;
            border: none;
        }}

        .btn-action.btn-link:hover {{
            background: var(--primary-hover);
            box-shadow: 0 0 10px rgba(79, 70, 229, 0.4);
        }}

        /* Mirror Select styles */
        .mirror-select-container {{
            position: relative;
            display: inline-flex;
        }}

        .select-mirror {{
            background: #374151;
            color: white;
            border: none;
            padding: 0.6rem;
            border-radius: 0 0.5rem 0.5rem 0;
            font-size: 0.85rem;
            cursor: pointer;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #1f2937;
            color: #10b981;
            border: 1px solid #10b981;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
            z-index: 1000;
            transform: translateY(150%);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}

        .toast.show {{
            transform: translateY(0);
        }}

        /* Animations */
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @media (max-width: 640px) {{
            body {{ padding: 1.5rem 1rem; }}
            h1 {{ font-size: 2.2rem; }}
            .controls {{ flex-direction: column; align-items: stretch; }}
            .filter-buttons {{ width: 100%; justify-content: space-between; }}
            .btn-filter {{ flex-grow: 1; text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Gestor de Bibliografía</h1>
            <p class="subtitle">Capítulo 3 - Análisis de Datos | Tesis Doctoral</p>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val primary-text">{len(parsed_items)}</div>
                <div class="stat-lbl">Total Artículos</div>
            </div>
            <div class="stat-card">
                <div class="stat-val success-text">{success_count}</div>
                <div class="stat-lbl">Descargados (PDF)</div>
            </div>
            <div class="stat-card">
                <div class="stat-val warning-text">{failed_count}</div>
                <div class="stat-lbl">Pendientes</div>
            </div>
            <div class="stat-card">
                <div class="stat-val" style="color: #60a5fa;">{int(success_count/len(parsed_items)*100)}%</div>
                <div class="stat-lbl">Completado</div>
            </div>
        </div>

        <div class="controls">
            <div class="search-container">
                <input type="text" id="searchInput" class="search-input" placeholder="Buscar por autor, título, año...">
            </div>
            <div class="filter-buttons">
                <button class="btn-filter active" onclick="filterStatus('all')">Todos</button>
                <button class="btn-filter" onclick="filterStatus('success')">Descargados</button>
                <button class="btn-filter" onclick="filterStatus('failed')">Pendientes</button>
            </div>
        </div>

        <div class="reference-list" id="referenceList">
"""
    
    # Loop over parsed items and create HTML cards
    for item in parsed_items:
        idx = item['index']
        is_success = item['status'] == 'Success'
        card_class = "success-card" if is_success else "failed-card"
        badge_class = "success-badge" if is_success else "failed-badge"
        badge_text = "✓ Descargado" if is_success else "⚠ Pendiente"
        
        # Determine button actions
        actions_html = ""
        if is_success:
            # File URL to open locally
            pdf_url = f"file:///{dest_dir.replace(chr(92), '/')}/{item['filename']}"
            actions_html += f'<a href="{pdf_url}" class="btn-action btn-open" target="_blank">Abrir PDF</a>'
        else:
            if item['doi']:
                # Sci-Hub mirrors
                doi_esc = urllib.parse.quote(item['doi'])
                actions_html += f"""
                <div class="mirror-select-container">
                    <a href="https://sci-hub.ren/{item['doi']}" class="btn-action btn-scihub" id="scihub_link_{idx}" target="_blank" style="border-radius: 0.5rem 0 0 0.5rem;">Descargar Sci-Hub</a>
                    <select class="select-mirror" onchange="changeMirror({idx}, '{item['doi']}', this)">
                        <option value="https://sci-hub.ren/">.ren</option>
                        <option value="https://sci-hub.se/">.se</option>
                        <option value="https://sci-hub.st/">.st</option>
                        <option value="https://sci-hub.ru/">.ru</option>
                    </select>
                </div>
                """
                actions_html += f'<button class="btn-action btn-copy" onclick="copyToClipboard(\'{item["doi"]}\', \'DOI copiado!\')">Copiar DOI</button>'
            elif item['url']:
                actions_html += f'<a href="{item["url"]}" class="btn-action btn-link" target="_blank">Abrir Enlace Original</a>'
            else:
                # No DOI, no URL (Books, proceedings)
                title_esc = urllib.parse.quote(f"{item['authors']} {item['title']}")
                actions_html += f'<a href="https://scholar.google.com/scholar?q={title_esc}" class="btn-action btn-link" target="_blank">Buscar en Scholar</a>'
                actions_html += f'<button class="btn-action btn-copy" onclick="copyToClipboard(\'{item["title"].replace(chr(39), chr(92)+chr(39))}\', \'Título copiado!\')">Copiar Título</button>'

        html_content += f"""
            <div class="ref-card {card_class}" data-status="{item['status'].lower()}" data-search="{item['authors'].lower()} {item['title'].lower()} {str(item['year']).lower()}">
                <div class="ref-header">
                    <div class="ref-meta">
                        <span class="index-badge">#{idx}</span>
                        <span class="ref-author">{item['authors']}</span>
                        <span class="ref-year">({item['year']})</span>
                    </div>
                    <span class="status-badge {badge_class}">{badge_text}</span>
                </div>
                <div class="ref-title">{item['title']}</div>
                <div class="ref-citation">{item['citation']}</div>
                <div class="ref-actions">
                    {actions_html}
                </div>
            </div>
"""

    html_content += """
        </div>
    </div>

    <div class="toast" id="toast">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <span id="toastMessage">Mensaje</span>
    </div>

    <script>
        function copyToClipboard(text, message) {
            navigator.clipboard.writeText(text).then(function() {
                showToast(message);
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        }

        function showToast(message) {
            var toast = document.getElementById("toast");
            var toastMessage = document.getElementById("toastMessage");
            toastMessage.textContent = message;
            toast.classList.add("show");
            setTimeout(function() {
                toast.classList.remove("show");
            }, 3000);
        }

        function changeMirror(idx, doi, selectElem) {
            var mirrorBase = selectElem.value;
            var linkElem = document.getElementById("scihub_link_" + idx);
            linkElem.href = mirrorBase + doi;
        }

        // Live Search
        document.getElementById('searchInput').addEventListener('input', function(e) {
            var term = e.target.value.toLowerCase().trim();
            var cards = document.querySelectorAll('.ref-card');
            
            cards.forEach(function(card) {
                var searchData = card.getAttribute('data-search');
                if (searchData.includes(term)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });

        // Filter buttons
        var currentFilter = 'all';
        function filterStatus(status) {
            currentFilter = status;
            
            // Update active state of buttons
            var buttons = document.querySelectorAll('.btn-filter');
            buttons.forEach(function(btn) {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');

            var cards = document.querySelectorAll('.ref-card');
            cards.forEach(function(card) {
                var cardStatus = card.getAttribute('data-status');
                if (status === 'all' || cardStatus === status) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // clear search input
            document.getElementById('searchInput').value = '';
        }
    </script>
</body>
</html>
"""

    dashboard_out1 = os.path.join(dest_dir, "Biblio_Dashboard.html")
    dashboard_out2 = r"c:\Users\aru_a\OneDrive\1.Doctorado\9.Tesis\Capítulo_3\Biblio_Dashboard.html"
    
    with open(dashboard_out1, 'w', encoding='utf-8') as f:
        f.write(html_content)
    with open(dashboard_out2, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated HTML dashboards at:\n1. {dashboard_out1}\n2. {dashboard_out2}")

if __name__ == '__main__':
    main()
