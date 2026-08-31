"""Pydantic request/response models for the API layer."""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    title: str = "Monthly Sales Report"
    period_start: date
    period_end: date
    allowed_regions: list[str] = ["North", "South", "East", "West"]
    allowed_categories: list[str] = ["Electronics", "Furniture", "Clothing"]
    expected_total_revenue: Optional[float] = None
    use_sql_source: bool = True
    data_file: Optional[str] = Field(
        default=None, description="Filename in data/ to use instead of sales.csv"
    )


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    request: GenerateRequest
    error: Optional[str] = None
    pdf_filename: Optional[str] = None
    xlsx_filename: Optional[str] = None
    total_records: Optional[int] = None
    validation_errors: Optional[int] = None
    validation_warnings: Optional[int] = None
    issue_messages: list[str] = []


class JobList(BaseModel):
    count: int
    jobs: list[JobRecord]


class ReportFileInfo(BaseModel):
    filename: str
    size_bytes: int
    modified: datetime


class ReportList(BaseModel):
    count: int
    total: int
    page: int
    page_size: int
    reports: list[ReportFileInfo]


class UploadResponse(BaseModel):
    filename: str
    rows_detected: int
    saved_to: str


class MetricsResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    running_jobs: int
    total_reports_on_disk: int
    average_generation_seconds: Optional[float] = None