import os
import secrets
import logging
from decimal import Decimal
from datetime import datetime
from contextlib import contextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Reed Intel", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()


# ── Jinja2 filters ────────────────────────────────────────────────────────────

def _fdate(dt):
    if dt is None:
        return "—"
    try:
        return dt.strftime("%-d %b %Y")
    except Exception:
        return str(dt)


def _fdatetime(dt):
    if dt is None:
        return "—"
    try:
        return dt.strftime("%-d %b %Y, %H:%M")
    except Exception:
        return str(dt)


def _timeago(dt):
    if dt is None:
        return "Never"
    try:
        diff = datetime.utcnow() - dt.replace(tzinfo=None)
        secs = int(diff.total_seconds())
        if secs < 60:
            return "Just now"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return str(dt)


templates.env.filters["fdate"] = _fdate
templates.env.filters["fdatetime"] = _fdatetime
templates.env.filters["timeago"] = _timeago


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Database ──────────────────────────────────────────────────────────────────

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


def _norm(rows):
    result = []
    for row in rows:
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, Decimal):
                d[k] = float(v)
        result.append(d)
    return result


def fetch_data():
    d = {
        "sources": [],
        "editorial": [],
        "companies": [],
        "report": None,
        "stats": {"total_records": 0, "total_companies": 0, "new_items": 0, "active_sources": 0},
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
            d["sources"] = _norm(cur.fetchall())

            cur.execute("""
                SELECT queue_id::text, event_type, title, city, country, sector,
                       confidence_score, status, created_at, source_url, why_it_matters
                FROM editorial_queue
                ORDER BY created_at DESC
                LIMIT 30
            """)
            d["editorial"] = _norm(cur.fetchall())

            cur.execute("""
                SELECT legal_name, country, city, sector, confidence_score,
                       source_system, last_updated
                FROM companies
                ORDER BY confidence_score DESC NULLS LAST, last_updated DESC
                LIMIT 100
            """)
            d["companies"] = _norm(cur.fetchall())

            cur.execute("""
                SELECT report_id::text, week_start, week_end, title,
                       executive_summary, report_markdown, created_at
                FROM weekly_reports
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                d["report"] = dict(row)
                for k, v in d["report"].items():
                    if isinstance(v, Decimal):
                        d["report"][k] = float(v)

            for key, query in [
                ("total_records",  "SELECT COUNT(*)::int AS n FROM source_records"),
                ("total_companies","SELECT COUNT(*)::int AS n FROM companies"),
                ("new_items",      "SELECT COUNT(*)::int AS n FROM editorial_queue WHERE status = 'new'"),
                ("active_sources", "SELECT COUNT(*)::int AS n FROM sources WHERE active = true"),
            ]:
                cur.execute(query)
                d["stats"][key] = cur.fetchone()["n"]

            cur.close()
    except Exception as e:
        logger.error("Dashboard DB error: %s", e)
        d["error"] = str(e)
    return d


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, _: str = Depends(check_auth)):
    data = fetch_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        **data,
        "last_updated": datetime.utcnow().strftime("%-d %b %Y, %H:%M UTC"),
    })
