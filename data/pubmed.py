"""
PubMed API Connector
Searches PubMed/PMC via NCBI E-Utilities for research papers about a drug molecule.
"""

import requests
import xml.etree.ElementTree as ET
from config import Config


class PubMedConnector:
    """Retrieves research papers from PubMed for a given molecule."""

    def __init__(self):
        self.base_url = Config.PUBMED_BASE_URL
        self.api_key = Config.PUBMED_API_KEY
        self.max_results = Config.PUBMED_MAX_RESULTS

    def search(self, molecule: str) -> list:
        """
        Search PubMed for papers related to the molecule.
        Returns a list of dicts with title, abstract, pmid, authors, date.
        """
        # Step 1: ESearch to get PMIDs
        pmids = self._esearch(molecule)
        if not pmids:
            return []

        # Step 2: EFetch to get article details
        articles = self._efetch(pmids)
        return articles

    def _esearch(self, query: str) -> list:
        """Search PubMed and return list of PMIDs."""
        params = {
            "db": "pubmed",
            "term": f"{query} AND (drug repurposing OR pharmacology OR therapeutic)",
            "retmax": self.max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            resp = requests.get(
                f"{self.base_url}/esearch.fcgi", params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"[PubMed] ESearch error: {e}")
            return []

    def _efetch(self, pmids: list) -> list:
        """Fetch article details for a list of PMIDs."""
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            resp = requests.get(
                f"{self.base_url}/efetch.fcgi", params=params, timeout=15
            )
            resp.raise_for_status()
            return self._parse_xml(resp.text)
        except Exception as e:
            print(f"[PubMed] EFetch error: {e}")
            return []

    def _parse_xml(self, xml_text: str) -> list:
        """Parse PubMed XML response into structured article dicts."""
        articles = []
        try:
            root = ET.fromstring(xml_text)
            for article_elem in root.findall(".//PubmedArticle"):
                medline = article_elem.find(".//MedlineCitation")
                if medline is None:
                    continue

                pmid_elem = medline.find("PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "N/A"

                art = medline.find(".//Article")
                if art is None:
                    continue

                # Title
                title_elem = art.find("ArticleTitle")
                title = title_elem.text if title_elem is not None else "Untitled"

                # Abstract
                abstract_parts = []
                abstract_elem = art.find(".//Abstract")
                if abstract_elem is not None:
                    for abstract_text in abstract_elem.findall("AbstractText"):
                        if abstract_text.text:
                            abstract_parts.append(abstract_text.text)
                abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available."

                # Authors
                authors = []
                author_list = art.find("AuthorList")
                if author_list is not None:
                    for author in author_list.findall("Author"):
                        last = author.find("LastName")
                        fore = author.find("ForeName")
                        if last is not None and fore is not None:
                            authors.append(f"{fore.text} {last.text}")

                # Date
                date_elem = art.find(".//PubDate")
                year = ""
                if date_elem is not None:
                    year_elem = date_elem.find("Year")
                    year = year_elem.text if year_elem is not None else ""

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors[:5],  # limit to first 5 authors
                    "year": year,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "source": "PubMed"
                })
        except ET.ParseError as e:
            print(f"[PubMed] XML parse error: {e}")

        return articles
