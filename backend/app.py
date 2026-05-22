import os
import json
import hashlib
import logging
import requests
import feedparser
from deep_translator import GoogleTranslator
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

scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": None, "coalesce": True})

@asynccontextmanager
async def lifespan(app: FastAPI):
    now = datetime.now()  # local time — avoids timezone mismatch with APScheduler
    scheduler.add_job(run_prozorro,     "interval", minutes=30, next_run_time=now)
    scheduler.add_job(run_mtender,      "interval", minutes=60, next_run_time=now)
    scheduler.add_job(run_rss_feeds,    "interval", minutes=30, next_run_time=now)
    scheduler.add_job(run_opendatabot,  "interval", minutes=60, next_run_time=now)
    scheduler.add_job(run_anaf,         "interval", hours=6,    next_run_time=now)
    scheduler.add_job(run_ckan_portals, "interval", hours=6,    next_run_time=now)
    scheduler.add_job(run_ai_drafting,  "interval", minutes=15, next_run_time=now + timedelta(seconds=30))
    scheduler.start()
    logger.info("Scheduler started — 6 connectors + AI drafting active")
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


# ── Translation ──────────────────────────────────────────────────────────────

LANG_MAP = {"UK": "uk", "RO": "ro"}


def _is_likely_english(text: str) -> bool:
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return True
    return sum(1 for c in letters if ord(c) < 128) / len(letters) > 0.85


def _translate(text: str, source_lang: str = None) -> str:
    """Translate text to English via Google Translate (free, no key needed)."""
    if not text or not text.strip():
        return text
    # Only skip when auto-detecting — Romanian looks Latin but isn't English
    if source_lang is None and _is_likely_english(text):
        return text
    src = LANG_MAP.get(source_lang, "auto") if source_lang else "auto"
    try:
        return GoogleTranslator(source=src, target="en").translate(text[:4999]) or text
    except Exception as e:
        logger.warning("Translation failed: %s", e)
        return text


def _translate_pair(title: str, summary: str, source_lang: str = None) -> tuple:
    return _translate(title, source_lang), _translate(summary, source_lang)


def _parse_draft(text: str) -> dict:
    """Extract Headline/Deck/Body/Editor Notes sections from GPT response."""
    result = {"headline": "", "deck": "", "body": "", "editor_notes": ""}
    current_key = None
    current_lines: list[str] = []

    def _flush():
        if current_key:
            result[current_key] = "\n".join(current_lines).strip()

    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("headline:"):
            _flush(); current_key = "headline"
            current_lines = [line.strip()[len("headline:"):].strip()]
        elif low.startswith("deck:"):
            _flush(); current_key = "deck"
            current_lines = [line.strip()[len("deck:"):].strip()]
        elif low.startswith("body:"):
            _flush(); current_key = "body"
            rest = line.strip()[len("body:"):].strip()
            current_lines = [rest] if rest and not rest[:3].isdigit() else []
        elif low.startswith("editor verification notes:") or low.startswith("editor notes:"):
            _flush(); current_key = "editor_notes"
            idx = line.index(":") + 1
            current_lines = [line[idx:].strip()]
        elif current_key:
            current_lines.append(line.strip())

    _flush()
    return result


_AI_SYSTEM_PROMPT = (
    "You are Reed Intel's business-news drafting assistant. "
    "Use only the facts provided in the prompt. "
    "Do not invent quotes, people, dollar values, causes, or relationships. "
    "Write clearly for executives, investors, lawyers, bankers, and business owners. "
    "Mark any uncertainty as 'requires editor verification'."
)

_AI_USER_TEMPLATE = """Create a Reed Intel business brief from the following structured facts.

City: {city}
Country: {country}
Sector: {sector}
Event Type: {event_type}
Title: {title}
Why it matters: {why_it_matters}
Source URL: {source_url}
Confidence Score: {confidence_score}

Required format:
Headline:
Deck:
Body: 250-400 words
Editor Verification Notes:
"""


