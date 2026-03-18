"""
Patent Scraper
Searches Google Patents for patent information related to a drug molecule.
Uses requests + BeautifulSoup for parsing.
"""

import requests
from bs4 import BeautifulSoup
from config import Config


class PatentScraper:
    """Scrapes Google Patents for patent data related to a drug molecule."""

    def __init__(self):
        self.base_url = Config.PATENTS_SEARCH_URL
        self.max_results = Config.PATENTS_MAX_RESULTS
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def search(self, molecule: str) -> list:
        """
        Search Google Patents for patents related to the molecule.
        Returns a list of dicts with title, assignee, patent_id, filing_date, status.
        Falls back to structured placeholder data if scraping fails.
        """
        try:
            url = f"{self.base_url}/?q={molecule}&oq={molecule}"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            return self._parse_html(resp.text, molecule)
        except Exception as e:
            print(f"[Patents] Scraping error: {e}")
            # Return structured placeholder indicating scraping limitation
            return self._fallback_results(molecule)

    def _parse_html(self, html: str, molecule: str) -> list:
        """Parse Google Patents search results page."""
        patents = []
        soup = BeautifulSoup(html, "lxml")

        # Google Patents uses dynamic JS rendering, so direct scraping is limited
        # Try to find any result elements
        results = soup.select("search-result-item, .result-item, article")

        if not results:
            # Google Patents heavily relies on JS — fall back gracefully
            return self._fallback_results(molecule)

        for item in results[: self.max_results]:
            title_elem = item.select_one("h3, .result-title, a")
            title = title_elem.get_text(strip=True) if title_elem else "Untitled Patent"

            # Try to get patent ID from link
            link_elem = item.select_one("a[href*='patent']")
            patent_id = ""
            patent_url = ""
            if link_elem and link_elem.get("href"):
                href = link_elem["href"]
                patent_id = href.split("/")[-1] if "/" in href else href
                patent_url = f"https://patents.google.com{href}" if href.startswith("/") else href

            patents.append({
                "patent_id": patent_id or "N/A",
                "title": title,
                "assignee": "See full patent",
                "filing_date": "N/A",
                "status": "See full patent",
                "url": patent_url or f"https://patents.google.com/?q={molecule}",
                "source": "Google Patents"
            })

        return patents

    def _fallback_results(self, molecule: str) -> list:
        """
        Return a structured entry directing users to Google Patents.
        Used when direct scraping cannot extract detailed data.
        """
        return [{
            "patent_id": "search-required",
            "title": f"Patent search for '{molecule}'",
            "assignee": "Visit Google Patents for full results",
            "filing_date": "N/A",
            "status": "Manual review recommended",
            "url": f"https://patents.google.com/?q={molecule}",
            "source": "Google Patents",
            "note": (
                "Google Patents uses JavaScript rendering. "
                "Click the URL above to view full patent results."
            )
        }]
