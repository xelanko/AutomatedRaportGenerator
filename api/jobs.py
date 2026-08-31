"""
In-memory job manager. Report generation runs in a background thread
(via BackgroundTasks)

"""
import threading
import uuid
from datetime import datetime

from api.schemas import JobRecord, JobStatus, GenerateRequest
import config
import logger_setup
from data_sources import csv_source, sql_source
from pipeline import run_pipeline

log = logger_setup.get_logger(__name__)


class JobManager:
    def __init__(self):
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()
        self._durations: list[float] = []

    def create_job(self, req: GenerateRequest) -> JobRecord:
        job = JobRecord(job_id=str(uuid.uuid4()), status=JobStatus.QUEUED,
                         created_at=datetime.now(), request=req)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, status: JobStatus | None = None) -> list[JobRecord]:
        with self._lock:
            jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def metrics(self) -> dict:
        with self._lock:
            jobs = list(self._jobs.values())
            avg = sum(self._durations) / len(self._durations) if self._durations else None
        return {
            "total_jobs": len(jobs),
            "completed_jobs": sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
            "failed_jobs": sum(1 for j in jobs if j.status == JobStatus.FAILED),
            "running_jobs": sum(1 for j in jobs if j.status == JobStatus.RUNNING),
            "average_generation_seconds": avg,
        }

    def run_job(self, job_id: str):
        """Executed in a background thread. Never raises — errors are stored on the job."""
        job = self.get_job(job_id)
        if job is None:
            log.error(f"run_job called for unknown job_id={job_id}")
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        try:
            csv_path = config.DATA_DIR / (job.request.data_file or "sales.csv")
            if not csv_path.exists():
                raise FileNotFoundError(f"Data file not found: {csv_path}")

            records = csv_source.extract(csv_path)
            if job.request.use_sql_source:
                records += sql_source.extract()

            result = run_pipeline(
                raw_records=records,
                report_title=job.request.title,
                period_start=job.request.period_start,
                period_end=job.request.period_end,
                allowed_regions=set(job.request.allowed_regions),
                allowed_categories=set(job.request.allowed_categories),
                expected_total_revenue=job.request.expected_total_revenue,
            )
            metadata = result["metadata"]
            job.pdf_filename = result["pdf_path"].name
            job.xlsx_filename = result["xlsx_path"].name
            job.total_records = metadata.total_records
            job.validation_errors = metadata.validation_error_count
            job.validation_warnings = metadata.validation_warning_count
            job.issue_messages = [i.message for i in result["issues"]]
            job.status = JobStatus.COMPLETED
        except Exception as e:
            log.error(f"Job {job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
        finally:
            job.finished_at = datetime.now()
            if job.started_at:
                with self._lock:
                    self._durations.append((job.finished_at - job.started_at).total_seconds())


job_manager = JobManager()