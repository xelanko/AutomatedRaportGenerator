"""
Central configuration for the Automated Report Generator.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Directories
DATA_DIR = Path(os.getenv("REPORT_DATA_DIR", BASE_DIR / "data"))
OUTPUT_DIR = Path(os.getenv("REPORT_OUTPUT_DIR", BASE_DIR / "output"))
LOG_DIR = Path(os.getenv("REPORT_LOG_DIR", BASE_DIR / "logs"))

for directory in (DATA_DIR, OUTPUT_DIR, LOG_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Database (optional SQL source)
DB_URL = os.getenv("REPORT_DB_URL", "sqlite:///" + str(BASE_DIR / "sample.db"))

# API source (optional)
API_BASE_URL = os.getenv("REPORT_API_BASE_URL", "")
API_KEY = os.getenv("REPORT_API_KEY", "")

# Validation thresholds
OUTLIER_Z_SCORE_THRESHOLD = float(os.getenv("OUTLIER_Z_SCORE_THRESHOLD", "3.0"))
RECONCILIATION_TOLERANCE = float(os.getenv("RECONCILIATION_TOLERANCE", "0.01"))  # 1%

# Logging
LOG_LEVEL = os.getenv("REPORT_LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "report_generator.log"

# Scheduling
DEFAULT_SCHEDULE_CRON = os.getenv("REPORT_SCHEDULE_CRON", "0 7 * * MON")  # 7am every Monday