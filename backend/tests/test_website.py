from __future__ import annotations

import httpx
import respx

from app.services.website.checker import WebsiteChecker


HOME = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Studio">
</head>
<body>
  <header><h1>Studio</h1></header>
  <p>Chiama o scrivi a info@studio-test.example</p>
  <a href="/contatti">Contatti</a>
</body>
</html>
"""

CONTACTS = """
<html><body><a href="mailto:contatti@studio-test.example">mail</a></body></html>
"""


@respx.mock
def test_reachable_site_extracts_email_and_respects_robots():
    respx.get("https://studio-test.example/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nAllow: /\n")
    )
    respx.get("https://studio-test.example").mock(return_value=httpx.Response(200, text=HOME, headers={"content-type": "text/html"}))
    respx.get("https://studio-test.example/contatti").mock(
        return_value=httpx.Response(200, text=CONTACTS, headers={"content-type": "text/html"})
    )
    respx.get("https://studio-test.example/contatti/").mock(
        return_value=httpx.Response(200, text=CONTACTS, headers={"content-type": "text/html"})
    )
    respx.get("https://studio-test.example/contact").mock(return_value=httpx.Response(404))
    respx.get("https://studio-test.example/chi-siamo").mock(return_value=httpx.Response(404))
    respx.get("https://studio-test.example/about").mock(return_value=httpx.Response(404))
    respx.get("https://studio-test.example/privacy").mock(return_value=httpx.Response(404))

    check = WebsiteChecker().check("https://studio-test.example")
    assert check.status == "reachable"
    assert check.quality_score is not None
    emails = [e for e, _ in check.emails]
    assert "info@studio-test.example" in emails or "contatti@studio-test.example" in emails
    assert check.email_status == "found"


@respx.mock
def test_blocked_by_robots():
    respx.get("https://blocked.example/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /\n")
    )
    respx.get("https://blocked.example").mock(
        return_value=httpx.Response(200, text="<html><body>ok</body></html>", headers={"content-type": "text/html"})
    )
    check = WebsiteChecker().check("https://blocked.example")
    assert check.status == "blocked"


@respx.mock
def test_unreachable():
    respx.get("https://down.example").mock(side_effect=httpx.ConnectError("fail"))
    check = WebsiteChecker().check("https://down.example")
    assert check.status == "unreachable"


def test_no_website():
    check = WebsiteChecker().check(None)
    assert check.status == "no_website"
