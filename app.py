from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Citation Extractor</title>
    <style>
        /* Existing CSS styles remain unchanged */
    </style>
</head>
<body>
    <div class="container">
        <h1>Extract Citations from .txt</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="text_file" accept=".txt" required>
            <button type="submit">Upload and Process</button>
        </form>
        {% if citations %}
            <div id="results">
                <table>
                    <thead>
                        <tr>
                            <th>Author(s)</th>
                            <th>Year</th>
                            <th>Page/Paragraph</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for citation in citations %}
                            <tr>
                                <td>{{ citation.authors }}</td>
                                <td>{{ citation.year }}</td>
                                <td>{{ citation.page }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% endif %}
    </div>
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
