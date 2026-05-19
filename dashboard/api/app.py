import os
import secrets
import logging
from decimal import Decimal
from datetime import datetime
from contextlib import contextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)
security = HTTPBasic()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    expected_user = os.getenv("DASHBOARD_USER", "reedintel")
    expected_pass = os.getenv("DASHBOARD_PASS", "intel2024")
    ok_user = secrets.compare_digest(credentials.username.encode(), expected_user.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), expected_pass.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": 'Basic realm="Reed Intel"'},
        )
    return credentials.username


@contextmanager
def get_db():
    conn = psycopg2.connect(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        dbname=os.getenv("DATABASE_NAME", "reedintel"),
        user=os.getenv("DATABASE_USER", "reedadmin"),
        password=os.getenv("DATABASE_PASSWORD", ""),
        sslmode=os.getenv("DATABASE_SSLMODE", "require"),
        connect_timeout=10,
    )
    try:
        yield conn
    finally:
        conn.close()


def norm(rows):
    result = []
    for row in rows:
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, Decimal):
                d[k] = float(v)
            elif hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        result.append(d)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
async def get_dashboard(_: str = Depends(check_auth)):
    data = {
        "sources": [],
        "editorial": [],
        "companies": [],
        "report": None,
        "stats": {"total_records": 0, "total_companies": 0, "new_items": 0, "active_sources": 0},
        "last_updated": datetime.utcnow().isoformat(),
        "error": None,
    }
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute("""
                SELECT s.source_name, s.source_type, s.city, s.country, s.active,
                       MAX(sr.fetched_at) AS last_fetched,
                       COUNT(sr.record_id)::int AS record_count
                FROM sources s
                LEFT JOIN source_records sr ON s.source_name = sr.source_name
                GROUP BY s.source_id, s.source_name, s.source_type, s.city, s.country, s.active
                ORDER BY s.country, s.city
            """)
            data["sources"] = norm(cur.fetchall())

            cur.execute("""
                SELECT queue_id::text, event_type, title, city, country, sector,
                       confidence_score, status, created_at, source_url, why_it_matters
                FROM editorial_queue
                ORDER BY created_at DESC
                LIMIT 30
            """)
            data["editorial"] = norm(cur.fetchall())

            cur.execute("""
                SELECT legal_name, country, city, sector, confidence_score,
                       source_system, last_updated
                FROM companies
                ORDER BY confidence_score DESC NULLS LAST, last_updated DESC
                LIMIT 100
            """)
            data["companies"] = norm(cur.fetchall())

            cur.execute("""
                SELECT report_id::text, week_start, week_end, title,
                       executive_summary, report_markdown, created_at
                FROM weekly_reports
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, Decimal):
                        d[k] = float(v)
                    elif hasattr(v, "isoformat"):
                        d[k] = v.isoformat()
                data["report"] = d

            for key, query in [
                ("total_records",   "SELECT COUNT(*)::int AS n FROM source_records"),
                ("total_companies", "SELECT COUNT(*)::int AS n FROM companies"),
                ("new_items",       "SELECT COUNT(*)::int AS n FROM editorial_queue WHERE status = 'new'"),
                ("active_sources",  "SELECT COUNT(*)::int AS n FROM sources WHERE active = true"),
            ]:
                cur.execute(query)
                data["stats"][key] = cur.fetchone()["n"]

            cur.close()
    except Exception as e:
        logger.error("DB error: %s", e)
        data["error"] = str(e)

    return JSONResponse(content=data)


# Serve React SPA — must be defined after all API routes
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_root(_: str = Depends(check_auth)):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str, _: str = Depends(check_auth)):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
