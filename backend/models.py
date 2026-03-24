from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="Company name, URL, or LinkedIn page")


class ReportSection(BaseModel):
    name: str
    title: str
    content: str
    order: int


class Report(BaseModel):
    id: str
    slug: str
    company: str
    input_query: str
    sections: dict  # {section_name: {content, order}}
    sources: list[str]
    is_complete: bool
    generated_at: datetime
    expires_at: datetime
    token_count: Optional[int] = None
    search_count: Optional[int] = None
    gen_time_ms: Optional[int] = None