def _generate_draft_for_item(item: dict) -> dict:
    """Call OpenAI and return parsed draft sections."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    client = OpenAI(api_key=api_key)
    prompt = _AI_USER_TEMPLATE.format(
        city=item.get("city", ""),
        country=item.get("country", ""),
        sector=item.get("sector", ""),
        event_type=item.get("event_type", ""),
        title=item.get("title", ""),
        why_it_matters=item.get("why_it_matters", ""),
        source_url=item.get("source_url", ""),
        confidence_score=item.get("confidence_score", ""),
    )
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": _AI_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
    )
    return _parse_draft(response.choices[0].message.content)


def _insert_editorial(cur, conn, event_type, title, city, country, sector,
                      source_url, why_it_matters, confidence_score, source_lang=None):
    """Translate then insert one editorial queue item."""
    title, why_it_matters = _translate_pair(title, why_it_matters, source_lang=source_lang)
    cur.execute("""
        INSERT INTO editorial_queue
            (event_type, title, city, country, sector, source_url, why_it_matters, confidence_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (event_type, title, city, country, sector, source_url, why_it_matters, confidence_score))
    conn.commit()


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
                    _insert_editorial(cur, conn,
                        event_type="procurement_tender",
                        title=title[:500] or f"Tender {tender_id}",
                        city=city or "Ukraine",
                        country="Ukraine",
                        sector=sector,
                        source_url=f"{PROZORRO_BASE}/{tender_id}",
                        why_it_matters=f"Public procurement detected. Estimated value: {value}.",
                        confidence_score=0.75,
                        source_lang="UK",
                    )
                    created += 1

            cur.close()
    except Exception as e:
        logger.error("ProZorro DB write error: %s", e)

    logger.info("ProZorro fetch done: %d new signals", created)
    return created


# ── MTender (Moldova) ─────────────────────────────────────────────────────────

# MTender's OpenProcurement API is no longer publicly accessible.
# Falling back to Moldova's open data CKAN portal (date.gov.md).
ANSC_CKAN_URL = "https://date.gov.md/api/3/action/package_search"
MTENDER_KEYWORDS = ["achizitii", "licitatie", "tender", "contract", "constructii", "energie", "infrastructura"]


def run_mtender():
    logger.info("MTender/ANSC fetch started")
    try:
        resp = requests.get(ANSC_CKAN_URL, params={"q": "achizitii publice tender", "rows": 100}, timeout=30)
        resp.raise_for_status()
        packages = resp.json().get("result", {}).get("results", [])
    except Exception as e:
        logger.error("MTender/ANSC error: %s", e)
        return 0

    created = 0
    try:
        with get_db() as conn:
            cur = conn.cursor()
            for pkg in packages:
                pkg_id = pkg.get("id")
                title = pkg.get("title", "")
                raw = json.dumps(pkg, ensure_ascii=False)
                h = _content_hash(raw)

                cur.execute("SELECT record_id FROM source_records WHERE source_name='MTender' AND content_hash=%s LIMIT 1", (h,))
                if cur.fetchone():
                    continue

                cur.execute("""
                    INSERT INTO source_records (source_name, source_url, external_id, raw_json, content_hash)
                    VALUES ('MTender', %s, %s, %s::jsonb, %s)
                """, (pkg.get("url") or ANSC_CKAN_URL, pkg_id, raw, h))
                conn.commit()

                if any(kw in title.lower() for kw in MTENDER_KEYWORDS):
                    _insert_editorial(cur, conn,
                        event_type="moldova_procurement",
                        title=title[:500] or f"ANSC Dataset {pkg_id}",
                        city="Chisinau",
                        country="Moldova",
                        sector="Government Procurement",
                        source_url=pkg.get("url") or ANSC_CKAN_URL,
                        why_it_matters="Moldova public procurement dataset on date.gov.md.",
                        confidence_score=0.60,
                        source_lang="RO",
                    )
                    created += 1
            cur.close()
    except Exception as e:
        logger.error("MTender DB error: %s", e)

    logger.info("MTender/ANSC fetch done: %d new signals", created)
    return created


# ── ANAF / Romania Open Data ──────────────────────────────────────────────────

ANAF_OPENDATA_URL = "https://data.gov.ro/api/3/action/package_search"
ANAF_KEYWORDS = ["achizitii", "licitatie", "contract", "investitie", "infrastructura"]


