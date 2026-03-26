# 🤖 AI Resume Screening System

An NLP-powered web application that evaluates resumes against a job description, ranks candidates by match score, and surfaces skill gaps — helping recruiters shortlist faster.

---

## 🚀 Features

| Feature | Detail |
|---|---|
| 📄 Multi-resume upload | PDF, DOCX, TXT supported |
| 🧠 Skill extraction | 300+ canonical skills with alias normalisation (`"ml"` = `"machine learning"`) |
| 📊 Composite match score | 60% TF-IDF similarity + 40% skill overlap, rescaled for realistic output |
| 🏆 Candidate ranking | Sorted by score: Strong / Moderate / Weak match |
| ❌ Skill gap analysis | Exact list of job-required skills missing from each resume |
| 📅 Experience detection | Extracts years of experience from resume text |
| 🛡️ Fault-tolerant | Per-file error isolation — one bad upload doesn't lose all results |
| 💡 AI improvement tips | Optional `/ai-tips` endpoint powered by Claude for per-candidate feedback |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask |
| NLP | spaCy `en_core_web_sm` |
| ML | scikit-learn (TF-IDF, cosine similarity) |
| File parsing | PyPDF2, python-docx |
| AI tips (optional) | Anthropic Python SDK |
| Frontend | HTML, CSS, Bootstrap 5 |

---

## 📁 Project Structure

```
ai-resume-screener/
│
├── app.py                  # Flask app — routes, scoring, skill extraction
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html          # Frontend UI
│
├── static/
│   └── css/
│       └── style.css       # Custom styles
│
└── uploads/                # Temp file storage (auto-created on startup)
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

### 3. (Optional) Enable AI tips
```bash
export ANTHROPIC_API_KEY=your_key_here
```
Without this, the rest of the app works fine — only the `/ai-tips` endpoint requires it.

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
```
http://127.0.0.1:5000
```

---

## 📸 How It Works

1. Paste a **job description** into the text area
2. Upload one or more resumes (PDF / DOCX / TXT)
3. Click **Analyze Resumes**
4. View ranked candidates with:
   - Composite match score (%)
   - Score breakdown (TF-IDF vs skill overlap)
   - Matching skills ✅
   - Missing skills ❌
   - Years of experience detected

---

## 🧠 Scoring Algorithm

```
Resume text    ──┐
                 ├──► TF-IDF vectorizer ──► cosine similarity ──► rescaled (÷0.45) ──┐
Job description ─┘                                                                     │
                                                                                       ├──► composite score (0–100)
Skill alias map ──► canonical skill sets ──► overlap % ────────────────────────────────┘
                                                60% weight                40% weight

Thresholds:  ≥ 65 → Strong Match   40–64 → Moderate Match   < 40 → Weak Match
```

**Why rescale TF-IDF?**  
Raw cosine similarity between two short documents rarely exceeds 0.45, even for near-perfect matches. Dividing by 0.45 before converting to a percentage makes the score use the full 0–100 range meaningfully.

**Why alias normalisation?**  
Without it, `"ml"` and `"machine learning"` count as different skills. The alias map resolves 300+ surface forms to canonical names before any comparison is made.

---

## ⚠️ Known Limitations

- Skill extraction is keyword-based — context-free (e.g. "no experience in Python" still matches Python)
- PDF text extraction quality depends on how the PDF was generated; scanned PDFs are not supported
- Experience detection is heuristic — it finds the highest number matching `"N years of experience"` patterns

---

## 👨‍💻 Author

**Shella Sai Srinivas** — B.Tech, Electronics and Communication Engineering  
[LinkedIn](#) · [GitHub](https://github.com/ssfullstack007)

---

## 📜 License

MIT — open source, free to use and modify.
