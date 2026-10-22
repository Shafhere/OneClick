from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import logging

from app.models.schemas import AnalyzeRequest, ChatRequest
from app.core.crawler import scrape_website
from app.services.extractor import extract_company_data
from app.services.rag_service import index_website_content, query_website
from app.services.history_service import save_report, list_reports, get_report, delete_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("oneclick")
app = FastAPI(title="OneClick API", description="Evidence-first company intelligence research", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "oneclick-api", "version": "2.0.0"}


@app.post("/api/analyze")
def analyze_company(request: AnalyzeRequest):
    target_url = str(request.url)
    stage = "starting"

    try:
        stage = "crawling website"
        logger.info("Stage 1: crawling %s", target_url)
        pages = scrape_website(target_url)

        crawl_warnings = pages[0].pop("_crawl_warnings", []) if pages else []
        discovered_count = pages[0].pop("_discovered_url_count", len(pages)) if pages else len(pages)

        stage = "extracting company data"
        logger.info("Stage 2: extracting data from %s pages", len(pages))
        profile = extract_company_data(pages)

        stage = "indexing website content"
        logger.info("Stage 3: indexing website content")
        index_website_content(target_url, pages)

        result = {
            "url": target_url,
            "profile": profile.model_dump(),
            "pages_crawled": len(pages),
            "discovered_url_count": discovered_count,
            "crawl_warnings": crawl_warnings,
            "pages": [
                {
                    "url": page["url"],
                    "title": page.get("title", ""),
                    "characters": len(page.get("text", "")),
                }
                for page in pages
            ],
        }

        stage = "saving report"
        logger.info("Stage 4: saving report")
        result["report_id"] = save_report(target_url, result)

        logger.info("Analysis completed successfully for %s", target_url)
        return result

    except ValueError as exc:
        logger.exception("Validation or value error for %s", target_url)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        logger.exception("Analysis failed during '%s' for %s", stage, target_url)
        raise HTTPException(
            status_code=500,
            detail=f"Failed during {stage}: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/api/chat")
def chat_with_company(request: ChatRequest):
    try:
        return query_website(str(request.url), request.question.strip())
    except Exception as exc:
        logger.exception("Company chat failed")
        raise HTTPException(status_code=500, detail=f"Company chat failed ({type(exc).__name__}). Check backend logs.") from exc


@app.get("/api/history")
def research_history(limit: int = 50):
    return {"reports": list_reports(limit)}


@app.get("/api/history/{report_id}")
def research_history_detail(report_id: int):
    result = get_report(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Research report not found.")
    return result


@app.delete("/api/history/{report_id}")
def remove_history_item(report_id: int):
    if not delete_report(report_id):
        raise HTTPException(status_code=404, detail="Research report not found.")
    return {"deleted": True, "report_id": report_id}
