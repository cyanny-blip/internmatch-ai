from matcher import extract_skills, rank_jobs, skill_categories


def test_skill_alias_and_boundaries():
    found = extract_skills("Python, C++, SQL, React.js, machine learning and GitHub")
    assert {"Python", "C++", "SQL", "React", "Machine Learning", "Git"} <= found
    assert "Java" not in found


def test_empty_skills():
    assert not extract_skills("")


def test_skill_grouping():
    assert skill_categories(frozenset({"SQL", "Git"})) == {
        "Programming": ["SQL"], "Engineering": ["Git"]
    }


def test_relevant_job_ranks_first():
    jobs = [
        {"title": "Gardening", "description": "landscaping flowers soil planting"},
        {"title": "Developer", "description": "Python, SQL, Git, algorithms"},
    ]
    ranked = rank_jobs("Python and SQL with Git, algorithms", jobs)
    assert ranked[0]["title"] == "Developer"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert not ranked[0]["missing_mentions"]


def test_missing_skills_are_mentions_not_eligibility():
    jobs = [{"title": "AI", "description": "Python, PyTorch, AWS"}]
    ranked = rank_jobs("Python", jobs)
    assert ranked[0]["missing_mentions"] == ["AWS", "PyTorch"]
    assert ranked[0]["matched_skills"] == ["Python"]
    assert abs(ranked[0]["skill_coverage"] - 33.3) < 0.1


def test_no_detected_job_skills_uses_text_only():
    ranked = rank_jobs("orchard pear cultivation", [{"title": "Grower", "description": "orchard pear cultivation"}])
    assert ranked[0]["skill_coverage"] is None
    assert ranked[0]["score"] == ranked[0]["text_similarity"]


def test_validation():
    import pytest
    with pytest.raises(ValueError):
        rank_jobs("", [{"title": "Test", "description": "Python"}])
    with pytest.raises(ValueError):
        rank_jobs("Python", [{"title": "Blank", "description": ""}])
    with pytest.raises(ValueError):
        rank_jobs("Python", [{"title": "Test", "description": "Python"}], text_weight=2)
    with pytest.raises(ValueError):
        rank_jobs("Python", [{"title": "Test", "description": "Python"}], method="unknown")


def test_skills_sorted_and_scores_bounded():
    jobs = [
        {"title": "A", "description": "Python Java SQL"},
        {"title": "B", "description": "Java Python"},
    ]
    for row in rank_jobs("Python SQL", jobs, text_weight=0):
        assert 0 <= row["score"] <= 100
        assert row["matched_skills"] == sorted(row["matched_skills"])
