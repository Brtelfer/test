from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Citation Extractor</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }

        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 2.5rem;
        }

        h1 {
            color: #2c3e50;
            margin-bottom: 2rem;
            font-weight: 600;
            text-align: center;
            font-size: 2.2rem;
        }

        .upload-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
            border: 2px dashed #ced4da;
            transition: border-color 0.3s ease;
        }

        .upload-section:hover {
            border-color: #4a90e2;
        }

        .custom-file-input {
            display: inline-block;
            background: #4a90e2;
            color: white;
            padding: 0.8rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s ease;
            font-weight: 500;
        }

        .custom-file-input:hover {
            background: #357abd;
        }

        input[type="file"] {
            display: none;
        }

        button[type="submit"] {
            background: #00c853;
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.3s ease;
            margin-top: 1rem;
        }

        button[type="submit"]:hover {
            background: #009624;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        th {
            background: #4a90e2;
            color: white;
            padding: 1rem;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 1rem;
            border-bottom: 1px solid #f0f0f0;
            color: #2c3e50;
        }

        tr:hover {
            background-color: #f8f9fa;
        }

        tr:nth-child(even) {
            background-color: #f8f9fa;
        }

        #results {
            margin-top: 2rem;
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .file-name {
            margin-top: 0.5rem;
            color: #6c757d;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Academic Citation Extractor</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="upload-section">
                <label class="custom-file-input">
                    Choose TXT File
                    <input type="file" name="text_file" accept=".txt" required>
                </label>
                <div class="file-name" id="file-name">No file chosen</div>
                <button type="submit">Process Document</button>
            </div>
        </form>
        {% if citations %}
            <div id="results">
                <table>
                    <thead>
                        <tr>
                            <th>Author(s)</th>
                            <th>Year</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for citation in citations %}
                            <tr>
                                <td>{{ citation.authors }}</td>
                                <td>{{ citation.year }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% endif %}
    </div>

    <script>
        document.querySelector('input[type="file"]').addEventListener('change', function(e) {
            const fileName = document.getElementById('file-name');
            fileName.textContent = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
        });
    </script>
</body>
</html>
"""

def extract_citations(text):
    citations = []
    # Regex updated to capture page/paragraph in groups 3 and 6
    pattern = re.compile(
        r'\(([A-Za-z’]+(?:, [A-Za-z’]+)*(?:,? & [A-Za-z’]+)?(?: et al\.)?),? (\d{4}|n\.d\.)(?:, (p\. \d+|para\. \d+))?\)'  # Groups 1,2,3
        r'|'  # OR
        r'\b([A-Za-z’]+(?:, [A-Za-z’]+)*(?:,? & [A-Za-z’]+)?(?: et al\.)?)\s*\((\d{4}|n\.d\.)(?:, (p\. \d+|para\. \d+))?\)',  # Groups 4,5,6
        re.IGNORECASE
    )
    matches = pattern.findall(text)
    for match in matches:
        authors, year, page = '', '', ''
        # Check which alternative matched based on group1 (index 0) or group4 (index 3)
        if match[0]:  # First alternative (groups 1,2,3)
            authors = match[0].strip()
            year = match[1].strip()
            page = match[2].strip() if match[2] else ''
        else:  # Second alternative (groups 4,5,6)
            authors = match[3].strip()
            year = match[4].strip()
            page = match[5].strip() if match[5] else ''
        citations.append({'authors': authors, 'year': year, 'page': page})
    return citations

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    citations = []
    if request.method == 'POST':
        text_file = request.files.get('text_file')
        if text_file:
            text = text_file.read().decode('utf-8')
            citations = extract_citations(text)
    return render_template_string(HTML_CONTENT, citations=citations)

if __name__ == "__main__":
    app.run(debug=True)
