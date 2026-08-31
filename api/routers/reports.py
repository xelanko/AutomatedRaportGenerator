"""Async report generation plus report-file management."""
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from starlette import status

import config
from api.security import require_api_key
from api.jobs import job_manager
from api.schemas import GenerateRequest, JobRecord, ReportList, ReportFileInfo

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=JobRecord, status_code=status.HTTP_202_ACCEPTED)
def generate_report(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Queue a generation job and return immediately with a job_id.
    Poll GET /jobs/{job_id}; once status == completed, download via GET /reports/{filename}."""
    job = job_manager.create_job(req)
    background_tasks.add_task(job_manager.run_job, job.job_id)
    return job


def _resolve_safe_path(filename: str):
    file_path = (config.OUTPUT_DIR / filename).resolve()
    if config.OUTPUT_DIR.resolve() not in file_path.parents:
        raise HTTPException(400, "Invalid filename")
    return file_path


@router.get("", response_model=ReportList)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="modified_desc",
                       pattern="^(modified_desc|modified_asc|name_asc|name_desc)$"),
):
    files = [f for f in config.OUTPUT_DIR.iterdir() if f.is_file() and f.suffix in (".pdf", ".xlsx")]
    key_fn = {
        "modified_desc": lambda f: -f.stat().st_mtime,
        "modified_asc": lambda f: f.stat().st_mtime,
        "name_asc": lambda f: f.name,
        "name_desc": lambda f: f.name,
    }[sort]
    files = sorted(files, key=key_fn, reverse=(sort == "name_desc"))

    total = len(files)
    start = (page - 1) * page_size
    page_files = files[start:start + page_size]

    return ReportList(
        count=len(page_files), total=total, page=page, page_size=page_size,
        reports=[ReportFileInfo(filename=f.name, size_bytes=f.stat().st_size,
                                 modified=datetime.fromtimestamp(f.stat().st_mtime))
                 for f in page_files],
    )


@router.get("/{filename}")
def download_report(filename: str):
    file_path = _resolve_safe_path(filename)
    if not file_path.exists():
        raise HTTPException(404, "Report not found")
    media_type = ("application/pdf" if file_path.suffix == ".pdf"
                  else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return FileResponse(path=file_path, filename=file_path.name, media_type=media_type)


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(filename: str):
    file_path = _resolve_safe_path(filename)
    if not file_path.exists():
        raise HTTPException(404, "Report not found")
    file_path.unlink()