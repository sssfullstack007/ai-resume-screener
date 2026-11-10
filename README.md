# AI Resume Screener

A Flask app that scores uploaded resumes against a job description. It combines
TF-IDF cosine similarity with skill-overlap matching, then reports a match score,
the skills that matched, and the specific skills missing from each resume.

## Example output

Three sample resumes scored against one job description, using the same
functions the `/analyze` route calls:

```
job skills: ['communication', 'flask', 'git', 'pandas', 'python', 'sql']

candidate_a_python_focus.txt
  composite 59.4%  (Moderate Match)
  breakdown: tfidf 32.3% x 0.6  +  skills 100.0% x 0.4
  experience detected: 2 year(s)
  matching : ['communication', 'flask', 'git', 'pandas', 'python', 'sql']
  missing  : []

candidate_b_frontend.txt
  composite 10.0%  (Weak Match)
  breakdown: tfidf 5.6% x 0.6  +  skills 16.7% x 0.4
  experience detected: 4 year(s)
  matching : ['git']
  missing  : ['communication', 'flask', 'pandas', 'python', 'sql']

candidate_c_beginner.txt
  composite 19.1%  (Weak Match)
  breakdown: tfidf 9.7% x 0.6  +  skills 33.3% x 0.4
  experience detected: 0 year(s)
  matching : ['flask', 'python']
  missing  : ['communication', 'git', 'pandas', 'sql']
```

Candidate A has every required skill and still scores 59.4%, because TF-IDF
rewards longer, more similar text. That limitation is documented below rather
than hidden behind the threshold.

## Features

| Feature | Detail |
|---|---|
| Multi-resume upload | PDF, DOCX and TXT |
| Skill extraction | 110 aliases resolving to 82 canonical skills (`"ml"` = `"machine learning"`) |
| Composite score | 60% TF-IDF similarity + 40% skill overlap, rescaled to 0–100 |
| Candidate ranking | Sorted by score: Strong / Moderate / Weak, with thresholds at 65 and 40 |
| Skill gap analysis | The job-required skills missing from each resume |
| Experience detection | Highest `"N years of experience"` match in the text |
| Fault tolerance | Each upload is parsed in isolation, so one bad file does not lose the batch |

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask |
| Matching | scikit-learn TF-IDF vectoriser, cosine similarity |
| File parsing | PyPDF2 (PDF), python-docx (DOCX) |
| Tests | `unittest` from the standard library |
| Frontend | HTML, CSS, Bootstrap 5 via CDN |
| Optional | Anthropic SDK, only for the `/ai-tips` endpoint |

## Project structure

```
ai-resume-screener/
├── app.py                  # routes, scoring, skill extraction
├── requirements.txt
├── templates/
│   └── index.html          # single-page UI
├── static/
│   └── css/
│       └── style.css
├── tests/
│   ├── test_scoring.py     # 18 tests over the scoring logic
│   └── test_routes.py      # 5 tests over the HTTP routes
├── uploads/                # temp storage, created at import, git-ignored
├── LICENSE
└── README.md
```

## Setup and run

```bash
git clone https://github.com/sssfullstack007/ai-resume-screener.git
cd ai-resume-screener
py -m pip install -r requirements.txt
py app.py
```

Then open <http://127.0.0.1:5000>, paste a job description, and upload one or
more resumes.

### Optional: AI tips endpoint

`/ai-tips` proxies to Claude so the API key stays server-side. It needs one
extra package and an environment variable:

```bash
py -m pip install anthropic
export ANTHROPIC_API_KEY=your_key_here     # Windows: set ANTHROPIC_API_KEY=...
```

The rest of the app works without either. The page itself never calls this
endpoint, and no key is stored in this repository.

## Tests

```bash
py -m unittest discover -s tests -v
```

23 tests, no extra dependency. `test_scoring.py` covers the alias matcher, the
0–100 bounds, the 60/40 weighting, the rank thresholds, the skill diff and the
experience heuristic. `test_routes.py` drives the real Flask app through its
test client: the page loads, a missing job description is rejected with 400,
results come back sorted, one unsupported file does not lose the rest of the
batch, and uploads are cleaned up.

