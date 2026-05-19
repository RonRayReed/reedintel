from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SourceRecord(BaseModel):
    source_name: str
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    raw_json: Optional[dict] = None
    raw_text: Optional[str] = None


class Company(BaseModel):
    legal_name: str
    normalized_name: Optional[str] = None
    registration_number: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    sector: Optional[str] = None
    source_system: Optional[str] = None
    confidence_score: float = 0.5


class ProcurementEvent(BaseModel):
    source_name: str
    tender_id: Optional[str] = None
    buyer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    value_amount: Optional[float] = None
    currency: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    award_date: Optional[date] = None
    publication_date: Optional[date] = None
    source_url: Optional[str] = None
    confidence_score: float = 0.5


class EditorialItem(BaseModel):
    event_type: str
    title: str
    city: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    source_url: Optional[str] = None
    why_it_matters: Optional[str] = None
    confidence_score: float = 0.5
    company_id: Optional[UUID] = None
    procurement_event_id: Optional[UUID] = None