def run_anaf():
    logger.info("ANAF/RO-OpenData fetch started")
    try:
        resp = requests.get(ANAF_OPENDATA_URL, params={"q": "achizitii publice licitatie", "rows": 50}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error("ANAF/RO-OpenData error: %s", e)
        return 0

    packages = resp.json().get("result", {}).get("results", [])
    created = 0
    try:
        with get_db() as conn:
            cur = conn.cursor()
            for pkg in packages:
                pkg_id = pkg.get("id")
                title = pkg.get("title", "")
                raw = json.dumps(pkg, ensure_ascii=False)
                h = _content_hash(raw)

                cur.execute("SELECT record_id FROM source_records WHERE source_name='ANAF' AND content_hash=%s LIMIT 1", (h,))
                if cur.fetchone():
                    continue

                cur.execute("""
                    INSERT INTO source_records (source_name, source_url, external_id, raw_json, content_hash)
                    VALUES ('ANAF', %s, %s, %s::jsonb, %s)
                """, (pkg.get("url") or "https://data.gov.ro", pkg_id, raw, h))
                conn.commit()

                if any(kw in title.lower() for kw in ANAF_KEYWORDS):
                    _insert_editorial(cur, conn,
                        event_type="romania_opendata",
                        title=title[:500] or f"RO Dataset {pkg_id}",
                        city="Bucharest",
                        country="Romania",
                        sector="Government Procurement",
                        source_url=pkg.get("url") or "https://data.gov.ro",
                        why_it_matters="Romanian public procurement dataset published on data.gov.ro.",
                        confidence_score=0.55,
                        source_lang="RO",
                    )
                    created += 1
            cur.close()
    except Exception as e:
        logger.error("ANAF DB error: %s", e)

    logger.info("ANAF fetch done: %d new signals", created)
    return created


# ── OpenDataBot (Ukrainian company enrichment) ────────────────────────────────

OPENDATABOT_URL = "https://opendatabot.ua/api/v2/company"


def run_opendatabot():
    api_key = os.getenv("OPENDATABOT_API_KEY", "")
    if not api_key:
        logger.info("OpenDataBot skipped — OPENDATABOT_API_KEY not set")
        return 0

    logger.info("OpenDataBot enrichment started")
    enriched = 0
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT raw_json->'procuringEntity'->'identifier'->>'id' AS edrpou
                FROM source_records
                WHERE source_name = 'ProZorro'
                  AND raw_json->'procuringEntity'->'identifier'->>'scheme' = 'UA-EDR'
                  AND raw_json->'procuringEntity'->'identifier'->>'id' IS NOT NULL
                  AND raw_json->'procuringEntity'->'identifier'->>'id' NOT IN (
                      SELECT registration_number FROM companies
                      WHERE source_system = 'OpenDataBot' AND registration_number IS NOT NULL
                  )
                LIMIT 20
            """)
            codes = [row[0] for row in cur.fetchall() if row[0]]

            for edrpou in codes:
                try:
                    r = requests.get(f"{OPENDATABOT_URL}/{edrpou}",
                                     headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
                    r.raise_for_status()
                    payload = r.json()
                    name = payload.get("name") or payload.get("full_name") or edrpou
                    raw = json.dumps(payload, ensure_ascii=False)
                    h = _content_hash(raw)

                    cur.execute("SELECT record_id FROM source_records WHERE source_name='OpenDataBot' AND content_hash=%s LIMIT 1", (h,))
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO source_records (source_name, source_url, external_id, raw_json, content_hash)
                            VALUES ('OpenDataBot', %s, %s, %s::jsonb, %s)
                        """, (f"{OPENDATABOT_URL}/{edrpou}", edrpou, raw, h))

                    cur.execute("""
                        INSERT INTO companies (legal_name, registration_number, country, source_system, confidence_score, last_updated)
                        VALUES (%s, %s, 'Ukraine', 'OpenDataBot', 0.90, NOW())
                        ON CONFLICT (country, registration_number)
                        DO UPDATE SET legal_name        = EXCLUDED.legal_name,
                                      source_system     = EXCLUDED.source_system,
                                      confidence_score  = GREATEST(companies.confidence_score, EXCLUDED.confidence_score),
                                      last_updated      = NOW()
                    """, (name, edrpou))
                    conn.commit()
                    enriched += 1
                except Exception as e:
                    logger.warning("OpenDataBot enrichment error for %s: %s", edrpou, e)

            cur.close()
    except Exception as e:
        logger.error("OpenDataBot DB error: %s", e)

    logger.info("OpenDataBot enrichment done: %d companies", enriched)
    return enriched


# ── CKAN city portals ─────────────────────────────────────────────────────────

CKAN_PORTALS = [
    ("Lviv Open Data",   "https://opendata.city-adm.lviv.ua", ""),
    ("Kyiv Open Data",   "https://data.kyivcity.gov.ua",      ""),
    ("Romania OpenData", "https://data.gov.ro",                "achizitii publice"),
]