One scoring test is a regression test: `c++`, `c#` and `.net` used to be in the
alias map but could never match, because `\b` requires a word character at both
edges and those aliases do not have one.

## Deploying it

This is a Flask app, so it needs a Python host. **GitHub Pages cannot serve it** —
Pages only serves static files, which is why the portfolio works there and this
does not.

### Option A — Hugging Face Spaces

The Space files live in `deploy/huggingface/`:

| File | Why it exists |
|---|---|
| `Dockerfile` | Spaces builds a container; runs gunicorn on port 7860 as non-root uid 1000 |
| `README.md` | Spaces reads the YAML front matter for title, SDK and `app_port` |
| `.dockerignore` | Keeps tests, caches and the deploy folder out of the image |
| `publish.ps1` | Copies the app into a Space checkout, and pushes with `-Push` |

```bash
git clone https://huggingface.co/spaces/<user>/ai-resume-screener hf-space
powershell -File deploy\huggingface\publish.ps1 -Target ..\hf-space -Push
```

The Space rebuilds on every push. Re-run the same command after changing `app.py`.

### Option B — Render

1. On Render: **New → Blueprint**, select this repository.
2. Render reads `render.yaml` and builds it.
3. You get a URL like `https://ai-resume-screener-xxxx.onrender.com`.

The `Procfile` and `render.yaml` carry the same start command as the Dockerfile.

### What has to be true on any host

| Setting | Purpose |
|---|---|
| gunicorn, not `flask run` | The dev server is single-threaded and not for public traffic |
| Bind `0.0.0.0` on the injected port | Hosts assign the port at runtime; hardcoding 5000 fails |
| `debug=False` | The Werkzeug debugger allows remote code execution — never public |
| Pinned interpreter | `PYTHON_VERSION=3.11.9`, so builds are reproducible |

**Free-tier reality, stated honestly:** the service sleeps after about 15 minutes
of inactivity, so the first visit afterwards takes 30–60 seconds to wake. It has
512 MB RAM, which is enough for scikit-learn here. Disk is ephemeral.

**Privacy:** uploads are written to `uploads/` and deleted in a `finally` block
after each request. Nothing is persisted, there is no database, and resume
contents are not logged.

Other hosts that work: Hugging Face Spaces (Docker SDK) and PythonAnywhere.
Fly.io no longer has a free tier.

## How it works

1. Paste a job description.
2. Upload one or more resumes.
3. The server extracts text, extracts canonical skills from both sides, and
   computes the composite score.
4. Results are ranked: composite score, score breakdown, matching skills,
   missing skills, and years of experience detected.

## Scoring

```
Resume text    ──┐
                 ├──► TF-IDF (1-2 grams) ──► cosine similarity ──► ÷0.45 ──┐
Job description ─┘                                                          │
                                                                            ├──► composite (0-100)
Skill aliases ──► canonical skills ──► overlap % ────────────────────────────┘
                                        60% weight     40% weight

Thresholds: ≥ 65 Strong Match, 40–64 Moderate Match, < 40 Weak Match
```

**Why rescale TF-IDF?** Raw cosine similarity between two short documents rarely
exceeds about 0.45, even for near-perfect matches. Dividing by 0.45 before
converting to a percentage uses the whole 0–100 range.

**Why alias normalisation?** Without it, `"ml"` and `"machine learning"` count as
different skills. The alias map resolves 110 surface forms to 82 canonical names
before any comparison happens.

## Known limitations

- Skill extraction is keyword-based and context-free: `"no experience in Python"`
  still counts as Python.
- TF-IDF is length-sensitive. A short resume with 100% skill overlap scores lower
  than a long, keyword-dense one. The thresholds do not correct for this.
- PDF extraction depends on how the PDF was produced; scanned images are not
  supported because there is no OCR.
- Experience detection is a regex heuristic: it takes the highest number matching
  `"N years of experience"`, so it can be fooled by phrasing.
- All scoring logic currently lives in one `app.py`. It should be split into
  modules before it grows further.
- `/ai-tips` has not been exercised against a live API call, because no key is
  stored in this repository.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Sai Srinivas Shella** — B.Tech, Electronics and Communication Engineering
[GitHub](https://github.com/sssfullstack007)
