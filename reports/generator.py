"""
Report Generator — Structured Innovation Opportunity Reports
Generates JSON reports combining raw data, AI analysis, and verified citations.
"""

import json
import os
import uuid
from datetime import datetime
from config import Config


class ReportGenerator:
    """Generates the final Structured Innovation Opportunity Report."""

    def __init__(self):
        self.reports_dir = Config.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, molecule: str, raw_data: dict, analysis: dict, citations: dict) -> dict:
        """
        Combine all data into the final Innovation Opportunity Report.
        Returns the full report as a dict and saves to disk.
        """
        report_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        report = {
            "report_id": report_id,
            "molecule": molecule,
            "generated_at": timestamp,
            "executive_summary": analysis.get("executive_summary", ""),
            "overall_confidence": analysis.get("overall_confidence", "low"),
            "sections": {
                "clinical_status": analysis.get("clinical_status", {}),
                "patent_landscape": analysis.get("patent_landscape", {}),
                "regulatory_status": analysis.get("regulatory_status", {}),
                "market_analysis": analysis.get("market_analysis", {}),
                "repurposing_opportunities": analysis.get("repurposing_opportunities", []),
            },
            "raw_data": {
                "research_papers": raw_data.get("research_papers", []),
                "clinical_trials": raw_data.get("clinical_trials", []),
                "patents": raw_data.get("patents", []),
            },
            "citations": citations,
            "data_sources": {
                "pubmed_articles": len(raw_data.get("research_papers", [])),
                "clinical_trials": len(raw_data.get("clinical_trials", [])),
                "patent_records": len(raw_data.get("patents", [])),
            },
            "errors": raw_data.get("_errors", {}),
        }

        # Save to disk
        self._save_report(report_id, report)

        return report

    def _save_report(self, report_id: str, report: dict):
        """Save report JSON to the generated_reports directory."""
        filepath = os.path.join(self.reports_dir, f"report_{report_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"[Report] Saved to {filepath}")
        except Exception as e:
            print(f"[Report] Save error: {e}")

    def get_report(self, report_id: str) -> dict:
        """Load a previously generated report by ID."""
        filepath = os.path.join(self.reports_dir, f"report_{report_id}.json")
        if not os.path.exists(filepath):
            return {"error": f"Report {report_id} not found"}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to load report: {e}"}

    def list_reports(self) -> list:
        """List all generated reports (metadata only)."""
        reports = []
        try:
            for fname in os.listdir(self.reports_dir):
                if fname.endswith(".json"):
                    filepath = os.path.join(self.reports_dir, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        reports.append({
                            "report_id": data.get("report_id", ""),
                            "molecule": data.get("molecule", ""),
                            "generated_at": data.get("generated_at", ""),
                            "confidence": data.get("overall_confidence", ""),
                        })
        except Exception as e:
            print(f"[Report] List error: {e}")
        return reports
