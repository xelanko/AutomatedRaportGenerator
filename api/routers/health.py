"""Unauthenticated health/metrics — safe to expose to a load balancer."""
from fastapi import APIRouter
import config
from api.jobs import job_manager
from api.schemas import MetricsResponse

router = APIRouter(tags=["health"])


def _writable(path) -> bool:
    try:
        probe = path / ".write_check"
        probe.touch()
        probe.unlink()
        return True
    except Exception:
        return False


@router.get("/health")
def health():
    checks = {"output_dir_writable": _writable(config.OUTPUT_DIR),
              "data_dir_writable": _writable(config.DATA_DIR)}
    return {"status": "ok" if all(checks.values()) else "degraded", "checks": checks}


@router.get("/metrics", response_model=MetricsResponse)
def metrics():
    m = job_manager.metrics()
    m["total_reports_on_disk"] = len(
        [f for f in config.OUTPUT_DIR.iterdir() if f.is_file() and f.suffix in (".pdf", ".xlsx")]
    )
    return MetricsResponse(**m)