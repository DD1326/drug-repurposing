"""
ClinicalTrials.gov API Connector (v2)
Searches for clinical trials related to a drug molecule.
"""

import requests
from config import Config


class ClinicalTrialsConnector:
    """Retrieves clinical trial data from ClinicalTrials.gov for a given molecule."""

    def __init__(self):
        self.base_url = Config.CLINICAL_TRIALS_BASE_URL
        self.max_results = Config.CLINICAL_TRIALS_MAX_RESULTS

    def search(self, molecule: str) -> dict:
        """
        Search ClinicalTrials.gov for trials involving the molecule.
        Returns a dict with 'results' (list) and 'total_count' (int).
        """
        params = {
            "query.term": molecule,
            "pageSize": self.max_results,
            "countTotal": "true",
            "format": "json",
        }

        try:
            resp = requests.get(
                f"{self.base_url}/studies", params=params, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "results": self._parse_response(data),
                "total_count": data.get("totalCount", 0)
            }
        except Exception as e:
            print(f"[ClinicalTrials] Search error: {e}")
            return {"results": [], "total_count": 0}

    def _parse_response(self, data: dict) -> list:
        """Parse ClinicalTrials.gov v2 API response."""
        trials = []
        studies = data.get("studies", [])

        for study in studies:
            protocol = study.get("protocolSection", {})
            id_module = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            design_module = protocol.get("designModule", {})
            conditions_module = protocol.get("conditionsModule", {})
            description_module = protocol.get("descriptionModule", {})
            enrollment_info = design_module.get("enrollmentInfo", {})

            nct_id = id_module.get("nctId", "N/A")

            # Extract phases
            phases = design_module.get("phases", [])
            phase_str = ", ".join(phases) if phases else "Not Specified"

            # Extract conditions
            conditions = conditions_module.get("conditions", [])

            trials.append({
                "nct_id": nct_id,
                "title": id_module.get("officialTitle", id_module.get("briefTitle", "Untitled")),
                "status": status_module.get("overallStatus", "Unknown"),
                "phase": phase_str,
                "conditions": conditions[:5],
                "enrollment": enrollment_info.get("count", "N/A"),
                "start_date": status_module.get("startDateStruct", {}).get("date", "N/A"),
                "brief_summary": description_module.get("briefSummary", ""),
                "url": f"https://clinicaltrials.gov/study/{nct_id}",
                "source": "ClinicalTrials.gov"
            })

        return trials
