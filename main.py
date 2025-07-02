from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests, re, urllib.parse

app = FastAPI()

# ---------- helper ----------
def short_domain(url: str) -> str:
    """Return domain.tld (very light, no external cache needed)."""
    host = urllib.parse.urlparse(url).hostname or ""
    host = re.sub(r"^(www|m|web)\.", "", host)   # strip common subdomains
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host

# ---------- /fetch-page ----------
@app.get("/fetch-page")
def fetch_page(url: str):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "SEO-Auditor-Bot"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- /analyze-seo ----------
class AnalyzeBody(BaseModel):
    html: str
    url: str
    primary_keyword: str

@app.post("/analyze-seo")
def analyze_seo(body: AnalyzeBody):
    try:
        soup = BeautifulSoup(body.html, "html.parser")
        pk = body.primary_keyword.lower()

        # --- basic elements ---
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_tag.get("content", "").strip() if meta_tag else ""

        h1s = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
        text = soup.get_text(" ", strip=True)

        report = {
            "title": {
                "present": bool(title),
                "length": len(title),
                "includes_kw": pk in title.lower()
            },
            "meta": {
                "present": bool(meta_desc),
                "length": len(meta_desc),
                "includes_kw": pk in meta_desc.lower()
            },
            "h1": {
                "count": len(h1s),
                "includes_kw": pk in (h1s[0].lower() if h1s else "")
            },
            "word_count": len(re.findall(r"\w+", text)),
            "kw_in_first_150": pk in text[:150].lower(),
            "internal_links": len([a for a in soup.find_all("a", href=True)
                                   if short_domain(a["href"]) == short_domain(body.url)]),
            "external_links": len([a for a in soup.find_all("a", href=True)
                                   if short_domain(a["href"]) not in ["", short_domain(body.url)]]),
            "images": {
                "total": len(soup.find_all("img")),
                "missing_alt": sum(1 for img in soup.find_all("img") if not img.get("alt"))
            },
            "url_contains_kw": pk in body.url.lower()
        }
        return report

    except Exception as e:
        print("analyze_seo error:", e)
        raise HTTPException(status_code=400, detail=str(e))
