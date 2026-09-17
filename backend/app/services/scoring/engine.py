from __future__ import annotations

from dataclasses import dataclass

import yaml

from app.config import Settings, get_settings


@dataclass
class ScoreResult:
    score: int
    priority: str
    evidence: list[str]
    suggested_service: str


def load_scoring_config(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return yaml.safe_load(settings.scoring_path.read_text(encoding="utf-8")) or {}


def score_lead(
    *,
    website_status: str,
    quality_score: int | None,
    responsive: bool = True,
    has_email: bool = False,
    has_phone: bool = False,
    has_address: bool = False,
    quality_insufficient: bool = False,
    notes: str | None = None,
    config: dict | None = None,
) -> ScoreResult:
    cfg = config or load_scoring_config()
    weights = cfg.get("weights") or {}
    thresholds = cfg.get("thresholds") or {}
    evidence: list[str] = []
    total = 0

    def add(key: str, cond: bool, label: str) -> None:
        nonlocal total
        if not cond:
            return
        delta = int(weights.get(key, 0))
        total += delta
        sign = "+" if delta >= 0 else ""
        evidence.append(f"{label} ({sign}{delta})")

    add("no_website", website_status == "no_website", "Nessun sito")
    add("unreachable_website", website_status in {"unreachable", "error", "blocked"}, "Sito non raggiungibile o bloccato")
    very_low = (
        quality_score is not None
        and quality_score < int(thresholds.get("quality_very_low", 35))
        and website_status == "reachable"
    )
    add("very_low_quality", very_low, "Quality score molto basso")
    add("not_responsive", website_status == "reachable" and not responsive, "Segnali di mancata adattabilità mobile")
    add("public_email", has_email, "Email pubblica disponibile")
    add("phone", has_phone, "Telefono disponibile")
    add("local_presence", has_address, "Indirizzo/presenza locale")
    modern = (
        website_status == "reachable"
        and quality_score is not None
        and quality_score >= int(thresholds.get("quality_modern", 75))
        and responsive
    )
    add("modern_complete", modern, "Sito moderno e sufficientemente completo")
    add("insufficient_data", (quality_insufficient or website_status in {"unknown", "redirect_only"}) and website_status != "no_website", "Dati insufficienti")

    score = max(0, min(100, total))
    a_min = int(thresholds.get("priority_a", 70))
    b_min = int(thresholds.get("priority_b", 40))
    if score >= a_min:
        priority = "A"
    elif score >= b_min:
        priority = "B"
    else:
        priority = "C"

    return ScoreResult(
        score=score,
        priority=priority,
        evidence=evidence,
        suggested_service=suggest_service(website_status, quality_score, notes, thresholds),
    )


def suggest_service(
    website_status: str,
    quality_score: int | None,
    notes: str | None,
    thresholds: dict,
) -> str:
    text = (notes or "").lower()
    if any(token in text for token in ("catalogo", "prenotaz", "booking", "e-commerce", "ecommerce")):
        return "Web app o integrazione da valutare"
    if any(token in text for token in ("automat", "workflow", "integrazione gestionale")):
        return "Automazione"
    if any(token in text for token in ("manutenzione", "software esistente", "gestionale già")):
        return "Manutenzione/evolutive"
    if website_status == "no_website":
        return "Sviluppo sito web"
    if website_status in {"unreachable", "error", "blocked"}:
        return "Restyling / sito professionale"
    if quality_score is not None and quality_score < int(thresholds.get("quality_very_low", 35)):
        return "Restyling / sito professionale"
    if website_status == "reachable" and quality_score is not None and quality_score >= int(thresholds.get("quality_modern", 75)):
        return "Analisi preliminare"
    if website_status in {"unknown", "redirect_only"}:
        return "Analisi preliminare"
    return "Analisi preliminare"
