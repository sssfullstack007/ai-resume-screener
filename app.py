import os
import re
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# Create upload folder at import time, not just in __main__
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# ---------------------------------------------------------------------------
# Skill taxonomy — expanded + normalised aliases
# ---------------------------------------------------------------------------

# Maps every surface form → canonical name so "ML" and "machine learning" match
SKILL_ALIASES: dict[str, str] = {
    # Python ecosystem
    "python": "python", "py": "python",
    "pandas": "pandas", "numpy": "numpy", "scipy": "scipy",
    "matplotlib": "matplotlib", "seaborn": "seaborn",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "tensorflow": "tensorflow", "tf": "tensorflow",
    "pytorch": "pytorch", "torch": "pytorch",
    "keras": "keras", "fastapi": "fastapi", "flask": "flask",
    "django": "django",
    # ML / AI
    "machine learning": "machine learning", "ml": "machine learning",
    "deep learning": "deep learning", "dl": "deep learning",
    "nlp": "nlp", "natural language processing": "nlp",
    "computer vision": "computer vision", "cv": "computer vision",
    "llm": "llm", "large language models": "llm",
    "generative ai": "generative ai", "gen ai": "generative ai",
    "data analysis": "data analysis", "data analytics": "data analysis",
    "data science": "data science",
    # Web / frontend
    "javascript": "javascript", "js": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "react": "react", "reactjs": "react",
    "angular": "angular", "angularjs": "angular",
    "vue": "vue", "vuejs": "vue",
    "nodejs": "node.js", "node.js": "node.js", "node": "node.js",
    "html": "html", "css": "css", "html5": "html",
    # Backend
    "java": "java", "spring": "spring", "spring boot": "spring boot",
    "c++": "c++", "cpp": "c++", "c#": "c#", "dotnet": ".net", ".net": ".net",
    "php": "php", "ruby": "ruby", "rails": "ruby on rails",
    "go": "go", "golang": "go",
    "rust": "rust", "swift": "swift", "kotlin": "kotlin",
    # Databases
    "sql": "sql", "mysql": "mysql", "postgresql": "postgresql",
    "postgres": "postgresql", "mongodb": "mongodb", "mongo": "mongodb",
    "redis": "redis", "elasticsearch": "elasticsearch",
    "oracle": "oracle db", "cassandra": "cassandra",
    # Cloud / DevOps
    "aws": "aws", "amazon web services": "aws",
    "azure": "azure", "microsoft azure": "azure",
    "gcp": "gcp", "google cloud": "gcp",
    "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes",
    "terraform": "terraform", "ansible": "ansible",
    "ci/cd": "ci/cd", "jenkins": "jenkins", "github actions": "github actions",
    "linux": "linux", "unix": "unix",
    # Tools / practices
    "git": "git", "github": "github", "gitlab": "gitlab",
    "rest api": "rest api", "graphql": "graphql", "grpc": "grpc",
    "agile": "agile", "scrum": "scrum", "kanban": "kanban",
    "jira": "jira", "confluence": "confluence",
    "power bi": "power bi", "tableau": "tableau",
    "excel": "excel", "google sheets": "google sheets",
    # Soft skills
    "communication": "communication", "leadership": "leadership",
    "teamwork": "teamwork", "problem solving": "problem solving",
    "project management": "project management",
}

# Pre-sort by length descending so multi-word phrases match before subwords
_SORTED_ALIASES = sorted(SKILL_ALIASES.keys(), key=len, reverse=True)


def _compile_alias(surface: str) -> re.Pattern[str]:
    """
    Build a pattern that matches one alias as a whole token.

    A plain \\b boundary is wrong for aliases that start or end with a symbol.
    "c++", "c#" and ".net" contain no word character at one edge, so \\b can
    never match there and those skills were silently undetectable. Guard only
    the edges that actually are alphanumeric.
    """
    prefix = r"(?<![A-Za-z0-9])" if surface[0].isalnum() else ""
    suffix = r"(?![A-Za-z0-9])" if surface[-1].isalnum() else ""
    return re.compile(prefix + re.escape(surface) + suffix)


_ALIAS_PATTERNS = {surface: _compile_alias(surface) for surface in _SORTED_ALIASES}


def extract_skills(text: str) -> list[str]:
    """
    Extract canonical skills from text.

    Uses length-sorted alias matching to prefer multi-word phrases
    ("machine learning") over their abbreviations ("ml") when both
    are present, then deduplicates by canonical name.
    """
    text_lower = text.lower()
    found: set[str] = set()

    for surface, pattern in _ALIAS_PATTERNS.items():
        if pattern.search(text_lower):
            found.add(SKILL_ALIASES[surface])

    return sorted(found)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    if ext == "docx":
        return extract_text_from_docx(file_path)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def calculate_match_score(resume_text: str, job_description: str) -> float:
    """
    Compute a 0-100 similarity score using TF-IDF cosine similarity.

    Raw cosine on short docs rarely exceeds ~0.45, so we rescale:
      scaled = min(raw / 0.45, 1.0) * 100
    This maps a strong but realistic match (raw ≈ 0.40) to ~89 points.
    """
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        raw = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        scaled = min(raw / 0.45, 1.0) * 100
        return round(scaled, 1)
    except Exception:
        return 0.0


