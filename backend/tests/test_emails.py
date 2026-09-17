from __future__ import annotations

from app.services.enrichment.emails import extract_emails, normalize_email


HTML = """
<html>
  <body>
    <a href="mailto:Info@PanificioEsempio.it">scrivici</a>
    <p>Contatti: commerciale@panificioesempio.it , foto@cdn.example.com.png</p>
    <img src="header.jpg" alt="contact@image.jpg">
  </body>
</html>
"""


def test_extract_prefers_generic_and_keeps_source():
    pairs = extract_emails(HTML, "https://panificioesempio.it/contatti")
    emails = [e for e, _ in pairs]
    assert "info@panificioesempio.it" in emails
    assert "commerciale@panificioesempio.it" in emails
    assert emails[0] == "info@panificioesempio.it"
    assert all(src.endswith("/contatti") for _, src in pairs)


def test_discard_invalid_patterns():
    assert normalize_email("not-an-email") is None
    assert normalize_email("file@cdn.example.com.png") is None
    assert normalize_email("header.jpg@image.jpg") is None
    assert normalize_email("  Hello@Studio.IT. ") == "hello@studio.it"
