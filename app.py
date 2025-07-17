from flask import Flask, request, render_template_string, make_response
import spacy
import pandas as pd
from collections import Counter
import requests
from io import StringIO

# Initialize Flask app
app = Flask(__name__)

# Pre-load spaCy model and frequency data
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")

print("Loading frequency data...")
freq_dict = {}
try:
    # Download frequency data
    url = "https://raw.githubusercontent.com/j-hollander/annotationcode1/main/1Tfreqs.txt"
    response = requests.get(url)
    response.raise_for_status()
    
    # Process each line
    for line in StringIO(response.text):
        parts = line.split()
        if len(parts) >= 2:
            freq_dict[parts[0]] = parts[1]
    print("Frequency data loaded successfully!")
except Exception as e:
    print(f"Error loading frequency data: {str(e)}")

# Define DataFrame columns
column_names = [
    "Token", "TokenLower", "Lemma", "SourceFile", "POS", "Tag", "Dep", 
    "Shape", "Alpha", "Stop", "TokenLength", "CorpusFrequency"
]

# HTML Template (updated for feature extraction)
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Linguistic Feature Extractor</title>
    <style>
        /* ... (keep existing styles unchanged) ... */
    </style>
</head>
<body>
    <div class="container">
        <h1>Linguistic Feature Extractor</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="upload-section">
                <label class="custom-file-input">
                    Choose TXT File
                    <input type="file" name="text_file" accept=".txt" required>
                </label>
                <div class="file-name" id="file-name">No file chosen</div>
                <button type="submit">Extract Features</button>
            </div>
        </form>
        {% if message %}
            <div id="results">
                <p>{{ message }}</p>
                {% if download_url %}
                    <p>Download results: <a href="{{ download_url }}">CSV File</a></p>
                {% endif %}
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check file upload
        if 'text_file' not in request.files:
            return render_template_string(HTML_CONTENT, message="No file uploaded")
            
        file = request.files['text_file']
        if file.filename == '':
            return render_template_string(HTML_CONTENT, message="No selected file")
            
        if not file.filename.endswith('.txt'):
            return render_template_string(HTML_CONTENT, message="Invalid file type. Please upload a .txt file")

        try:
            # Read and preprocess text
            text = file.read().decode('utf-8')
            text = text.replace("\n\n", " ").replace("\n", " ")
            
            # Process text with spaCy
            doc = nlp(text)
            
            # Build token data
            data = []
            for token in doc:
                token_lower = token.text.lower()
                data.append([
                    token.text,
                    token_lower,
                    token.lemma_,
                    file.filename,
                    token.pos_,
                    token.tag_,
                    token.dep_,
                    token.shape_,
                    token.is_alpha,
                    token.is_stop,
                    len(token.text),
                    freq_dict.get(token_lower, "N/A")  # Use .get() to handle missing keys
                ])
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=column_names)
            df["TokenCumulFreq"] = df.groupby('TokenLower').cumcount() + 1
            df["LemmaCumulFreq"] = df.groupby('Lemma').cumcount() + 1
            token_freq = Counter(df["TokenLower"])
            df['WordTotN'] = df['TokenLower'].map(token_freq)
            df.index.name = 'TokenIndex'

            # Create CSV response
            csv_output = df.to_csv(index=True)
            response = make_response(csv_output)
            response.headers['Content-Disposition'] = f'attachment; filename={file.filename.replace(".txt", "_features.csv")}'
            response.headers['Content-type'] = 'text/csv'
            return response
            
        except Exception as e:
            return render_template_string(HTML_CONTENT, message=f"Processing error: {str(e)}")

    # GET request - show upload form
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
