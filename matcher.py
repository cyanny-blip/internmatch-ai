"""Transparent, explainable matching of resumes and internship descriptions.

All rankings are heuristic text comparisons. They are not hiring predictions.
"""
from __future__ import annotations

from functools import lru_cache
import re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# A deliberately small, inspectable dictionary. Extend as your field evolves.
SKILL_GROUPS: dict[str, dict[str, tuple[str, ...]]] = {
    "Programming": {
        "Python": ("python",),
        "Java": ("java",),
        "JavaScript": ("javascript", "java script", "js"),
        "TypeScript": ("typescript",),
        "C++": ("c++", "cplusplus"),
        "C#": ("c#", "c sharp"),
        "Go": ("golang", "go programming"),
        "R": ("r programming", "r language", "r studio", "rstudio"),
        "Bash": ("bash", "shell scripting"),
        "SQL": ("sql",),
        "HTML": ("html",),
        "CSS": ("css",),
    },
    "Data & AI": {
        "Machine Learning": ("machine learning", "ml models", "ml model"),
        "Deep Learning": ("deep learning",),
        "NLP": ("natural language processing", "nlp"),
        "LLMs": ("large language models", "llms", "llm", "generative ai", "genai"),
        "Data Analysis": ("data analysis", "data analytics"),
        "Data Visualization": ("data visualization", "data visualisation", "visualization"),
        "Statistics": ("statistics", "statistical analysis"),
        "Pandas": ("pandas",),
        "NumPy": ("numpy",),
        "scikit-learn": ("scikit-learn", "sklearn"),
        "PyTorch": ("pytorch",),
        "TensorFlow": ("tensorflow",),
        "Power BI": ("power bi",),
        "Tableau": ("tableau",),
        "Excel": ("excel", "spreadsheets"),
    },
    "Engineering": {
        "Git": ("git", "github", "gitlab"),
        "Linux": ("linux",),
        "Docker": ("docker",),
        "Kubernetes": ("kubernetes", "k8s"),
        "AWS": ("aws", "amazon web services"),
        "Azure": ("azure",),
        "GCP": ("gcp", "google cloud platform"),
        "CI/CD": ("ci/cd", "continuous integration", "continuous deployment"),
        "REST APIs": ("rest api", "restful api", "rest apis"),
        "Testing": ("unit testing", "automated testing", "pytest", "test automation"),
        "Algorithms": ("algorithms", "algorithm design"),
        "Data Structures": ("data structures",),
        "Object-Oriented Programming": ("object-oriented programming", "oop"),
        "System Design": ("system design",),
    },
    "Web & Databases": {
        "React": ("react", "reactjs", "react.js"),
        "Node.js": ("node.js", "nodejs"),
        "FastAPI": ("fastapi",),
        "Flask": ("flask",),
        "Streamlit": ("streamlit",),
        "PostgreSQL": ("postgresql", "postgres"),
        "MySQL": ("mysql",),
        "MongoDB": ("mongodb",),
    },
    "Professional": {
        "Communication": ("communication", "communicating"),
        "Teamwork": ("teamwork", "collaboration", "collaborative"),
        "Troubleshooting": ("troubleshooting", "debugging"),
        "Customer Service": ("customer service", "technical support"),
        "Documentation": ("documentation", "technical writing"),
        "Agile": ("agile", "scrum"),
    },
}


@lru_cache(maxsize=1024)
def extract_skills(text: str) -> frozenset[str]:
    """Return skills explicitly mentioned, using case-insensitive word boundaries."""
    if not text or not text.strip():
        return frozenset()
    found: set[str] = set()
    for group in SKILL_GROUPS.values():
        for skill, aliases in group.items():
            if any(re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", text, re.I)
                   for alias in aliases):
                found.add(skill)
    return frozenset(found)


def skill_categories(skills: set[str] | frozenset[str]) -> dict[str, list[str]]:
    return {
        category: sorted(name for name in entries if name in skills)
        for category, entries in SKILL_GROUPS.items()
        if any(name in skills for name in entries)
    }


def _tfidf_scores(resume: str, descriptions: list[str]) -> np.ndarray:
    if not descriptions:
        return np.array([], dtype=float)
    try:
        model = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                sublinear_tf=True, max_features=15000)
        matrix = model.fit_transform([resume, *descriptions])
        return cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    except ValueError:  # Example: documents contain only stop words
        return np.zeros(len(descriptions), dtype=float)


@lru_cache(maxsize=1)
def _semantic_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Semantic mode is optional. Install packages from requirements-semantic.txt "
            "or select the TF-IDF method."
        ) from exc
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _semantic_scores(resume: str, descriptions: list[str]) -> np.ndarray:
    model = _semantic_model()
    vectors = model.encode([resume, *descriptions], normalize_embeddings=True)
    return np.clip(np.asarray(vectors[1:]) @ np.asarray(vectors[0]), 0, 1)


def rank_jobs(
    resume: str,
    jobs: list[dict[str, str]],
    *,
    text_weight: float = 0.65,
    method: str = "tfidf",
) -> list[dict[str, Any]]:
    """Rank jobs. A score of 80 is NOT an 80% chance of getting hired.

    If a description has no recognized skills, its score uses text similarity
    alone. This avoids a meaningless zero skill-coverage penalty.
    """
    if not 0 <= text_weight <= 1:
        raise ValueError("text_weight must be between zero and one")
    if not resume or not resume.strip():
        raise ValueError("Enter a resume or skill summary first")
    if not jobs:
        return []
    for idx, job in enumerate(jobs):
        if not job.get("description", "").strip():
            raise ValueError(f"Job row {idx + 1} needs a description")

    descriptions = [job["description"] for job in jobs]
    if method == "tfidf":
        raw_similarities = _tfidf_scores(resume, descriptions)
    elif method == "semantic":
        raw_similarities = _semantic_scores(resume, descriptions)
    else:
        raise ValueError("Unknown method; use 'tfidf' or 'semantic'")

    own_skills = extract_skills(resume)
    ranked: list[dict[str, Any]] = []
    for job, raw_similarity in zip(jobs, raw_similarities):
        required_mentions = extract_skills(job["description"])
        matched = sorted(required_mentions & own_skills)
        missing = sorted(required_mentions - own_skills)
        coverage = len(matched) / len(required_mentions) if required_mentions else None
        similarity = float(np.clip(raw_similarity, 0, 1))
        score = (
            text_weight * similarity + (1 - text_weight) * coverage
            if coverage is not None else similarity
        )
        ranked.append({
            "title": job.get("title", "Untitled role"),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "url": job.get("url", ""),
            "description": job["description"],
            "score": round(score * 100, 1),
            "text_similarity": round(similarity * 100, 1),
            "skill_coverage": round(coverage * 100, 1) if coverage is not None else None,
            "matched_skills": matched,
            "missing_mentions": missing,
            "mentioned_skill_count": len(required_mentions),
        })
    return sorted(ranked, key=lambda row: (-row["score"], row["title"].casefold()))
