import re

SECTOR_KEYWORDS = {
    "IT": ["software", "it", "technology", "технолог", "програм", "ai", "cyber"],
    "Banking & Finance": ["bank", "finance", "leasing", "insurance", "capital", "кредит"],
    "Real Estate": ["development", "developer", "real estate", "construction", "нерухом", "буд"],
    "Ports & Logistics": ["port", "terminal", "shipping", "logistics", "warehouse", "cargo", "порт"],
    "Energy": ["energy", "electric", "power", "grid", "solar", "gas", "енерг"],
    "Healthcare": ["hospital", "clinic", "medical", "pharma", "rehab", "лікар"],
    "Law": ["law", "legal", "attorney", "право", "адвокат"],
    "Accounting & Advisory": ["audit", "accounting", "tax", "advisory", "consulting"],
    "Infrastructure": ["road", "bridge", "highway", "reconstruction", "дорога", "міст"],
}

CITY_KEYWORDS = {
    "Kyiv": ["kyiv", "kiev", "київ"],
    "Lviv": ["lviv", "львів"],
    "Odesa": ["odesa", "odessa", "одеса"],
    "Chisinau": ["chisinau", "chișinău", "chisinău", "кишинів"],
    "Bucharest": ["bucharest", "bucuresti", "bucurești"],
}

LEGAL_SUFFIXES = ["llc", "ltd", "inc", "corp", "gmbh", "srl", "sa", "pjsc", "jsc", "тов", "тзов"]


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9а-яіїєґăâîșț\s]", " ", n)
    for suffix in LEGAL_SUFFIXES:
        n = re.sub(rf"\b{suffix}\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def infer_sector(text: str) -> str:
    t = (text or "").lower()
    for sector, terms in SECTOR_KEYWORDS.items():
        if any(term in t for term in terms):
            return sector
    return "General Business"


def infer_city(text: str) -> str | None:
    t = (text or "").lower()
    for city, terms in CITY_KEYWORDS.items():
        if any(term in t for term in terms):
            return city
    return None
