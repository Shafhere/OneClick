
from fastapi import FastAPI, HTTPException
import traceback

from app.models.schemas import AnalyzeRequest, ChatRequest
from app.core.crawler import scrape_website
from app.services.extractor import extract_company_data
from app.services.rag_service import (
    index_website_content,
    query_website,
)

app = FastAPI(
    title="OneClick API",
    description="AI-powered company intelligence research",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_company(request: AnalyzeRequest):
    try:
        pages = scrape_website(str(request.url))

        profile = extract_company_data(pages)

        index_website_content(str(request.url), pages)

        return {
            "profile": profile.model_dump(),
            "pages_crawled": len(pages),
            "pages": [
                {
                    "url": page["url"],
                    "title": page["title"],
                    "characters": len(page["text"]),
                }
                for page in pages
            ],
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Company analysis failed. Check the backend terminal."
        )   


@app.post("/api/chat")
def chat_with_company(request: ChatRequest):
    try:
        return query_website(
            str(request.url),
            request.question,
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The company chat request failed.",
        )
