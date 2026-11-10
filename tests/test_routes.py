"""
Tests for the HTTP routes, using Flask's test client.

Run from the repository root:

    py -m unittest discover -s tests -v
"""

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

JOB = "Junior Python developer. Python, SQL, Flask, Git, communication."

GOOD_RESUME = (
    b"Python developer with 2 years of experience. Flask, SQL, Git. "
    b"Strong communication."
)

WEAK_RESUME = b"Frontend developer. JavaScript, React, CSS."


class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _analyze(self, files, job=JOB):
        return self.client.post(
            "/analyze",
            data={"job_description": job, "resumes": files},
            content_type="multipart/form-data",
        )

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Resume", response.data)

    def test_missing_job_description_is_rejected(self):
        response = self.client.post(
            "/analyze",
            data={"job_description": "", "resumes": [(io.BytesIO(GOOD_RESUME), "a.txt")]},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_analysis_returns_ranked_results(self):
        response = self._analyze(
            [
                (io.BytesIO(GOOD_RESUME), "good.txt"),
                (io.BytesIO(WEAK_RESUME), "weak.txt"),
            ]
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()

        self.assertEqual(len(body["results"]), 2)
        scores = [r["score"] for r in body["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

        best = body["results"][0]
        self.assertEqual(best["filename"], "good.txt")
        self.assertEqual(best["missing_skills"], [])
        for key in (
            "score", "rank_label", "matching_skills", "missing_skills",
            "score_breakdown", "years_experience",
        ):
            self.assertIn(key, best)

    def test_one_bad_file_does_not_lose_the_batch(self):
        response = self._analyze(
            [
                (io.BytesIO(GOOD_RESUME), "good.txt"),
                (io.BytesIO(b"MZ\x90\x00 binary"), "virus.exe"),
            ]
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()

        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["filename"], "good.txt")
        self.assertEqual(len(body["errors"]), 1)
        self.assertTrue(any("virus.exe" in message for message in body["errors"]))

    def test_uploaded_files_are_cleaned_up(self):
        upload_dir = Path(app.root_path) / "uploads"
        before = set(upload_dir.iterdir()) if upload_dir.exists() else set()
        self._analyze([(io.BytesIO(GOOD_RESUME), "cleanup.txt")])
        after = set(upload_dir.iterdir()) if upload_dir.exists() else set()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
