from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

from app.schemas import PlaceCandidate

PHONE_RE = re.compile(r"[^\d+]")


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalize_name(value: str) -> str:
    cleaned = strip_accents(value).lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    cleaned = strip_accents(value).lower()
    cleaned = re.sub(r"\b(via|viale|piazza|corso|contrada|str\.)\b", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = PHONE_RE.sub("", value)
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("+39"):
        digits = "+39" + digits[3:]
    elif digits.startswith("39") and len(re.sub(r"\D", "", digits)) >= 11:
        digits = "+" + digits
    elif digits.startswith("0"):
        digits = "+39" + digits
    if len(re.sub(r"\D", "", digits)) < 8:
        return None
    return digits


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    raw = url.strip()
    if not raw:
        return None
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    host = urlparse(raw).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_website(url: str | None) -> str | None:
    if not url:
        return None
    raw = url.strip()
    if not raw:
        return None
    if not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.netloc:
        return None
    return raw.split("#")[0].rstrip("/")


def extract_postal_code(address: str | None) -> str | None:
    if not address:
        return None
    match = re.search(r"\b(\d{5})\b", address)
    return match.group(1) if match else None


def extract_city(address: str | None, fallback: str | None = None) -> str | None:
    if not address:
        return fallback
    match = re.search(r"\b\d{5}\s+([A-Za-zÀ-ÿ'’\- ]+)", address)
    if match:
        city = match.group(1).split(",")[0].strip()
        return city.title() if city else fallback
    return fallback


def normalize_place(candidate: PlaceCandidate) -> dict:
    website = normalize_website(candidate.website)
    return {
        "source_provider": candidate.provider,
        "source_external_id": candidate.external_id,
        "name": candidate.name.strip(),
        "category": candidate.category,
        "address": candidate.address.strip() if candidate.address else None,
        "city": candidate.city or extract_city(candidate.address),
        "postal_code": candidate.postal_code or extract_postal_code(candidate.address),
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "phone": normalize_phone(candidate.phone) or candidate.phone,
        "website": website,
    }
