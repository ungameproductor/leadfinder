from __future__ import annotations

import re
from collections.abc import Iterable
from html import unescape

EMAIL_RE = re.compile(
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
)
MAILTO_RE = re.compile(r"mailto:([^?'\"\s>]+)", re.I)
INVALID_LOCAL = re.compile(r"(png|jpe?g|gif|webp|svg|css|js|woff2?)$", re.I)
GENERIC_ORDER = ("info@", "contatti@", "commerciale@", "hello@", "office@", "segreteria@")


def extract_emails(html: str, page_url: str) -> list[tuple[str, str]]:
    text = unescape(html)
    found: list[str] = []
    for match in MAILTO_RE.findall(text):
        found.append(match)
    for match in EMAIL_RE.findall(text):
        found.append(match)

    unique: dict[str, str] = {}
    for raw in found:
        email = normalize_email(raw)
        if email and email not in unique:
            unique[email] = page_url
    return prefer_generic(unique.items())


def normalize_email(value: str) -> str | None:
    email = unescape(value).strip().lower().rstrip(".,;:")
    email = email.replace("%40", "@")
    if email.count("@") != 1:
        return None
    local, domain = email.split("@", 1)
    if not local or not domain or "." not in domain:
        return None
    if INVALID_LOCAL.search(local):
        return None
    if domain.endswith((".png", ".jpg", ".jpeg", ".gif", ".css", ".js")):
        return None
    if any(token in email for token in ("example.com", "email.com", "domain.com", "sentry.io")):
        return None
    if " " in email:
        return None
    return email


def prefer_generic(pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    items = list(pairs)

    def rank(email: str) -> int:
        for i, prefix in enumerate(GENERIC_ORDER):
            if email.startswith(prefix):
                return i
        return len(GENERIC_ORDER)

    return sorted(items, key=lambda item: rank(item[0]))
