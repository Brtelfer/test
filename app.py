from flask import Flask, request, render_template_string, make_response, jsonify
import spacy
import pandas as pd
from collections import Counter
import requests
from io import StringIO
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Initialize Flask app
app = Flask(__name__)

# Pre-load spaCy model and frequency data
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")

print("Loading frequency data...")
freq_dict = {}
try:
    url = "https://raw.githubusercontent.com/j-hollander/annotationcode1/main/1Tfreqs.txt"
    response = requests.get(url)
    response.raise_for_status()
    
    for line in StringIO(response.text):
        parts = line.split()
        if len(parts) >= 2:
            freq_dict[parts[0]] = float(parts[1])  # Convert to float
    print("Frequency data loaded successfully!")
except Exception as e:
    print(f"Error loading frequency data: {str(e)}")

# Define DataFrame columns
column_names = [
    "Token", "TokenLower", "Lemma", "SourceFile", "POS", "Tag", "Dep", 
    "Shape", "Alpha", "Stop", "TokenLength", "CorpusFrequency"
]

# HTML Template with visualizations
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Vocabulary Analysis Tool</title>
    <style>
        /* ... (keep existing styles unchanged) ... */
        
        .analysis-section {
            margin-top: 2rem;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .chart-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 1rem;
        }
        
        .chart-box {
            flex: 1;
            min-width: 300px;
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            text-align: center;
            margin-bottom: 1rem;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .chart-img {
            width: 100%;
            height: auto;
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        
        .toggle-btn {
            background: #4a90e2;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vocabulary Analysis Tool</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="upload-section">
                <label class="custom-file-input">
                    Choose TXT File
                    <input type="file" name="text_file" accept=".txt" required>
                </label>
                <div class="file-name" id="file-name">No file chosen</div>
                <button type="submit">Analyze Vocabulary</button>
            </div>
        </form>
        
        {% if analysis_results %}
            <div class="analysis-section">
                <h2>Analysis Results: {{ filename }}</h2>
                
                <div class="chart-container">
                    <div class="chart-box">
                        <h3 class="chart-title">Novel Vocabulary Terms</h3>
                        <img src="data:image/png;base64,{{ analysis_results.novel_chart }}" class="chart-img" alt="Novel Vocabulary">
                        <p>Terms with low corpus frequency that may be unfamiliar to students</p>
                    </div>
                    
                    <div class="chart-box">
                        <h3 class="chart-title">Important Topic Terms</h3>
                        <img src="data:image/png;base64,{{ analysis_results.important_chart }}" class="chart-img" alt="Important Vocabulary">
                        <p>Key terms that appear frequently in this text</p>
                    </div>
                </div>
                
                <button class="toggle-btn" onclick="toggleTable('novelTable')">
                    Show/Hide Novel Vocabulary Details
                </button>
                <div id="novelTable" style="display:none;">
                    <div class="table-container">
                        {{ analysis_results.novel_table | safe }}
                    </div>
                </div>
                
                <button class="toggle-btn" onclick="toggleTable('importantTable')">
                    Show/Hide Important Terms Details
                </button>
                <div id="importantTable" style="display:none;">
                    <div class="table-container">
                        {{ analysis_results.important_table | safe }}
                    </div>
                </div>
                
                <p style="margin-top: 1.5rem;">
                    <a href="{{ analysis_results.download_link }}" class="custom-file-input">
                        Download Full Analysis CSV
                    </a>
                </p>
            </div>
        {% endif %}
    </div>

    <script>
        document.querySelector('input[type="file"]').addEventListener('change', function(e) {
            const fileName = document.getElementById('file-name');
            fileName.textContent = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
        });
        
        function toggleTable(tableId) {
            const table = document.getElementById(tableId);
            table.style.display = table.style.display === 'none' ? 'block' : 'none';
        }
    </script>
</body>
</html>
"""

def generate_vocabulary_chart(data, title, color, is_novel=True):
    """Generate matplotlib chart for vocabulary analysis"""
    plt.figure(figsize=(10, 6))
    
    if is_novel:
        # Sort by corpus frequency (lowest first)
        data = data.sort_values('CorpusFrequency', ascending=True).head(15)
        y = data['TokenLower']
        x = data['CorpusFrequency']
        xlabel = 'Frequency in Billion-Word Corpus (log scale)'
        log_scale = True
    else:
        # Sort by document frequency (highest first)
        data = data.sort_values('DocumentFrequency', ascending=False).head(15)
        y = data['TokenLower']
        x = data['DocumentFrequency']
        xlabel = 'Frequency in This Document'
        log_scale = False
    
    # Create horizontal bar chart
    bars = plt.barh(y, x, color=color)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.tight_layout()
    
    if log_scale:
        plt.xscale('log')
    
    # Add value labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, 
                 f' {width:.2f}' if is_novel else f' {int(width)}', 
                 ha='left', va='center')
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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
                    freq_dict.get(token_lower, 0)  # Default to 0 if not found
                ])
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=column_names)
            df["TokenCumulFreq"] = df.groupby('TokenLower').cumcount() + 1
            df["LemmaCumulFreq"] = df.groupby('Lemma').cumcount() + 1
            token_freq = Counter(df["TokenLower"])
            df['WordTotN'] = df['TokenLower'].map(token_freq)
            df.index.name = 'TokenIndex'

            # Vocabulary analysis
            # Filter out stopwords, punctuation, and short tokens
            vocab_df = df[(df['Stop'] == False) & 
                         (df['Alpha'] == True) & 
                         (df['TokenLength'] > 2)].copy()
            
            # Group by token
            grouped = vocab_df.groupby('TokenLower').agg(
                DocumentFrequency=('TokenLower', 'size'),
                CorpusFrequency=('CorpusFrequency', 'first')
            ).reset_index()
            
            # Novel vocabulary: low corpus frequency
            novel_df = grouped[grouped['CorpusFrequency'] < 100].sort_values('CorpusFrequency').head(25)
            novel_df['FrequencyPerMillion'] = novel_df['CorpusFrequency'] * 1000
            novel_table = novel_df[['TokenLower', 'DocumentFrequency', 'FrequencyPerMillion']]\
                .rename(columns={
                    'TokenLower': 'Vocabulary Term',
                    'DocumentFrequency': 'In This Text',
                    'FrequencyPerMillion': 'Per Million Words (Corpus)'
                })\
                .to_html(classes='table', index=False, float_format='%.2f')
            
            # Important vocabulary: high document frequency
            important_df = grouped.sort_values('DocumentFrequency', ascending=False).head(25)
            important_table = important_df[['TokenLower', 'DocumentFrequency', 'CorpusFrequency']]\
                .rename(columns={
                    'TokenLower': 'Vocabulary Term',
                    'DocumentFrequency': 'In This Text',
                    'CorpusFrequency': 'Corpus Frequency'
                })\
                .to_html(classes='table', index=False, float_format='%.2f')
            
            # Generate visualizations
            novel_chart = generate_vocabulary_chart(
                novel_df, 
                '15 Most Novel Vocabulary Terms', 
                'salmon',
                is_novel=True
            )
            
            important_chart = generate_vocabulary_chart(
                important_df, 
                '15 Most Important Topic Terms', 
                'lightgreen',
                is_novel=False
            )
            
            # Prepare CSV download
            csv_output = df.to_csv(index=True)
            b64_csv = base64.b64encode(csv_output.encode('utf-8')).decode('utf-8')
            download_link = f'data:text/csv;base64,{b64_csv}'
            
            return render_template_string(HTML_CONTENT,
                analysis_results={
                    'novel_chart': novel_chart,
                    'important_chart': important_chart,
                    'novel_table': novel_table,
                    'important_table': important_table,
                    'download_link': download_link
                },
                filename=file.filename
            )
            
        except Exception as e:
            return render_template_string(HTML_CONTENT, message=f"Processing error: {str(e)}")

    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
