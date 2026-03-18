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

    def search(self, molecule: str) -> dict:
        """
        Search PubMed for papers related to the molecule.
        Returns a dict with 'results' (list) and 'total_count' (int).
        """
        # Clean molecule name (basic)
        molecule_clean = molecule.strip()
        
        # Step 1: ESearch to get PMIDs and total count
        pmids, total_count = self._esearch(molecule_clean)
        
        # If no results, try without the restrictive "repurposing" tags
        if not pmids:
            pmids, total_count = self._esearch(molecule_clean, restrictive=False)
            
        if not pmids:
            return {"results": [], "total_count": 0}

        # Step 2: EFetch to get article details
        articles = self._efetch(pmids)
        return {"results": articles, "total_count": total_count}

    def _esearch(self, query: str, restrictive: bool = True) -> tuple:
        """Search PubMed and return (list of PMIDs, total count)."""
        search_term = f'("{query}"[Title/Abstract])'
        if restrictive:
            search_term += " AND (drug repurposing OR pharmacology OR therapeutic OR trial)"
            
        params = {
            "db": "pubmed",
            "term": search_term,
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
            esearchresult = data.get("esearchresult", {})
            return (
                esearchresult.get("idlist", []),
                int(esearchresult.get("count", "0"))
            )
        except Exception as e:
            print(f"[PubMed] ESearch error: {e}")
            return [], 0

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
