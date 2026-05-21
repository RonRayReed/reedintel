import os
import json
import hashlib
import logging
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env if present (local dev only — no-op in production)
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager, contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(run_prozorro, "interval", minutes=30, next_run_time=datetime.utcnow())
    scheduler.start()
    logger.info("Scheduler started — ProZorro runs every 30 minutes")
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
_origins = os.getenv("ALLOWED_ORIGINS", "")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins.split(",") if _origins else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



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


# ── ProZorro ingestion ────────────────────────────────────────────────────────

PROZORRO_BASE = "https://public.api.openprocurement.org/api/2.5/tenders"
KEYWORDS = ["reconstruction", "repair", "road", "bridge", "energy", "hospital", "port", "infrastructure"]
CITY_TERMS = {
    "Kyiv": ["kyiv", "київ"],
    "Lviv": ["lviv", "львів"],
    "Odesa": ["odesa", "одеса", "odessa"],
}


def _infer_city(text):
    t = (text or "").lower()
    for city, terms in CITY_TERMS.items():
        if any(term in t for term in terms):
            return city
    return None


def _infer_sector(text):
    t = (text or "").lower()
    if any(w in t for w in ["road", "bridge", "дорога", "міст"]):      return "Infrastructure"
    if any(w in t for w in ["energy", "electric", "power", "енерг"]):   return "Energy"
    if any(w in t for w in ["hospital", "medical", "clinic", "лікар"]): return "Healthcare"
    if any(w in t for w in ["port", "harbor", "terminal", "порт"]):     return "Ports & Logistics"
    return "Government Procurement"


def _content_hash(payload):
    if not isinstance(payload, str):
        payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def run_prozorro():
    logger.info("ProZorro fetch started")
    since = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    try:
        resp = requests.get(PROZORRO_BASE, params={"offset": since, "descending": "1"}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error("ProZorro API error: %s", e)
        return 0

    tenders = resp.json().get("data", [])
    logger.info("ProZorro: %d tenders retrieved", len(tenders))
    created = 0

    try:
        with get_db() as conn:
            cur = conn.cursor()
            for item in tenders:
                tender_id = item.get("id")
                if not tender_id:
                    continue
                try:
                    detail = requests.get(f"{PROZORRO_BASE}/{tender_id}", timeout=30).json().get("data", {})
                except Exception:
                    continue

                title = detail.get("title", "")
                combined = f"{title} {detail.get('description', '')}"
                raw = json.dumps(detail, ensure_ascii=False)
                h = _content_hash(raw)

                cur.execute(
                    "SELECT record_id FROM source_records WHERE source_name='ProZorro' AND content_hash=%s LIMIT 1",
                    (h,)
                )
                if cur.fetchone():
                    continue

                cur.execute("""
                    INSERT INTO source_records (source_name, source_url, external_id, raw_json, content_hash)
                    VALUES ('ProZorro', %s, %s, %s::jsonb, %s)
                """, (f"{PROZORRO_BASE}/{tender_id}", tender_id, raw, h))
                conn.commit()

                city = _infer_city(combined)
                sector = _infer_sector(combined)
                value = detail.get("value", {}).get("amount")

                if city or any(k in combined.lower() for k in KEYWORDS) or (value and value > 250_000):
                    cur.execute("""
                        INSERT INTO editorial_queue
                            (event_type, title, city, country, sector, source_url, why_it_matters, confidence_score)
                        VALUES ('procurement_tender', %s, %s, 'Ukraine', %s, %s, %s, 0.75)
                    """, (
                        title[:500] or f"Tender {tender_id}",
                        city or "Ukraine",
                        sector,
                        f"{PROZORRO_BASE}/{tender_id}",
                        f"Public procurement detected. Estimated value: {value}.",
                    ))
                    conn.commit()
                    created += 1

            cur.close()
    except Exception as e:
        logger.error("ProZorro DB write error: %s", e)

    logger.info("ProZorro fetch done: %d new signals", created)
    return created


# ── API routes ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth")
async def auth(req: LoginRequest):
    if req.username == os.getenv("DASH_USER", "admin") and \
       req.password == os.getenv("DASH_PASSWORD", "changeme"):
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/fetch-now")
async def fetch_now():
    import asyncio
    count = await asyncio.get_event_loop().run_in_executor(None, run_prozorro)
    return {"status": "done", "signals_created": count}


@app.get("/api/dashboard")
async def get_dashboard():
    data = {
        "sources": [], "editorial": [], "companies": [], "report": None,
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
                ORDER BY created_at DESC LIMIT 50
            """)
            data["editorial"] = norm(cur.fetchall())

            cur.execute("""
                SELECT legal_name, country, city, sector, confidence_score,
                       source_system, last_updated
                FROM companies
                ORDER BY confidence_score DESC NULLS LAST, last_updated DESC LIMIT 100
            """)
            data["companies"] = norm(cur.fetchall())

            cur.execute("""
                SELECT report_id::text, week_start, week_end, title,
                       executive_summary, report_markdown, created_at
                FROM weekly_reports ORDER BY created_at DESC LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, Decimal): d[k] = float(v)
                    elif hasattr(v, "isoformat"): d[k] = v.isoformat()
                data["report"] = d

            for key, query in [
                ("total_records",   "SELECT COUNT(*)::int AS n FROM source_records"),
                ("total_companies", "SELECT COUNT(*)::int AS n FROM companies"),
                ("new_items",       "SELECT COUNT(*)::int AS n FROM editorial_queue WHERE status='new'"),
                ("active_sources",  "SELECT COUNT(*)::int AS n FROM sources WHERE active=true"),
            ]:
                cur.execute(query)
                data["stats"][key] = cur.fetchone()["n"]

            cur.close()
    except Exception as e:
        logger.error("Dashboard DB error: %s", e)
        data["error"] = str(e)

    return JSONResponse(content=data)