def run_ckan_portals():
    logger.info("CKAN portals fetch started")
    total = 0
    try:
        with get_db() as conn:
            cur = conn.cursor()
            for source_name, base_url, query in CKAN_PORTALS:
                try:
                    resp = requests.get(
                        base_url.rstrip("/") + "/api/3/action/package_search",
                        params={"q": query, "rows": 100}, timeout=30,
                    )
                    resp.raise_for_status()
                    packages = resp.json().get("result", {}).get("results", [])
                except Exception as e:
                    logger.warning("CKAN error for %s: %s", source_name, e)
                    continue

                for pkg in packages:
                    raw = json.dumps(pkg, ensure_ascii=False)
                    h = _content_hash(raw)
                    cur.execute("SELECT record_id FROM source_records WHERE source_name=%s AND content_hash=%s LIMIT 1",
                                (source_name, h))
                    if cur.fetchone():
                        continue
                    cur.execute("""
                        INSERT INTO source_records (source_name, source_url, external_id, raw_json, content_hash)
                        VALUES (%s, %s, %s, %s::jsonb, %s)
                    """, (source_name, pkg.get("url") or base_url, pkg.get("id"), raw, h))
                    conn.commit()
                    total += 1
            cur.close()
    except Exception as e:
        logger.error("CKAN DB error: %s", e)

    logger.info("CKAN portals done: %d new records", total)
    return total


# ── RSS feeds ─────────────────────────────────────────────────────────────────

RSS_FEEDS = [
    {"source_name": "Lviv IT Cluster",      "url": "https://itcluster.lviv.ua/en/feed/",           "city": "Lviv",      "country": "Ukraine"},
    {"source_name": "Interfax Ukraine",     "url": "https://en.interfax.com.ua/news/economic.rss",  "city": "Kyiv",      "country": "Ukraine"},
    {"source_name": "Moldova Newsmaker",    "url": "https://newsmaker.md/rss",                      "city": "Chisinau",  "country": "Moldova"},
    {"source_name": "ZDG Moldova",          "url": "https://www.zdg.md/feed/",                      "city": "Chisinau",  "country": "Moldova"},
    {"source_name": "Romania Economica",    "url": "https://www.economica.net/rss",                  "city": "Bucharest", "country": "Romania"},
]


def run_rss_feeds():
    logger.info("RSS feeds fetch started")
    total = 0
    try:
        with get_db() as conn:
            cur = conn.cursor()
            for feed_conf in RSS_FEEDS:
                try:
                    feed = feedparser.parse(feed_conf["url"])
                except Exception as e:
                    logger.warning("RSS parse error for %s: %s", feed_conf["source_name"], e)
                    continue

                for entry in feed.entries:
                    title    = entry.get("title", "")
                    link     = entry.get("link", "")
                    summary  = entry.get("summary", "")
                    entry_id = entry.get("id") or link
                    raw_text = f"{title}\n{summary}"
                    h = _content_hash(raw_text)

                    cur.execute("SELECT record_id FROM source_records WHERE source_name=%s AND content_hash=%s LIMIT 1",
                                (feed_conf["source_name"], h))
                    if cur.fetchone():
                        continue

                    cur.execute("""
                        INSERT INTO source_records (source_name, source_url, external_id, raw_text, content_hash)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (feed_conf["source_name"], link, entry_id, raw_text, h))

                    _insert_editorial(cur, conn,
                        event_type="rss_article",
                        title=title[:500],
                        city=feed_conf["city"],
                        country=feed_conf["country"],
                        sector="General Business",
                        source_url=link,
                        why_it_matters=f"RSS signal from {feed_conf['source_name']}.",
                        confidence_score=0.50,
                    )
                    total += 1
            cur.close()
    except Exception as e:
        logger.error("RSS DB error: %s", e)

    logger.info("RSS feeds done: %d new signals", total)
    return total


# ── AI drafting ──────────────────────────────────────────────────────────────

def run_ai_drafting():
    if not os.getenv("OPENAI_API_KEY", ""):
        logger.info("AI drafting skipped — OPENAI_API_KEY not set")
        return 0

    logger.info("AI drafting started")
    drafted = 0
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT eq.queue_id::text, eq.event_type, eq.title, eq.city,
                       eq.country, eq.sector, eq.source_url, eq.why_it_matters,
                       eq.confidence_score
                FROM editorial_queue eq
                LEFT JOIN ai_drafts ad ON ad.queue_id = eq.queue_id
                WHERE eq.status = 'new'
                  AND ad.draft_id IS NULL
                ORDER BY eq.created_at DESC
                LIMIT 5
            """)
            items = [dict(r) for r in cur.fetchall()]
            cur.close()

            for item in items:
                queue_id = item["queue_id"]
                try:
                    parsed = _generate_draft_for_item(item)
                    with conn.cursor() as wc:
                        wc.execute("""
                            INSERT INTO ai_drafts
                                (queue_id, headline, deck, body, model_name, prompt_version, status)
                            VALUES (%s::uuid, %s, %s, %s, 'gpt-4.1-mini', 'v1', 'draft')
                        """, (queue_id, parsed["headline"], parsed["deck"], parsed["body"]))
                    conn.commit()
                    drafted += 1
                    logger.info("AI draft created for queue_id=%s", queue_id)
                except Exception as e:
                    logger.warning("AI draft failed for %s: %s", queue_id, e)
    except Exception as e:
        logger.error("AI drafting DB error: %s", e)

    logger.info("AI drafting done: %d drafts created", drafted)
    return drafted


