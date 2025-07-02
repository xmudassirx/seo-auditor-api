# helpers_schema.py
import extruct, requests
from w3lib.html import get_base_url

def extract_schema(url: str) -> dict:
    """Return JSON-LD & Microdata extracted from the page."""
    html = requests.get(url, timeout=10, headers={
        "User-Agent": "Mozilla/5.0 (SEO-Auditor)"
    }).text
    base = get_base_url(html, url)
    data = extruct.extract(html, base_url=base, syntaxes=["json-ld", "microdata"])
    return data
