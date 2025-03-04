from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

# HTML and CSS as a string
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Citation Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }

        .container {
            width: 50%;
            margin: 50px auto;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        h1 {
            margin-bottom: 20px;
        }

        input[type="file"] {
            margin-bottom: 20px;
        }

        button {
            padding: 10px 20px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        button:hover {
            background-color: #0056b3;
        }

        #results {
            margin-top: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
        }

        th {
            background-color: #f4f4f4;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Extract Citations from .txt</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="text_file" accept=".txt" required>
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
    pattern = re.compile(r'\(([A-Za-z’]+(?:, [A-Za-z’]+)*(?:,? & [A-Za-z’]+)?(?: et al\.)?),? (\d{4}|n\.d\.)(?:, (?:p\. \d+|para\. \d+))?\)|\b([A-Za-z’]+(?:, [A-Za-z’]+)*(?:,? & [A-Za-z’]+)?(?: et al\.)?)\s*\((\d{4}|n\.d\.)(?:, (?:p\. \d+|para\. \d+))?\)', re.IGNORECASE)
    matches = pattern.findall(text)
    for match in matches:
        # Debugging information to check the captured groups
        print(f"Match: {match}")
        if match[0] or match[3]:
            authors = match[0] if match[0] else match[3]
            year = match[1] if match[1] else match[4]
            page = match[2] if match[2] else match[5] if match[5] else ''
            citations.append({'authors': authors.strip(), 'year': year.strip(), 'page': page.strip()})
        else:
            print(f"Warning: Unexpected match format - {match}")
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
