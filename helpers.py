# helpers.py  (or paste below existing code in main.py)

import httpx, re, json, time, urllib.parse
from fastapi import HTTPException

def fetch_robots_txt(domain: str) -> str:
    url = urllib.parse.urljoin(domain, "/robots.txt")
    try:
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"robots.txt fetch failed: {e}")

def parse_robots(robots_text: str, target_path: str) -> dict:
    """
    Very light parser: finds any Disallow rule that blocks the target path.
    """
    blocked = False
    rules = []
    for line in robots_text.splitlines():
        m = re.match(r"(?i)disallow:\s*(.*)", line)
        if m:
            rule = m.group(1).strip()
            rules.append(rule or "/")
            if target_path.startswith(rule):
                blocked = True
    return {"blocked": blocked, "rules": rules}

# ---- Core Web Vitals via PageSpeed Insights ----

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

def call_psi(url: str, api_key: str) -> dict:
    """
    Tries mobile first; if PageSpeed blocks or lacks data, retries desktop.
    Returns the metrics for whichever strategy succeeds.
    """
    for strat in ("mobile", "desktop"):
        params = {
            "url": url,
            "key": api_key,
            "strategy": strat,
            "category": "performance"
        }
        r = httpx.get(PSI_ENDPOINT, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            audits = data["lighthouseResult"]["audits"]
            metrics = audits["metrics"]["details"]["items"][0]
            return {
                "strategy": strat,                         # so the GPT can mention which one succeeded
                "lcp_ms": metrics["largestContentfulPaint"],
                "cls": audits["cumulative-layout-shift"]["displayValue"],
                "inp_ms": metrics.get("experimental_interaction_to_next_paint"),
                "score": data["lighthouseResult"]["categories"]["performance"]["score"]
            }

    # If both attempts failed:
    raise HTTPException(status_code=400, detail="PSI failed on mobile and desktop")


