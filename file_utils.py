"""Input decoding and defensive CSV validation. Uploaded files are not saved."""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader

MAX_RESUME_BYTES = 4 * 1024 * 1024
MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_JOBS = 200


def resume_to_text(file: BinaryIO, filename: str) -> str:
    raw = file.read(MAX_RESUME_BYTES + 1)
    if len(raw) > MAX_RESUME_BYTES:
        raise ValueError("Resume file is too large (limit: 4 MB)")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".txt":
            return raw.decode("utf-8-sig")
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(raw))
            if len(reader.pages) > 30:
                raise ValueError("Use a resume of 30 pages or fewer")
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if suffix == ".docx":
            doc = Document(io.BytesIO(raw))
            paragraphs = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                paragraphs.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
            return "\n".join(paragraphs)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not read that {suffix or 'file'} file") from exc
    raise ValueError("Supported resume formats: .txt, .pdf and .docx")


def load_jobs_csv(raw: bytes) -> list[dict[str, str]]:
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError("CSV file is too large (limit: 2 MB)")
    try:
        contents = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Save your CSV as UTF-8") from exc
    try:
        reader = csv.DictReader(io.StringIO(contents))
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        fields = {field.strip().lower(): field for field in reader.fieldnames if field}
        title_field = fields.get("title") or fields.get("job_title")
        description_field = fields.get("description") or fields.get("job_description")
        if not title_field or not description_field:
            raise ValueError("CSV needs title and description columns")
        jobs: list[dict[str, str]] = []
        for line, row in enumerate(reader, start=2):
            if len(jobs) >= MAX_JOBS:
                raise ValueError(f"Use {MAX_JOBS} jobs or fewer at once")
            if None in row:
                raise ValueError(f"Invalid CSV row {line}; check quoted commas")
            desc = (row.get(description_field) or "").strip()
            if not desc:
                continue
            record = {name: (row.get(fields.get(name, "")) or "").strip()
                      for name in ("company", "location", "url")}
            record.update({"title": (row.get(title_field) or "Untitled role").strip(),
                           "description": desc})
            jobs.append(record)
        if not jobs:
            raise ValueError("No jobs with descriptions found in the CSV")
        return jobs
    except csv.Error as exc:
        raise ValueError("Invalid CSV format") from exc
