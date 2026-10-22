
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ProductInfo(BaseModel):
    name: str
    description: str
    source_urls: List[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    company_name: str
    industry: str = "Not found"
    headquarters: str = "Not found"
    founding_year: Optional[str] = None
    business_model: str = "Not found"
    target_audience: str = "Not found"
    pricing_model: str = "Not disclosed publicly"
    products: List[ProductInfo] = Field(default_factory=list)
    partnerships: List[str] = Field(default_factory=list)
    sustainability: List[str] = Field(default_factory=list)
    executive_summary: str
    known_gaps: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class ChatRequest(BaseModel):
    url: HttpUrl
    question: str = Field(min_length=2, max_length=1000)
