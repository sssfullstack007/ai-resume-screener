"""
Tests for the scoring and skill-extraction logic.

Run from the repository root:

    py -m unittest discover -s tests -v

No extra dependency: this uses the standard library's unittest.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import (  # noqa: E402
    SKILL_ALIASES,
    calculate_match_score,
    composite_score,
    extract_skills,
    extract_years_of_experience,
    get_candidate_rank,
    get_matching_skills,
    get_missing_skills,
    _skill_score,
)


class TestSkillExtraction(unittest.TestCase):
    def test_plain_skills_are_found(self):
        found = extract_skills("I use Python and SQL every day")
        self.assertIn("python", found)
        self.assertIn("sql", found)

    def test_symbol_aliases_are_found(self):
        """Regression: a \\b boundary can never match c++, c# or .net."""
        found = extract_skills("Skills: C++, C#, .NET")
        self.assertIn("c++", found)
        self.assertIn("c#", found)
        self.assertIn(".net", found)

    def test_longer_alias_does_not_leak_into_shorter_one(self):
        found = extract_skills("I write javascript")
        self.assertIn("javascript", found)
        self.assertNotIn("java", found)

    def test_alias_normalises_to_one_canonical_name(self):
        shorthand = extract_skills("ml")
        spelled_out = extract_skills("machine learning")
        self.assertEqual(shorthand, spelled_out)

    def test_no_skill_matched_in_plain_prose(self):
        found = extract_skills("I enjoy hiking and cooking on weekends")
        self.assertEqual(found, [])

    def test_alias_map_is_not_empty(self):
        self.assertGreater(len(SKILL_ALIASES), 50)


class TestScoring(unittest.TestCase):
    def test_score_stays_in_range(self):
        for resume, job in [
            ("python sql flask", "python sql flask"),
            ("", "python sql"),
            ("completely unrelated text", "python sql flask"),
        ]:
            score = calculate_match_score(resume, job)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)

    def test_identical_text_scores_highest(self):
        text = "python sql flask pandas git"
        self.assertGreater(calculate_match_score(text, text), 90)

    def test_skill_score_full_and_partial(self):
        self.assertEqual(_skill_score(["a", "b"], ["a", "b"]), 100.0)
        self.assertEqual(_skill_score(["a"], ["a", "b"]), 50.0)
        self.assertEqual(_skill_score([], ["a", "b"]), 0.0)

    def test_skill_score_without_job_skills_is_zero(self):
        self.assertEqual(_skill_score(["a"], []), 0.0)

    def test_composite_is_weighted_average(self):
        resume = "python sql flask pandas git"
        job = "python sql flask pandas git"
        skills = extract_skills(resume)
        score = composite_score(resume, skills, job, skills)
        self.assertGreaterEqual(score, 90.0)


class TestSkillDiff(unittest.TestCase):
    def test_missing_skills(self):
        self.assertEqual(
            get_missing_skills(["python", "sql"], ["python", "sql", "flask"]),
            ["flask"],
        )

    def test_matching_skills(self):
        self.assertEqual(
            get_matching_skills(["python", "sql", "excel"], ["python", "sql"]),
            ["python", "sql"],
        )

    def test_diff_is_sorted(self):
        missing = get_missing_skills([], ["sql", "flask", "aws"])
        self.assertEqual(missing, sorted(missing))


class TestRanking(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(get_candidate_rank(90)[0], "Strong Match")
        self.assertEqual(get_candidate_rank(65)[0], "Strong Match")
        self.assertEqual(get_candidate_rank(64)[0], "Moderate Match")
        self.assertEqual(get_candidate_rank(40)[0], "Moderate Match")
        self.assertEqual(get_candidate_rank(39)[0], "Weak Match")


class TestExperience(unittest.TestCase):
    def test_detects_years(self):
        self.assertEqual(extract_years_of_experience("I have 5 years of experience"), 5)
        self.assertEqual(extract_years_of_experience("3 yrs experience in QA"), 3)

    def test_returns_none_when_absent(self):
        self.assertIsNone(extract_years_of_experience("Recent graduate"))

    def test_takes_the_highest_number(self):
        text = "2 years of experience as an intern, 6 years of experience overall"
        self.assertEqual(extract_years_of_experience(text), 6)


if __name__ == "__main__":
    unittest.main()
