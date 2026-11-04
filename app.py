"""InternMatch — an educational, explainable internship-matching web app."""
from __future__ import annotations

from collections import Counter
import importlib.util
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from file_utils import load_jobs_csv, resume_to_text
from matcher import extract_skills, rank_jobs, skill_categories

ROOT = Path(__file__).resolve().parent
DEMO_RESUME = (ROOT / "sample_data" / "demo_resume.txt").read_text(encoding="utf-8")
DEMO_JOBS = (ROOT / "sample_data" / "demo_jobs.csv").read_bytes()

st.set_page_config(
    page_title="InternMatch • Explainable job matching",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1220px; }
    h1, h2, h3 { letter-spacing: -0.02em; }
    [data-testid="stMetric"] {
        background: #172337; border: 1px solid #263954;
        padding: 1rem; border-radius: 14px;
    }
    .hero {
        padding: 1.25rem 1.5rem; border-radius: 18px;
        background: linear-gradient(115deg, #132d36, #183151 80%);
        border: 1px solid #2f6570; margin-bottom: 1.3rem;
    }
    .hero small { color: #9bead6; text-transform: uppercase; letter-spacing: .12em; }
    .hero h1 { margin: .25rem 0; }
    .hero p { color: #c9d9ea; margin-bottom: 0; }
    .muted { color: #adc4d8; font-size: .92rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <small>Portfolio project · Python + NLP</small>
  <h1>🧭 InternMatch</h1>
  <p>Find relevant internships, see what keywords overlap, and decide which skills to learn next.</p>
</div>
""", unsafe_allow_html=True)
st.caption("Educational tool • No scraping • No hiring predictions • Demo listings are fictional")

with st.sidebar:
    st.header("⚙️ Matching settings")
    text_weight_pct = st.slider(
        "Text similarity weight", min_value=0, max_value=100,
        value=65, step=5,
        help="Remaining weight goes to detected skill coverage. If a listing mentions no recognized skills, only text similarity is used.",
    )
    semantic_available = importlib.util.find_spec("sentence_transformers") is not None
    methods = ["TF-IDF (fast, local)"] + (["Semantic embeddings (advanced)"] if semantic_available else [])
    chosen_method = st.selectbox("Matching method", methods)
    method = "semantic" if chosen_method.startswith("Semantic") else "tfidf"
    if not semantic_available:
        st.caption("Optional sentence-embedding mode requires requirements-semantic.txt on a local machine.")
    st.divider()
    st.subheader("How the score works")
    st.write(f"**{text_weight_pct}%** text similarity + **{100 - text_weight_pct}%** mentioned-skill coverage")
    st.caption("Scores are heuristics, not grades, ATS scores, job eligibility checks, or interview probabilities.")
    st.divider()
    st.subheader("Privacy")
    st.caption("This code does not save uploaded resumes or send them to an AI API. On a deployed website, uploads are processed by its hosting server. Don't publish your personal resume in GitHub.")

left, right = st.columns([1, 1], gap="large")
with left:
    st.subheader("1 · Add your experience")
    resume_mode = st.radio("Resume input", ["Try fictional example", "Paste my skills", "Upload resume"], horizontal=True)
    if resume_mode == "Try fictional example":
        resume_text = st.text_area("Fictional example resume", DEMO_RESUME, height=205)
        st.info("This is imaginary demo content. Replace it with your own accurate experience when ready.")
    elif resume_mode == "Paste my skills":
        resume_text = st.text_area(
            "Paste a resume or a skills summary", height=210,
            placeholder="Your education, projects, technical skills, and work experience. Avoid adding private contact details.",
        )
    else:
        resume_file = st.file_uploader("Upload a .pdf, .docx, or .txt resume", type=["pdf", "docx", "txt"])
        resume_text = ""
        if resume_file is not None:
            try:
                resume_text = resume_to_text(resume_file, resume_file.name)
                if not resume_text.strip():
                    st.error("No selectable text found. If this is a scanned PDF, paste your resume text instead.")
                else:
                    st.success(f"Read {len(resume_text):,} characters of text.")
            except ValueError as exc:
                st.error(str(exc))
    own_skills = extract_skills(resume_text)
    if resume_text.strip():
        st.caption(f"Detected {len(own_skills)} recognizable skills in your text")
        with st.expander("See detected skills"):
            for category, skills in skill_categories(own_skills).items():
                st.write(f"**{category}:** {', '.join(skills)}")
            if not own_skills:
                st.write("No matching terms found. You can still compare text similarity.")

with right:
    st.subheader("2 · Add internship listings")
    job_mode = st.radio("Job descriptions", ["Use fictional examples", "Upload jobs CSV", "Paste one job"], horizontal=True)
    jobs = []
    if job_mode == "Use fictional examples":
        jobs = load_jobs_csv(DEMO_JOBS)
        st.success(f"Loaded {len(jobs)} fictional sample positions — not live vacancies.")
        st.download_button("⬇ Download the sample jobs CSV", DEMO_JOBS,
                           file_name="example_jobs.csv", mime="text/csv")
    elif job_mode == "Upload jobs CSV":
        st.caption("Required: `title`, `description`. Optional: `company`, `location`, `url`.")
        uploaded_csv = st.file_uploader("Upload CSV (up to 200 jobs)", type=["csv"])
        if uploaded_csv is not None:
            try:
                jobs = load_jobs_csv(uploaded_csv.getvalue())
                st.success(f"Loaded {len(jobs)} positions")
            except ValueError as exc:
                st.error(str(exc))
    else:
        title = st.text_input("Job title", placeholder="e.g. Software Engineering Intern")
        company = st.text_input("Company (optional)")
        location = st.text_input("Location (optional)")
        url = st.text_input("Job link (optional, https://...)")
        description = st.text_area("Paste the job description", height=130)
        if description.strip():
            jobs = [{"title": title.strip() or "Pasted position", "company": company,
                     "location": location, "url": url, "description": description}]
    st.caption("Use real job descriptions you find yourself. This project doesn't check application deadlines or verify vacancies.")

st.divider()
st.subheader("3 · Explore your matches")

if not resume_text.strip():
    st.info("Add your experience in Step 1 to start.")
elif not jobs:
    st.info("Add at least one job description in Step 2 to start.")
else:
    try:
        results = rank_jobs(resume_text, jobs, text_weight=text_weight_pct / 100, method=method)
    except Exception as exc:
        st.error(f"Matching couldn't run: {exc}")
        st.stop()

    location_filter = st.text_input("Filter by location (optional)", placeholder="e.g. Edmonton, remote, Calgary")
    if location_filter.strip():
        visible = [r for r in results if location_filter.casefold().strip() in r["location"].casefold()]
    else:
        visible = results

    if not visible:
        st.warning("No listings matched that location filter. Try removing it.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Listings compared", len(visible))
        m2.metric("Highest relative match", f"{visible[0]['score']:.1f}/100")
        m3.metric("Skills found in your text", len(own_skills))

        chart_data = pd.DataFrame([
            {"Role": f"{r['title'][:36]} · {i + 1}", "Heuristic score": r["score"]}
            for i, r in enumerate(visible[:10])
        ]).set_index("Role")
        st.bar_chart(chart_data, horizontal=True, color="#71E5C1")

        st.caption("The score is a tunable text-and-keyword comparison. It is **not** a hiring probability or a standardized industry score.")
        csv_rows = [{
            "title": r["title"], "company": r["company"], "location": r["location"],
            "heuristic_score": r["score"], "text_similarity": r["text_similarity"],
            "mentioned_skill_coverage": r["skill_coverage"],
            "skills_found": "; ".join(r["matched_skills"]),
            "skills_not_mentioned_in_resume": "; ".join(r["missing_mentions"]),
            "url": r["url"],
        } for r in visible]
        csv_buffer = StringIO()
        pd.DataFrame(csv_rows).to_csv(csv_buffer, index=False)
        st.download_button("⬇ Export match results as CSV", csv_buffer.getvalue(),
                           file_name="internmatch_results.csv", mime="text/csv")

        for index, r in enumerate(visible):
            with st.container(border=True):
                col_title, col_score = st.columns([5, 1])
                with col_title:
                    st.markdown(f"#### {index + 1}. {r['title']}")
                    st.caption(" · ".join(p for p in (r["company"], r["location"]) if p) or "Unspecified company / location")
                with col_score:
                    st.metric("Match", f"{r['score']:.1f}")
                st.progress(min(max(r["score"] / 100, 0), 1))
                if r["url"] and urlparse(r["url"]).scheme in ("https", "http") and urlparse(r["url"]).netloc:
                    st.link_button("Open supplied job listing", r["url"])
                with st.expander("Why this role ranked here · skills and description"):
                    a, b = st.columns(2)
                    a.write(f"**Text similarity:** {r['text_similarity']:.1f}/100")
                    b.write("**Mentioned-skill coverage:** " +
                            (f"{r['skill_coverage']:.1f}%" if r["skill_coverage"] is not None else "No recognized job skills"))
                    st.write("**Skills mentioned in both texts**")
                    st.write(", ".join(r["matched_skills"]) or "None detected")
                    st.write("**Job-description skills not found in your text**")
                    st.write(", ".join(r["missing_mentions"]) or "None detected")
                    st.caption("Missing mentions do not mean you're unqualified or lack those skills; they might simply be missing from the text.")
                    st.write("**Job description**")
                    st.write(r["description"])

        st.divider()
        st.subheader("4 · Skill-gap explorer")
        st.write("These are terms mentioned in job descriptions but not detected in your resume text. Use them as a research and learning checklist—not as claims about your abilities.")
        gaps = Counter(skill for r in visible for skill in r["missing_mentions"])
        if gaps:
            gap_rows = [{"Skill mention": skill, "Jobs mentioning it": count}
                        for skill, count in gaps.most_common()]
            st.dataframe(pd.DataFrame(gap_rows), hide_index=True, use_container_width=True)
            top_gaps = ", ".join(skill for skill, _ in gaps.most_common(5))
            st.info(f"Suggested next step: choose **one** of these recurring skill terms to learn or demonstrate in a project: {top_gaps}.")
        else:
            st.success("No unmatched recognized skill terms in these job descriptions. Check the full requirements, experience level, and eligibility manually.")

with st.expander("Methodology, limitations, and responsible use"):
    st.markdown("""
    - **Text similarity:** TF-IDF vectors (unigrams and bigrams) with cosine similarity. An optional sentence-embedding mode is available when extra dependencies are installed.
    - **Skill coverage:** a small, editable dictionary of common skill terms and aliases, matched across the job description and resume. It is not a complete skills ontology.
    - **Overall heuristic:** weighted average of text similarity and skill coverage, except when no recognized skills are mentioned (then text similarity alone is used).
    - **What it cannot do:** verify qualifications, parse nuance such as 'preferred' versus 'required', check work authorization, identify live openings, guarantee interviews, or predict hiring decisions.
    - **Bias and limitations:** written wording strongly affects scores. Missing keyword mentions do not establish missing abilities. Always read original postings and make your own decisions.
    - **Data:** example employers and listings are fabricated. The code doesn't persist resumes to files or call third-party AI services. Deployed hosts still process uploads on their servers.
    """)

st.caption("Built with Streamlit · scikit-learn · Python | Independent educational project; not affiliated with Amii or any employer.")
