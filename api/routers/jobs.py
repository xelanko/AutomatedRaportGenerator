"""Check on async report-generation jobs."""
from fastapi import APIRouter, Depends, HTTPException
from api.security import require_api_key
from api.jobs import job_manager
from api.schemas import JobRecord, JobList, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=JobList)
def list_jobs(status: JobStatus | None = None):
    jobs = job_manager.list_jobs(status=status)
    return JobList(count=len(jobs), jobs=jobs)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job