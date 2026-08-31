"""
Structured data source: SQL database via SQLAlchemy.
Supports incremental extraction using a `since` watermark on a date column.
"""
from datetime import date
from sqlalchemy import create_engine, text
import config
import logger_setup

log = logger_setup.get_logger(__name__)


def extract(query: str = None, since: date = None) -> list[dict]:
    engine = create_engine(config.DB_URL)

    if query is None:
        query = "SELECT id, sale_date, region, category, revenue, quantity FROM sales"
        if since:
            query += " WHERE sale_date >= :since"

    log.info(f"Running SQL extraction (since={since})")
    with engine.connect() as conn:
        params = {"since": since} if since else {}
        result = conn.execute(text(query), params)
        rows = result.mappings().all()

    records = []
    for row in rows:
        records.append({
            "record_id": f"sql-{row.get('id')}",
            "record_date": row.get("sale_date"),
            "region": row.get("region"),
            "category": row.get("category"),
            "revenue": row.get("revenue"),
            "quantity": row.get("quantity"),
            "source": "sql",
        })
    log.info(f"Extracted {len(records)} records from SQL")
    return records


def create_sample_table_and_data():
    """Helper to set up a demo SQLite table so the example works out of the box."""
    engine = create_engine(config.DB_URL)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                sale_date DATE,
                region TEXT,
                category TEXT,
                revenue REAL,
                quantity INTEGER
            )
        """))
        existing = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar()
        if existing == 0:
            sample = [
                (1, "2025-06-01", "North", "Electronics", 12000.50, 34),
                (2, "2025-06-03", "South", "Furniture", 8000.00, 12),
                (3, "2025-06-10", "East", "Electronics", 15500.75, 41),
            ]
            conn.execute(
                text("INSERT INTO sales (id, sale_date, region, category, revenue, quantity) "
                     "VALUES (:id, :sale_date, :region, :category, :revenue, :quantity)"),
                [dict(zip(("id", "sale_date", "region", "category", "revenue", "quantity"), row))
                 for row in sample]
            )