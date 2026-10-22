# OneClick upgrade pack

## Included
- Crawler: extracts links before removing navigation, normalizes URLs, prioritizes useful company pages, enforces same-host crawling, and caps page size/configuration.
- RAG: hybrid semantic + keyword retrieval using reciprocal-rank fusion; answer prompts request inline source markers; API returns evidence excerpts for inspection.
- Dashboard: adds JSON report download and expandable retrieved-evidence inspection.
- Tests: starter unit tests for crawler parsing, URL normalization, chunking and tokenization.

## Important
- Keep your local `.env` and `backend/data/chroma` folder. They are not included in this pack.
- Before replacing files, commit your working project or make a backup.
- The crawler intentionally skips redirects and fails closed when `robots.txt` cannot be fetched. Some sites may therefore return fewer pages.
- This is a meaningful baseline upgrade, not a full production security audit. JS-rendered sites, external competitor research, report-history database, true cross-encoder reranking, and authenticated access are still future milestones.

## Run from Windows CMD
From project root:

```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

Backend (new CMD window):

```cmd
cd /d "%USERPROFILE%\Desktop\OneClick\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Frontend (another CMD window, from root):

```cmd
cd /d "%USERPROFILE%\Desktop\OneClick"
.venv\Scripts\activate
streamlit run frontend/app.py
```

Run tests from project root:

```cmd
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```
