from flask import Flask, render_template, request, jsonify
import os
import re
from werkzeug.utils import secure_filename
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text(file_path):
    """Extract text based on file type."""
    ext = file_path.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext == 'docx':
        return extract_text_from_docx(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()


def extract_skills(text):
    """Extract skills/keywords using spaCy NLP."""
    doc = nlp(text.lower())
    
    # Common tech skills list
    tech_skills = [
        "python", "java", "javascript", "sql", "html", "css", "react", "angular",
        "nodejs", "django", "flask", "spring", "machine learning", "deep learning",
        "nlp", "data analysis", "power bi", "tableau", "git", "docker", "kubernetes",
        "aws", "azure", "gcp", "rest api", "mongodb", "postgresql", "mysql",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spacy",
        "agile", "scrum", "linux", "c++", "c#", "php", "ruby", "swift", "kotlin",
        "excel", "communication", "teamwork", "problem solving", "leadership"
    ]
    
    found_skills = []
    text_lower = text.lower()
    for skill in tech_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    # Also extract noun phrases from spaCy
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:
            found_skills.append(chunk.text.strip())
    
    return list(set(found_skills))


def calculate_match_score(resume_text, job_description):
    """Calculate similarity score using TF-IDF and cosine similarity."""
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(score * 100, 2)
    except:
        return 0.0


def get_missing_skills(resume_skills, job_skills):
    """Find skills in job description but missing from resume."""
    resume_set = set([s.lower() for s in resume_skills])
    job_set = set([s.lower() for s in job_skills])
    return list(job_set - resume_set)


def get_matching_skills(resume_skills, job_skills):
    """Find skills present in both resume and job description."""
    resume_set = set([s.lower() for s in resume_skills])
    job_set = set([s.lower() for s in job_skills])
    return list(resume_set & job_set)


def get_candidate_rank(score):
    """Assign rank/label based on score."""
    if score >= 70:
        return "Strong Match", "success"
    elif score >= 45:
        return "Moderate Match", "warning"
    else:
        return "Weak Match", "danger"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    results = []
    job_description = request.form.get('job_description', '')

    if not job_description.strip():
        return jsonify({'error': 'Please provide a job description.'}), 400

    files = request.files.getlist('resumes')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Please upload at least one resume.'}), 400

    job_skills = extract_skills(job_description)

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            resume_text = extract_text(file_path)
            resume_skills = extract_skills(resume_text)
            score = calculate_match_score(resume_text, job_description)
            missing = get_missing_skills(resume_skills, job_skills)
            matching = get_matching_skills(resume_skills, job_skills)
            rank_label, rank_color = get_candidate_rank(score)

            results.append({
                'filename': filename,
                'score': score,
                'rank_label': rank_label,
                'rank_color': rank_color,
                'matching_skills': matching[:15],
                'missing_skills': missing[:10],
                'total_resume_skills': len(resume_skills)
            })

            # Clean up uploaded file
            os.remove(file_path)

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({'results': results, 'job_skills': job_skills[:20]})


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