def _skill_score(resume_skills: list[str], job_skills: list[str]) -> float:
    """Percentage of job skills present in resume (0-100)."""
    if not job_skills:
        return 0.0
    matched = set(resume_skills) & set(job_skills)
    return round(len(matched) / len(job_skills) * 100, 1)


def composite_score(resume_text: str, resume_skills: list[str],
                    job_description: str, job_skills: list[str]) -> float:
    """
    Weighted composite: 60% TF-IDF similarity + 40% skill overlap.
    Gives skill keyword matching more explicit weight.
    """
    tfidf = calculate_match_score(resume_text, job_description)
    skill = _skill_score(resume_skills, job_skills)
    return round(0.6 * tfidf + 0.4 * skill, 1)


def get_missing_skills(resume_skills: list[str], job_skills: list[str]) -> list[str]:
    return sorted(set(job_skills) - set(resume_skills))


def get_matching_skills(resume_skills: list[str], job_skills: list[str]) -> list[str]:
    return sorted(set(resume_skills) & set(job_skills))


def get_candidate_rank(score: float) -> tuple[str, str]:
    """
    Rank based on rescaled composite score.
    Thresholds are calibrated to the rescaled 0-100 range.
    """
    if score >= 65:
        return "Strong Match", "success"
    if score >= 40:
        return "Moderate Match", "warning"
    return "Weak Match", "danger"


# ---------------------------------------------------------------------------
# Extract years of experience (heuristic)
# ---------------------------------------------------------------------------

_EXP_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:year|yr)s?\s*(?:of\s+)?(?:experience|exp)",
    re.IGNORECASE,
)


def extract_years_of_experience(text: str) -> int | None:
    """Return the highest year-count found in the text, or None."""
    matches = _EXP_PATTERN.findall(text)
    if not matches:
        return None
    return max(int(m) for m in matches)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    job_description: str = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Please provide a job description."}), 400

    files = request.files.getlist("resumes")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Please upload at least one resume."}), 400

    job_skills = extract_skills(job_description)
    results = []
    errors = []

    for file in files:
        if not file or not file.filename:
            continue

        filename = secure_filename(file.filename)
        if not filename:
            errors.append(f"Skipped a file with an unsupported name.")
            continue

        if not allowed_file(filename):
            errors.append(f"'{filename}' is not a supported file type (pdf, docx, txt).")
            continue

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(file_path)
            resume_text = extract_text(file_path)

            if not resume_text.strip():
                errors.append(f"'{filename}' appears to be empty or unreadable.")
                continue

            resume_skills = extract_skills(resume_text)
            score = composite_score(resume_text, resume_skills, job_description, job_skills)
            missing = get_missing_skills(resume_skills, job_skills)
            matching = get_matching_skills(resume_skills, job_skills)
            rank_label, rank_color = get_candidate_rank(score)
            years_exp = extract_years_of_experience(resume_text)

            results.append({
                "filename": filename,
                "score": score,
                "rank_label": rank_label,
                "rank_color": rank_color,
                "matching_skills": matching[:15],
                "missing_skills": missing[:10],
                "total_resume_skills": len(resume_skills),
                "years_experience": years_exp,
                # Breakdown for transparency
                "score_breakdown": {
                    "tfidf": calculate_match_score(resume_text, job_description),
                    "skill_overlap": _skill_score(resume_skills, job_skills),
                },
            })

        except Exception as exc:
            logger.exception("Error processing '%s'", filename)
            errors.append(f"Failed to process '{filename}': {exc}")

        finally:
            # Always clean up — even if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)

    results.sort(key=lambda x: x["score"], reverse=True)

    return jsonify({
        "results": results,
        "job_skills": job_skills[:20],
        "errors": errors,  # surface per-file errors to the UI
    })


# ---------------------------------------------------------------------------
# Optional: AI-powered improvement tips via Anthropic API
# (frontend calls this with a single resume's score data)
# ---------------------------------------------------------------------------

@app.route("/ai-tips", methods=["POST"])
def ai_tips():
    """
    Return Claude-generated improvement tips for one resume.

    Expects JSON: { filename, score, matching_skills, missing_skills }

    Optional endpoint. The page does not call it; it exists as a server-side
    proxy so an API key never has to live in the browser. Requires
    `pip install anthropic` and ANTHROPIC_API_KEY in the environment.
    """
    data = request.get_json(silent=True) or {}
    # Validate minimally
    required = {"filename", "score", "missing_skills"}
    if not required.issubset(data):
        return jsonify({"error": "Missing required fields."}), 400

    # Build a prompt and call Claude
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    prompt = (
        f"A candidate's resume scored {data['score']:.0f}/100 for a job opening.\n"
        f"Matching skills: {', '.join(data.get('matching_skills', [])) or 'none'}.\n"
        f"Skills missing from resume but required by job: "
        f"{', '.join(data['missing_skills']) or 'none'}.\n\n"
        "Give 3 concise, actionable tips the candidate can use to improve this resume "
        "for this specific role. Be direct and specific."
    )

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        tips = message.content[0].text
        return jsonify({"tips": tips})
    except Exception as exc:
        logger.exception("Anthropic API error")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True)
