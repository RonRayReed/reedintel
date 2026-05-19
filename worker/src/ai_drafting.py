from openai import OpenAI
from sqlalchemy import text

from config import settings
from db import engine

SYSTEM_PROMPT = """
You are Reed Intel's business-news drafting assistant.
Use only the facts provided in the prompt.
Do not invent quotes, people, dollar values, causes, or relationships.
Write clearly for executives, investors, lawyers, bankers, and business owners.
Mark any uncertainty as 'requires editor verification'.
"""


def draft_from_queue_item(item: dict) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.openai_api_key)
    user_prompt = f"""
Create a Reed Intel business brief from the following structured facts.

City: {item.get('city')}
Country: {item.get('country')}
Sector: {item.get('sector')}
Event Type: {item.get('event_type')}
Title: {item.get('title')}
Why it matters: {item.get('why_it_matters')}
Source URL: {item.get('source_url')}
Confidence Score: {item.get('confidence_score')}

Required format:
Headline:
Deck:
Body: 250-400 words
Editor Verification Notes:
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    raw = response.choices[0].message.content
    return {"text": raw, "model": "gpt-4.1-mini"}


def save_ai_draft(
    queue_id: str,
    headline: str,
    deck: str,
    body: str,
    model_name: str = "gpt-4.1-mini",
    prompt_version: str = "v1",
):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO ai_drafts (queue_id, headline, deck, body, model_name, prompt_version)
            VALUES (:queue_id, :headline, :deck, :body, :model_name, :prompt_version)
        """), {
            "queue_id": queue_id,
            "headline": headline,
            "deck": deck,
            "body": body,
            "model_name": model_name,
            "prompt_version": prompt_version,
        })
