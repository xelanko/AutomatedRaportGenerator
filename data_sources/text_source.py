"""
Unstructured data source: plain-text/log/email files.
Extracts simple sentiment + region tags using lightweight keyword rules
(swap this out for an NLP/LLM pipeline if you want deeper analysis).
"""
import re
from pathlib import Path
from datetime import date
import logger_setup

log = logger_setup.get_logger(__name__)

POSITIVE_WORDS = {"great", "excellent", "love", "happy", "good", "fast", "helpful"}
NEGATIVE_WORDS = {"bad", "slow", "terrible", "hate", "broken", "delay", "poor"}
REGION_PATTERN = re.compile(r"\b(North|South|East|West)\b", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def _classify_sentiment(text_block: str) -> str:
    words = set(re.findall(r"[a-zA-Z']+", text_block.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def extract(folder_path: Path, default_date: date = None) -> list[dict]:
    log.info(f"Extracting unstructured text data from {folder_path}")
    if not folder_path.exists():
        raise FileNotFoundError(f"Text folder not found: {folder_path}")

    records = []
    for i, file in enumerate(sorted(folder_path.glob("*.txt"))):
        content = file.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue

        date_match = DATE_PATTERN.search(content)
        region_match = REGION_PATTERN.search(content)

        records.append({
            "record_id": f"text-{i}-{file.stem}",
            "record_date": date_match.group(0) if date_match else (default_date or date.today()),
            "region": region_match.group(0).title() if region_match else None,
            "sentiment": _classify_sentiment(content),
            "excerpt": content[:280],
            "source": "text",
        })
    log.info(f"Extracted {len(records)} feedback records from text files")
    return records