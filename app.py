from flask import Flask, render_template, request, redirect, url_for, send_file
import re
import csv
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'


def extract_chapter_headers(text):
    headers = []
    chapter_header_patterns = [
        r'CHAPTER\s+\w+\s*(?:\n\n|\n\s*)([^\n]+)',
    ]
    for pattern in chapter_header_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            header = match.group(0).strip()
            title = match.group(1).strip() if match.group(1) else ""
            headers.append((header, title))
    return headers


def save_chapter_headers_to_csv(headers, filename='chapter_headers.csv'):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Chapter', 'Title'])
        for chapter, title in headers:
            writer.writerow([chapter, title])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            with open(filepath, 'r') as f:
                text = f.read()

            headers = extract_chapter_headers(text)
            save_chapter_headers_to_csv(headers)

            return redirect(url_for('download_file'))

    return render_template('index.html')


@app.route('/download')
def download_file():
    path = "chapter_headers.csv"
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)