# 🧭 InternMatch — Explainable AI Internship Matcher

**Compare internship descriptions with your experience, understand the overlap, and identify skills to explore next.**

InternMatch is an interactive Python web app that uses natural-language processing (NLP) and transparent skill extraction to rank internship descriptions against a resume or skill summary. It was built as an **independent learning and portfolio project**, not as a recruiting or hiring system.

> **Status:** Functional portfolio prototype, with sample data and automated tests. The included employers and listings are **fictional examples**, not current vacancies.

## ✨ Features

- **Interactive matching dashboard:** Compare a resume against one posting, a CSV of postings, or eight fictional demo jobs.
- **Resume input:** Paste text or upload `.txt`, text-based `.pdf`, or `.docx` files.
- **Explainable ranking:** See the overall heuristic score, TF-IDF text similarity, recognized skills appearing in both texts, and skills mentioned in the job description but not found in the resume text.
- **Adjustable weighting:** Change the balance between text similarity and keyword-based skill coverage.
- **Skill-gap explorer:** Find recurring skill mentions across multiple job descriptions.
- **Exportable results:** Download ranked matches and explanations as CSV.
- **Optional advanced NLP:** Run semantic sentence embeddings by installing extra dependencies.
- **Automated testing:** GitHub Actions runs the test suite on each push/pull request.

## 🧰 Tech stack

| Layer | Technologies |
| --- | --- |
| Interface | Python, Streamlit |
| NLP baseline | scikit-learn `TfidfVectorizer`, cosine similarity |
| Skill analysis | Python regular expressions, transparent skill dictionary |
| Data | Python CSV tools, pandas |
| Document parsing | pypdf, python-docx |
| Optional NLP | sentence-transformers (`all-MiniLM-L6-v2`) |
| Testing and CI | pytest, GitHub Actions |

## 🚀 Quick start

Requires **Python 3.11+**.

```bash
# 1. Clone the repository after you've uploaded it to GitHub.
git clone https://github.com/YOUR_USERNAME/internmatch-ai.git
cd internmatch-ai

# 2. Create a virtual environment.
python -m venv .venv

# 3. Activate it.
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 4. Install packages.
pip install -r requirements.txt

# 5. Run the app.
streamlit run app.py
```

A local browser tab opens with the app. Select **Try fictional example** and **Use fictional examples** to try it without a resume or real job listing.

To enable **semantic embeddings** instead of TF-IDF, install `pip install -r requirements-semantic.txt` locally. The optional model is downloaded on first use, so this mode may be slower and requires an internet connection initially. The lightweight default deployment uses TF-IDF.

## 🗂️ Repository layout

```text
internmatch-ai/
├── app.py                  # Streamlit user interface
├── matcher.py              # Scoring, skill detection, optional embeddings
├── file_utils.py           # Resume parsing and CSV validation
├── sample_data/
│   ├── demo_jobs.csv       # Entirely fictional postings
│   └── demo_resume.txt     # Entirely fictional sample resume
├── tests/                  # Automated tests
├── .github/workflows/      # CI checks
├── .streamlit/config.toml  # Interface theme
├── requirements.txt
├── requirements-semantic.txt
└── README.md
```

## 🧪 How to use it with real listings

1. Select **Paste my skills** or **Upload resume** and provide an accurate, non-sensitive summary of your experience.
2. Choose **Paste one job** to compare a job directly, or **Upload jobs CSV** for multiple positions.
3. For a CSV, include `title` and `description` (or `job_title` and `job_description`). Optional columns are `company`, `location`, and `url`.
4. Check each match's explanation. Treat missing skill mentions as prompts to investigate, **not evidence that you lack those skills**.
5. Export the results and read the original job posting to confirm eligibility and dates.

**CSV example** (the actual file `sample_data/demo_jobs.csv` includes more examples):

```csv
title,company,location,description,url
Software Intern,Example Co.,Edmonton AB,"Python, SQL, Git, unit testing and communication",
```

## 🔬 How scoring works

Default scoring formula for each job:

```text
heuristic_score = 100 × (
    0.65 × text_similarity
  + 0.35 × mentioned_skill_coverage
)
```

- **Text similarity** is TF-IDF cosine similarity between the resume and each job description, measured from 0 to 1. Since scores depend on language and the comparison dataset, they aren't calibrated probabilities.
- **Mentioned-skill coverage** is the fraction of recognized skill terms in the job description that also appear in the resume text.
- If there are no recognized skill terms in the job description, only the text similarity score is used.
- Weighting is adjustable in the sidebar.

Example: a score of `72` is **not** a 72% chance of getting hired. The tool **does not** evaluate university eligibility, work authorization, required years of experience, hiring decisions, or whether a position is open.

## 🔒 Privacy and safety

- No external AI API, job-site scraper, or database is used by the default matching pipeline.
- The app does not write uploaded resumes to disk. Uploaded data is processed in the Streamlit server's memory during the session.
- If you deploy the app publicly, files and pasted text are processed on that **remote host**, not exclusively on the visitor's device. Follow the host's privacy policies.
- **Never commit real resumes, addresses, passwords, API keys, or other private information to this repository.** Use only fictional demo materials in public code.
- PDF text extraction is not OCR. Scanned/image-only PDFs may require users to paste their text.

## 🧪 Tests

```bash
pip install -r requirements.txt pytest
python -m pytest -q
```

The tests check keyword boundaries/aliases, scoring, ranking order, missing terms, input validation, and CSV parsing.

## 🌐 Deploy a live demo (optional)

1. Upload the project files into a **public** GitHub repository named `internmatch-ai`.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) using GitHub.
3. Choose **Create app**, then **Yup, I have an app**.
4. Select your GitHub repository, main branch, and `app.py` as the entrypoint.
5. Deploy, then put the resulting `.streamlit.app` URL in your GitHub repository's **About → Website** field.

The provided `requirements.txt` supports the default TF-IDF app. The semantic model is optional and is not installed in a standard deploy.

## 🗺️ Roadmap

- [ ] Improve skill extraction using contextual models rather than keyword mentions alone.
- [ ] Distinguish explicitly required skills from preferred skills.
- [ ] Evaluate rankings against a hand-labeled set of realistic job/resume pairs.
- [ ] Improve accessibility and mobile layouts based on usability testing.
- [ ] Add a local-only resume redaction helper before sharing results.

## 🎯 What this project demonstrates

Practical Python development, feature engineering, text vectorization, cosine similarity, transparent scoring, interactive dashboards, file validation, testing, and software documentation.

**Important:** This is an educational matching tool, not an official service of Amii, the University of Alberta, or any employer.
