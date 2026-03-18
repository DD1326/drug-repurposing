"""
Citation Engine — Automated Verified Source Citations
Ensures every AI insight maps back to a specific source (PMID, NCT ID, or patent number).
"""


class CitationEngine:
    """Builds and validates citations linking insights to original sources."""

    def __init__(self):
        self.citation_registry = {}

    def build_citations(self, data: dict) -> dict:
        """
        Create a citation registry from all retrieved data.
        Maps source IDs to their metadata for cross-referencing.
        """
        citations = {}

        # PubMed citations
        for paper in data.get("research_papers", []):
            pmid = paper.get("pmid", "")
            if pmid:
                citations[f"PMID:{pmid}"] = {
                    "type": "research_paper",
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "authors": paper.get("authors", []),
                    "year": paper.get("year", ""),
                }

        # Clinical trial citations
        for trial in data.get("clinical_trials", []):
            nct_id = trial.get("nct_id", "")
            if nct_id:
                citations[nct_id] = {
                    "type": "clinical_trial",
                    "title": trial.get("title", ""),
                    "url": trial.get("url", ""),
                    "phase": trial.get("phase", ""),
                    "status": trial.get("status", ""),
                }

        # Patent citations
        for patent in data.get("patents", []):
            pat_id = patent.get("patent_id", "")
            if pat_id and pat_id != "search-required":
                citations[pat_id] = {
                    "type": "patent",
                    "title": patent.get("title", ""),
                    "url": patent.get("url", ""),
                    "assignee": patent.get("assignee", ""),
                }

        self.citation_registry = citations
        return citations

    def get_citation(self, source_id: str) -> dict:
        """Retrieve citation details by source ID."""
        return self.citation_registry.get(source_id, {"error": "Citation not found"})

    def validate_citations(self, analysis: dict) -> dict:
        """
        Cross-reference citations mentioned in the AI analysis
        with the citation registry.
        """
        validation = {"valid": [], "unverified": [], "total": 0}

        # Check repurposing opportunities for source references
        for opp in analysis.get("repurposing_opportunities", []):
            for source in opp.get("sources", []):
                validation["total"] += 1
                # Check if source exists in our registry
                matched = False
                for reg_key in self.citation_registry:
                    if source in reg_key or reg_key in source:
                        validation["valid"].append({
                            "referenced": source,
                            "matched_to": reg_key,
                            "details": self.citation_registry[reg_key]
                        })
                        matched = True
                        break
                if not matched:
                    validation["unverified"].append(source)

        return validation
