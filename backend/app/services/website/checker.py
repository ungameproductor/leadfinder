from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
import yaml

from app.config import Settings, get_settings
from app.services.enrichment.emails import extract_emails
from app.services.website.quality import candidate_paths, score_page
from app.services.website.robots import allowed_by_robots


@dataclass
class WebsiteCheck:
    status: str
    final_url: str | None = None
    quality_score: int | None = None
    quality_evidence: list[str] = field(default_factory=list)
    insufficient: bool = False
    responsive: bool = True
    emails: list[tuple[str, str]] = field(default_factory=list)
    email_status: str = "not_found"
    error: str | None = None


class WebsiteChecker:
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client
        weights = yaml.safe_load(self.settings.scoring_path.read_text(encoding="utf-8")) or {}
        self.quality_weights = weights.get("quality_weights") or {}

    def check(self, website: str | None) -> WebsiteCheck:
        if not website:
            return WebsiteCheck(status="no_website", email_status="skipped")

        owns = self.client is None
        client = self.client or httpx.Client(
            timeout=self.settings.request_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": self.settings.http_user_agent, "Accept": "text/html,application/xhtml+xml"},
        )
        try:
            return self._check_with_client(client, website)
        finally:
            if owns:
                client.close()

    def _check_with_client(self, client: httpx.Client, website: str) -> WebsiteCheck:
        redirects = 0
        current = website
        html = ""
        status_code = 0
        elapsed_ms = None
        final_url = website
        try:
            while redirects <= 5:
                started = time.perf_counter()
                response = client.get(current)
                elapsed_ms = (time.perf_counter() - started) * 1000
                status_code = response.status_code
                if status_code in {301, 302, 303, 307, 308} and response.headers.get("location"):
                    redirects += 1
                    current = str(response.url.join(response.headers["location"]))
                    continue
                final_url = str(response.url)
                html = response.text if "text" in response.headers.get("content-type", "text/html") else ""
                if not html and response.content and len(response.content) < 2_000_000:
                    html = response.content.decode("utf-8", errors="ignore")
                break
        except httpx.TimeoutException:
            return WebsiteCheck(status="unreachable", error="timeout", email_status="skipped")
        except httpx.RequestError as exc:
            return WebsiteCheck(status="unreachable", error=str(exc), email_status="skipped")

        if redirects > 5:
            return WebsiteCheck(status="redirect_only", final_url=final_url, email_status="skipped")
        if status_code >= 400:
            return WebsiteCheck(
                status="error",
                final_url=final_url,
                quality_score=max(0, 20),
                quality_evidence=[f"HTTP {status_code}"],
                insufficient=True,
                email_status="skipped",
                error=f"HTTP {status_code}",
            )

        if not allowed_by_robots(client, final_url, self.settings.http_user_agent, self.settings.request_timeout_seconds):
            return WebsiteCheck(status="blocked", final_url=final_url, email_status="skipped", error="robots.txt")

        quality = score_page(
            url=final_url,
            status_code=status_code,
            html=html,
            elapsed_ms=elapsed_ms,
            weights=self.quality_weights,
            fetched_paths=[final_url],
        )
        emails: list[tuple[str, str]] = extract_emails(html, final_url)

        pages = candidate_paths(final_url, html, self.settings.crawl_max_pages_per_domain)
        for page_url in pages[1:]:
            time.sleep(self.settings.crawl_delay_seconds)
            if not allowed_by_robots(client, page_url, self.settings.http_user_agent, self.settings.request_timeout_seconds):
                continue
            try:
                page = client.get(page_url, follow_redirects=True)
            except httpx.RequestError:
                continue
            if page.status_code >= 400:
                continue
            ctype = page.headers.get("content-type", "")
            if "html" not in ctype and "text" not in ctype:
                continue
            emails.extend(extract_emails(page.text, str(page.url)))

        unique_emails: dict[str, str] = {}
        for email, source in emails:
            unique_emails.setdefault(email, source)
        email_pairs = list(unique_emails.items())
        return WebsiteCheck(
            status="reachable",
            final_url=final_url,
            quality_score=quality.score,
            quality_evidence=quality.evidence,
            insufficient=quality.insufficient,
            responsive=quality.responsive,
            emails=email_pairs,
            email_status="found" if email_pairs else "not_found",
        )
