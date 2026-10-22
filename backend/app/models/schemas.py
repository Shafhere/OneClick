from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ProductInfo(BaseModel):
    name: str
    description: str
    source_urls: List[str] = Field(default_factory=list)


class ClaimEvidence(BaseModel):
    claim: str
    source_url: str
    quote: str = ""


class CompanyProfile(BaseModel):
    company_name: str
    industry: str = "Not found in collected evidence"
    headquarters: str = "Not found in collected evidence"
    founding_year: Optional[str] = None
    business_model: str = "Not found in collected evidence"
    target_audience: str = "Not found in collected evidence"
    pricing_model: str = "Not found in collected evidence"
    products: List[ProductInfo] = Field(default_factory=list)
    partnerships: List[str] = Field(default_factory=list)
    sustainability: List[str] = Field(default_factory=list)
    executive_summary: str
    known_gaps: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)
    claim_evidence: List[ClaimEvidence] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class ChatRequest(BaseModel):
    url: HttpUrl
    question: str = Field(min_length=2, max_length=1000)
