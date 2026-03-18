"""
AI Analyzer — Cross-domain reasoning for drug repurposing.
Uses OpenAI GPT with RAG-style prompting when API key is available,
falls back to rule-based analysis otherwise.
"""

import json
from config import Config


class DrugAnalyzer:
    """Analyzes aggregated data to identify drug repurposing opportunities."""

    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL

    def analyze(self, molecule: str, data: dict) -> dict:
        """
        Perform AI-driven analysis on the retrieved data.
        Returns structured insights with repurposing recommendations.
        """
        if self.api_key and self.api_key != "your-openai-api-key-here":
            return self._ai_analysis(molecule, data)
        else:
            return self._rule_based_analysis(molecule, data)

    def _ai_analysis(self, molecule: str, data: dict) -> dict:
        """Use OpenAI GPT for cross-domain reasoning."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            # Build RAG context from retrieved data
            context = self._build_context(molecule, data)

            system_prompt = """You are a pharmaceutical research analyst specializing in drug repurposing.
Analyze the provided research data about a drug molecule and generate a structured report.
Focus on identifying potential new therapeutic uses based on clinical trial data, research papers, and patent information.
Always cite specific sources (PMIDs, NCT IDs, patent numbers) for your conclusions.

Return your analysis as valid JSON with these exact keys:
{
    "clinical_status": {"summary": "...", "key_findings": ["..."], "active_trials": 0},
    "patent_landscape": {"summary": "...", "key_patents": ["..."], "expiration_risk": "low/medium/high"},
    "regulatory_status": {"summary": "...", "approvals": ["..."]},
    "market_analysis": {"summary": "...", "unmet_needs": ["..."], "market_potential": "low/medium/high"},
    "repurposing_opportunities": [
        {"indication": "...", "evidence_strength": "low/medium/high", "rationale": "...", "sources": ["..."]}
    ],
    "overall_confidence": "low/medium/high",
    "executive_summary": "..."
}"""

            user_prompt = f"""Analyze the following data for the molecule: {molecule}

{context}

Provide your analysis as the specified JSON structure."""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except Exception as e:
            print(f"[AI Analyzer] OpenAI error: {e}, falling back to rule-based")
            return self._rule_based_analysis(molecule, data)

    def _rule_based_analysis(self, molecule: str, data: dict) -> dict:
        """Rule-based fallback analysis when no API key is available."""
        papers = data.get("research_papers", [])
        trials = data.get("clinical_trials", [])
        patents = data.get("patents", [])

        # Clinical status analysis
        active_trials = [t for t in trials if t.get("status") in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION")]
        completed_trials = [t for t in trials if t.get("status") == "COMPLETED"]
        all_conditions = []
        for t in trials:
            all_conditions.extend(t.get("conditions", []))
        unique_conditions = list(set(all_conditions))

        # Extract repurposing signals from conditions studied
        repurposing_opps = []
        if len(unique_conditions) > 1:
            for condition in unique_conditions[:5]:
                related_trials = [t for t in trials if condition in t.get("conditions", [])]
                repurposing_opps.append({
                    "indication": condition,
                    "evidence_strength": "high" if len(related_trials) > 2 else "medium" if related_trials else "low",
                    "rationale": f"Found {len(related_trials)} clinical trial(s) studying {molecule} for {condition}.",
                    "sources": [t.get("nct_id", "N/A") for t in related_trials[:3]]
                })

        return {
            "clinical_status": {
                "summary": (
                    f"Found {len(trials)} clinical trial(s) for {molecule}. "
                    f"{len(active_trials)} actively recruiting, "
                    f"{len(completed_trials)} completed."
                ),
                "key_findings": [
                    f"{t.get('title', 'Untitled')} — Phase: {t.get('phase', 'N/A')}, Status: {t.get('status', 'Unknown')}"
                    for t in trials[:5]
                ],
                "active_trials": len(active_trials)
            },
            "patent_landscape": {
                "summary": f"Found {len(patents)} patent record(s) related to {molecule}.",
                "key_patents": [
                    f"{p.get('title', 'Untitled')} (ID: {p.get('patent_id', 'N/A')})"
                    for p in patents[:5]
                ],
                "expiration_risk": "medium"
            },
            "regulatory_status": {
                "summary": f"Regulatory data derived from {len(trials)} trial record(s) and {len(papers)} research paper(s).",
                "approvals": [f"See clinical trial {t.get('nct_id', '')} for regulatory context" for t in trials[:3]]
            },
            "market_analysis": {
                "summary": f"{molecule} is being studied across {len(unique_conditions)} therapeutic area(s).",
                "unmet_needs": unique_conditions[:5] if unique_conditions else ["Further research needed"],
                "market_potential": "high" if len(unique_conditions) > 3 else "medium" if unique_conditions else "low"
            },
            "repurposing_opportunities": repurposing_opps if repurposing_opps else [{
                "indication": "Further investigation needed",
                "evidence_strength": "low",
                "rationale": f"Limited data available for {molecule}. More targeted research is recommended.",
                "sources": []
            }],
            "overall_confidence": "high" if len(trials) > 5 and len(papers) > 5 else "medium" if trials or papers else "low",
            "executive_summary": (
                f"Analysis of {molecule}: {len(papers)} research paper(s), {len(trials)} clinical trial(s), "
                f"and {len(patents)} patent record(s) were retrieved. "
                f"The molecule is being studied across {len(unique_conditions)} condition(s), "
                f"suggesting {'strong' if len(unique_conditions) > 3 else 'moderate' if unique_conditions else 'limited'} "
                f"repurposing potential."
            )
        }

    def _build_context(self, molecule: str, data: dict) -> str:
        """Build a text context from all retrieved data for the LLM prompt."""
        sections = [f"=== DATA FOR: {molecule.upper()} ===\n"]

        # Research papers
        papers = data.get("research_papers", [])
        sections.append(f"--- RESEARCH PAPERS ({len(papers)} found) ---")
        for p in papers[:8]:
            sections.append(
                f"- PMID: {p.get('pmid', 'N/A')} | Title: {p.get('title', 'N/A')} "
                f"| Year: {p.get('year', 'N/A')}\n  Abstract: {p.get('abstract', 'N/A')[:300]}..."
            )

        # Clinical trials
        trials = data.get("clinical_trials", [])
        sections.append(f"\n--- CLINICAL TRIALS ({len(trials)} found) ---")
        for t in trials[:8]:
            sections.append(
                f"- NCT: {t.get('nct_id', 'N/A')} | Title: {t.get('title', 'N/A')} "
                f"| Phase: {t.get('phase', 'N/A')} | Status: {t.get('status', 'N/A')} "
                f"| Conditions: {', '.join(t.get('conditions', []))}"
            )

        # Patents
        patents = data.get("patents", [])
        sections.append(f"\n--- PATENTS ({len(patents)} found) ---")
        for pat in patents[:8]:
            sections.append(
                f"- ID: {pat.get('patent_id', 'N/A')} | Title: {pat.get('title', 'N/A')} "
                f"| Assignee: {pat.get('assignee', 'N/A')} | Filed: {pat.get('filing_date', 'N/A')}"
            )

        return "\n".join(sections)
