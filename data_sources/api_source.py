"""
Structured data source: REST API with retry/backoff logic.
"""
import time
import requests
import config
import logger_setup

log = logger_setup.get_logger(__name__)


def extract(endpoint: str = "sales", params: dict = None, max_retries: int = 3) -> list[dict]:
    url = f"{config.API_BASE_URL.rstrip('/')}/{endpoint}"
    headers = {"Authorization": f"Bearer {config.API_KEY}"} if config.API_KEY else {}

    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"Calling API {url} (attempt {attempt}/{max_retries})")
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
            break
        except requests.RequestException as e:
            log.warning(f"API call failed: {e}")
            if attempt == max_retries:
                log.error("API extraction failed after max retries")
                raise
            time.sleep(2 ** attempt)  # exponential backoff

    records = []
    for i, item in enumerate(payload.get("data", [])):
        records.append({
            "record_id": f"api-{item.get('id', i)}",
            "record_date": item.get("date"),
            "region": item.get("region"),
            "category": item.get("category"),
            "revenue": item.get("revenue"),
            "quantity": item.get("quantity"),
            "source": "api",
        })
    log.info(f"Extracted {len(records)} records from API")
    return records