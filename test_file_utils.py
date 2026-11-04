import io
import pytest
from file_utils import load_jobs_csv, resume_to_text


def test_csv_with_alternate_columns():
    rows = load_jobs_csv(b'job_title,job_description,company\nIntern,"Python, SQL",Demo\n')
    assert rows[0]["title"] == "Intern"
    assert rows[0]["description"] == "Python, SQL"
    assert rows[0]["company"] == "Demo"


def test_csv_bad_headers():
    with pytest.raises(ValueError, match="title and description"):
        load_jobs_csv(b'role,content\nIntern,Python\n')


def test_csv_invalid_rows():
    with pytest.raises(ValueError, match="Invalid CSV row"):
        load_jobs_csv(b'title,description\nA,B,C\n')


def test_txt_upload():
    assert resume_to_text(io.BytesIO(b"Python SQL"), "resume.txt") == "Python SQL"


def test_unsupported_extension():
    with pytest.raises(ValueError, match="Supported resume"):
        resume_to_text(io.BytesIO(b""), "resume.png")
