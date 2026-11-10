---
title: AI Resume Screener
emoji: 📄
colorFrom: green
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Rank resumes against a job description
---

# AI Resume Screener

Upload one or more resumes (PDF, DOCX, TXT) plus a job description. The app
extracts canonical skills from both, scores each resume on TF-IDF similarity and
skill overlap, and returns a ranked shortlist with the skills each candidate is
missing.

Uploaded files are deleted immediately after processing. Nothing is stored, and
there is no database.

## Source and tests

Full repository, including the 23 tests and the scoring explanation:

<https://github.com/sssfullstack007/ai-resume-screener>

## Known limitations

- Skill matching is keyword-based and context-free, so a degree in "Electronics
  and Communication Engineering" is read as the soft skill "communication".
- TF-IDF is length-sensitive: a short resume with every required skill can still
  score in the "Moderate" band.
- Scanned PDFs are not supported; there is no OCR.

## Notes

This Space sleeps after 48 hours of inactivity. The first visit afterwards takes
roughly 30 seconds to start the container.
