"""
Data models used to normalize records coming from any source
(CSV, Excel, SQL, API, unstructured text) into one common schema,
plus the report metadata model.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SalesRecord(BaseModel):
    """Canonical internal record. All data sources are normalized into this."""
    record_id: str
    record_date: date
    region: str
    category: str
    revenue: float = Field(ge=0)
    quantity: int = Field(ge=0)
    source: str  # which pipeline produced this record

    @field_validator("revenue")
    @classmethod
    def revenue_must_be_reasonable(cls, v):
        if v > 10_000_000:
            raise ValueError(f"Revenue value {v} looks implausible (>10M in a single record)")
        return v


class FeedbackRecord(BaseModel):
    """Normalized unstructured record extracted from text/emails/logs."""
    record_id: str
    record_date: date
    region: Optional[str] = None
    sentiment: Optional[str] = None  # "positive" / "negative" / "neutral"
    excerpt: str
    source: str


class ValidationIssue(BaseModel):
    level: str  # "error" | "warning"
    field: Optional[str] = None
    message: str
    record_id: Optional[str] = None


class ReportMetadata(BaseModel):
    title: str
    generated_at: datetime = Field(default_factory=datetime.now)
    period_start: date
    period_end: date
    total_records: int
    validation_error_count: int = 0
    validation_warning_count: int = 0