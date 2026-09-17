from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


OBSOLETE_MARKERS = ("<frameset", "application/x-shockwave-flash", "document.write(")
CONTACT_HINTS = ("contatt", "prenota", "orari", "tel", "whatsapp", "email")
CONTACT_PATHS = ("/contatti", "/contatti/", "/contact", "/chi-siamo", "/about", "/privacy")


@dataclass
class QualityResult:
    score: int
    evidence: list[str] = field(default_factory=list)
    insufficient: bool = False
    responsive: bool = True


def score_page(
    *,
    url: str,
    status_code: int,
    html: str,
    elapsed_ms: float | None,
    weights: dict,
    fetched_paths: list[str],
) -> QualityResult:
    evidence: list[str] = []
    score = 55
    soup = BeautifulSoup(html or "", "lxml")
    lower = (html or "").lower()
    insufficient = not html or len(html) < 200

    parsed = urlparse(url)
    if parsed.scheme == "https":
        score += int(weights.get("https_ok", 8))
        evidence.append("HTTPS presente")
    else:
        score += int(weights.get("no_https", -20))
        evidence.append("HTTPS assente o non usato sull'URL finale")

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport and viewport.get("content"):
        score += int(weights.get("viewport_ok", 8))
        evidence.append("Meta viewport presente")
        responsive = True
    else:
        score += int(weights.get("no_viewport", -15))
        evidence.append("Meta viewport assente: possibile mancata adattabilità mobile")
        responsive = False

    if any(marker in lower for marker in OBSOLETE_MARKERS):
        score += int(weights.get("obsolete_tech", -15))
        evidence.append("Rilevati marker di tecnologie obsolete (frameset/Flash/document.write)")

    if status_code >= 400:
        score += int(weights.get("http_errors", -15))
        evidence.append(f"Risposta HTTP {status_code}")

    text = soup.get_text(" ", strip=True).lower()
    if any(hint in text for hint in CONTACT_HINTS) or soup.select("a[href^=mailto], a[href^=tel]"):
        score += int(weights.get("contact_info", 10))
        evidence.append("Informazioni di contatto o CTA visibili")
    else:
        score += int(weights.get("missing_cta", -8))
        evidence.append("Poche o nessuna CTA/contatto visibile in homepage")

    if soup.find("meta", attrs={"name": "description"}) or soup.find("main") or soup.find("header"):
        score += int(weights.get("modern_markup", 8))
        evidence.append("Markup HTML5 / meta description presenti")

    if elapsed_ms is not None and elapsed_ms > 2500:
        score += int(weights.get("slow_ttfb", -8))
        evidence.append(f"Tempo di risposta elevato ({int(elapsed_ms)} ms)")

    if insufficient:
        evidence.append("Contenuto scarso: dati insufficienti per una valutazione di qualità")

    score = max(0, min(100, score))
    return QualityResult(score=score, evidence=evidence, insufficient=insufficient, responsive=responsive)


def candidate_paths(base_url: str, html: str, max_pages: int) -> list[str]:
    soup = BeautifulSoup(html or "", "lxml")
    found = [base_url]
    hrefs = [a.get("href") for a in soup.select("a[href]")]
    base_host = urlparse(base_url).netloc
    extras: list[str] = []
    for href in hrefs:
        if not href:
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_host:
            continue
        path = parsed.path.lower()
        if any(token in path for token in ("contatt", "contact", "chi-siamo", "about", "privacy", "legal")):
            extras.append(absolute.split("#")[0])
    for path in CONTACT_PATHS:
        extras.append(urljoin(base_url if base_url.endswith("/") else base_url + "/", path.lstrip("/")))
    for url in extras:
        if url not in found:
            found.append(url)
        if len(found) >= max_pages:
            break
    return found[:max_pages]
