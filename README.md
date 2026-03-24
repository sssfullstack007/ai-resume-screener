# 🤖 AI Resume Screening System

An intelligent NLP-powered web application that automatically evaluates resumes against job descriptions, ranks candidates by match score, and identifies skill gaps.

---

## 🚀 Features

- 📄 **Multi-Resume Upload** — Upload multiple resumes at once (PDF, DOCX, TXT)
- 🧠 **NLP Skill Extraction** — Uses spaCy to extract skills and keywords
- 📊 **Match Score** — TF-IDF + Cosine Similarity calculates how well each resume fits
- 🏆 **Candidate Ranking** — Automatically ranks candidates from best to weakest match
- ❌ **Missing Skill Insights** — Shows exactly what skills a candidate is lacking
- 🌐 **Flask Web Interface** — Clean, responsive UI for easy use

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| NLP | spaCy (`en_core_web_sm`) |
| ML | Scikit-learn (TF-IDF, Cosine Similarity) |
| File Parsing | PyPDF2, python-docx |
| Frontend | HTML, CSS, Bootstrap 5 |

---

## 📁 Project Structure

```
ai-resume-screener/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html          # Frontend UI
│
├── static/
│   └── css/
│       └── style.css       # Custom styles
│
└── uploads/                # Temporary file storage (auto-created)
```

---

## ⚙️ Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/ssfullstack007/ai-resume-screener.git
cd ai-resume-screener
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## 📸 How It Works

1. Paste a **Job Description** into the text area
2. Upload one or more **resumes** (PDF/DOCX/TXT)
3. Click **Analyze Resumes**
4. View ranked results with:
   - Match score (%)
   - Matching skills ✅
   - Missing skills ❌

---

## 🧠 Algorithm

```
Resume Text  ──┐
               ├──► TF-IDF Vectorizer ──► Cosine Similarity ──► Match Score %
Job Description┘

spaCy NLP ──► Skill Extraction ──► Matching / Missing Skills
```

---

## 👩‍💻 Author

**Shella Sai Srinivas**  
B.Tech – Electronics and Communication Engineering  
[LinkedIn](https://linkedin.com/in/saisrinivas-shella) | [GitHub](https://github.com/ssfullstack007)

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