# ── API routes ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class StatusUpdate(BaseModel):
    status: str

@app.patch("/api/signals/{queue_id}/status")
async def update_signal_status(queue_id: str, body: StatusUpdate):
    if body.status not in ("new", "in_review", "published", "dismissed"):
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE editorial_queue SET status=%s WHERE queue_id=%s::uuid",
                (body.status, queue_id)
            )
            conn.commit()
            cur.close()
    except Exception as e:
        logger.error("Status update error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}

@app.post("/api/auth")
async def auth(req: LoginRequest):
    if req.username == os.getenv("DASH_USER", "admin") and \
       req.password == os.getenv("DASH_PASSWORD", "changeme"):
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/health")
async def health():
    return {"status": "ok"}


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = None

@app.post("/api/translate")
async def translate_text(req: TranslateRequest):
    import asyncio
    original = req.text
    translated = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _translate(req.text, source_lang=req.source_lang)
    )
    return {"original": original, "translated": translated, "changed": original != translated}


@app.post("/api/fetch-now")
async def fetch_now():
    import asyncio
    loop = asyncio.get_event_loop()
    results = {}
    for name, fn in [
        ("prozorro",      run_prozorro),
        ("mtender",       run_mtender),
        ("anaf",          run_anaf),
        ("opendatabot",   run_opendatabot),
        ("ckan_portals",  run_ckan_portals),
        ("rss_feeds",     run_rss_feeds),
    ]:
        try:
            results[name] = await loop.run_in_executor(None, fn)
        except Exception as e:
            results[name] = {"error": str(e)}
    return {"status": "done", "results": results}


@app.get("/api/drafts/{queue_id}")
async def get_draft(queue_id: str):
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT draft_id::text, queue_id::text, headline, deck, body,
                       model_name, prompt_version, status, created_at
                FROM ai_drafts
                WHERE queue_id = %s::uuid
                ORDER BY created_at DESC LIMIT 1
            """, (queue_id,))
            row = cur.fetchone()
            cur.close()
    except Exception as e:
        logger.error("Get draft error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="No draft found")
    return norm([dict(row)])[0]


@app.post("/api/drafts/{queue_id}/generate")
async def generate_draft(queue_id: str):
    if not os.getenv("OPENAI_API_KEY", ""):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")

    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT queue_id::text, event_type, title, city, country, sector,
                       source_url, why_it_matters, confidence_score
                FROM editorial_queue WHERE queue_id = %s::uuid
            """, (queue_id,))
            item = cur.fetchone()
            cur.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not item:
        raise HTTPException(status_code=404, detail="Signal not found")

    item = dict(item)

    import asyncio
    try:
        parsed = await asyncio.get_event_loop().run_in_executor(
            None, lambda: _generate_draft_for_item(item)
        )
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                INSERT INTO ai_drafts
                    (queue_id, headline, deck, body, model_name, prompt_version, status)
                VALUES (%s::uuid, %s, %s, %s, 'gpt-4.1-mini', 'v1', 'draft')
                RETURNING draft_id::text, queue_id::text, headline, deck, body,
                          model_name, prompt_version, status, created_at
            """, (queue_id, parsed["headline"], parsed["deck"], parsed["body"]))
            row = cur.fetchone()
            conn.commit()
            cur.close()
        return norm([dict(row)])[0]
    except Exception as e:
        logger.error("Generate draft error for %s: %s", queue_id, e)
        raise HTTPException(status_code=500, detail=str(e))


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
