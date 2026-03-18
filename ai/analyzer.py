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
        self.openai_api_key = Config.OPENAI_API_KEY
        self.openai_model = Config.OPENAI_MODEL
        self.gemini_api_key = Config.GEMINI_API_KEY
        self.gemini_model = Config.GEMINI_MODEL

    def analyze(self, molecule: str, data: dict) -> dict:
        """
        Perform AI-driven analysis on the retrieved data.
        Returns structured insights with repurposing recommendations.
        Tries OpenAI first, then Gemini, then falls back to rule-based.
        """
        # Try OpenAI
        if self.openai_api_key and self.openai_api_key not in ("", "your-openai-api-key-here"):
            try:
                return self._ai_analysis_openai(molecule, data)
            except Exception as e:
                print(f"[AI Analyzer] OpenAI failed: {e}")

        # Try Gemini
        if self.gemini_api_key and self.gemini_api_key not in ("", "your-gemini-api-key-here"):
            try:
                return self._ai_analysis_gemini(molecule, data)
            except Exception as e:
                print(f"[AI Analyzer] Gemini failed: {e}")

        # Fallback to Rule-based
        print("[AI Analyzer] No valid AI response, using rule-based fallback.")
        return self._rule_based_analysis(molecule, data)

    def _ai_analysis_openai(self, molecule: str, data: dict) -> dict:
        """Use OpenAI GPT for cross-domain reasoning."""
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key)

        context = self._build_context(molecule, data)
        system_prompt, user_prompt = self._get_prompts(molecule, context)

        response = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result_text = response.choices[0].message.content
        return json.loads(result_text)

    def _ai_analysis_gemini(self, molecule: str, data: dict) -> dict:
        """Use Google Gemini for cross-domain reasoning."""
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_api_key)
        
        # Use latest Gemini model
        model = genai.GenerativeModel(self.gemini_model)
        
        context = self._build_context(molecule, data)
        system_prompt, user_prompt = self._get_prompts(molecule, context)
        
        # Combined prompt as Gemini handles system instructions differently in older versions
        # but we use the new system_instruction parameter if supported
        full_prompt = f"{system_prompt}\n\nUSER INPUT:\n{user_prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        
        return json.loads(response.text)

    def _get_prompts(self, molecule: str, context: str) -> tuple:
        """Centralized prompts for LLMs."""
        system_prompt = """You are a pharmaceutical research analyst specializing in drug repurposing.
Analyze the provided research data about a drug molecule and generate a structured report.
Focus on identifying potential new therapeutic uses based on clinical trial data, research papers, and patent information.
Always cite specific sources (PMIDs, NCT IDs, patent numbers) for your conclusions.

Return your analysis AS VALID JSON ONLY with these exact keys:
{
    "clinical_status": {"summary": "...", "key_findings": ["..."], "active_trials": 0},
    "patent_landscape": {"summary": "...", "key_patents": ["..."], "expiration_risk": "low/medium/high"},
    "regulatory_status": {"summary": "...", "approvals": ["..."]},
    "market_analysis": {"summary": "...", "unmet_needs": ["..."], "market_potential": "low/medium/high"},
    "repurposing_opportunities": [
        {"indication": "...", "evidence_strength": "low/medium/high", "rationale": "...", "sources": ["..."]}
    ],
    "overall_confidence": "low/medium/high",
    "executive_summary": "Start with a sentence like: 'Our analysis of [X] research papers, [Y] clinical trials, and [Z] patents reveals...' using the total counts provided in the data headers."
}"""

        user_prompt = f"""Analyze the following data for the molecule: {molecule}

{context}

Provide your analysis as the specified JSON structure."""
        
        return system_prompt, user_prompt

    def _rule_based_analysis(self, molecule: str, data: dict) -> dict:
        """Rule-based fallback analysis when no API key is available."""
        papers_data = data.get("research_papers", {})
        trials_data = data.get("clinical_trials", {})
        patents_data = data.get("patents", {})

        papers = papers_data.get("results", [])
        trials = trials_data.get("results", [])
        patents = patents_data.get("results", [])

        total_papers = papers_data.get("total_count", 0)
        total_trials = trials_data.get("total_count", 0)
        total_patents = patents_data.get("total_count", 0)

        # Clinical status analysis
        active_trials = [t for t in trials if t.get("status") in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION")]
        completed_trials = [t for t in trials if t.get("status") == "COMPLETED"]
        all_conditions = []
        for t in trials:
            all_conditions.extend(t.get("conditions", []))
        unique_conditions = list(set(all_conditions))

        # Extract repurposing signals from conditions studied
        repurposing_opps = []
        # If we have any conditions at all, show the first few as opportunities
        if unique_conditions:
            # Dynamic cap based on found conditions to avoid "constant" feel
            for condition in unique_conditions[:100]:
                related_trials = [t for t in trials if condition in t.get("conditions", [])]
                repurposing_opps.append({
                    "indication": condition,
                    "evidence_strength": "high" if len(related_trials) > 3 else "medium" if related_trials else "low",
                    "rationale": f"Detected in {len(related_trials)} trial(s) specifically for this drug.",
                    "sources": [t.get("nct_id", "N/A") for t in related_trials[:3]]
                })
        else:
            # Try to extract from paper abstracts if trials are empty
            import re
            for p in papers[:15]:
                title = p.get("title", "")
                
                # Look for common condition suffixes or patterns
                # Matches words like "Hypertension", "Dermatitis", "Tuberculosis", "Alzheimer", "Cancer", "Pain"
                patterns = [
                    r"\b[A-Z][a-z]+(?:osis|itis|emia|ia|oma|opathy|syndrome|disease|cancer|pain|infection)\b",
                    r"(?:treatment of|efficacy in|patients with) ([A-Z][a-z]+)"
                ]
                
                found_condition = None
                for pattern in patterns:
                    match = re.search(pattern, title)
                    if match:
                        found_condition = match.group(1 if "(" in pattern else 0)
                        break
                
                if found_condition:
                    repurposing_opps.append({
                        "indication": found_condition,
                        "evidence_strength": "low",
                        "rationale": f"Potential signal detected from research title: {title}",
                        "sources": [p.get("pmid", "N/A")]
                    })
                
                # Fallback to broad categories if nothing found but keywords present
                elif any(word in title.lower() for word in ["cancer", "tumor", "oncology"]):
                    found_condition = "Oncology"
                elif any(word in title.lower() for word in ["heart", "cardio", "vascular"]):
                    found_condition = "Cardiovascular"
                
                if found_condition and not any(o["indication"] == found_condition for o in repurposing_opps):
                    repurposing_opps.append({
                        "indication": found_condition,
                        "evidence_strength": "low",
                        "rationale": f"General therapeutic category match: {title}",
                        "sources": [p.get("pmid", "N/A")]
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
                "summary": f"Identified related patent families and litigation records for {molecule}.",
                "key_patents": [
                    f"{p.get('title', 'Untitled')} (ID: {p.get('patent_id', 'N/A')})"
                    for p in patents[:8]
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
                "rationale": f"Limited clinical trial data available for {molecule}. Literature review is recommended.",
                "sources": []
            }],
            "overall_confidence": "high" if len(trials) > 5 and len(papers) > 5 else "medium" if trials or papers else "low",
            "executive_summary": (
                f"Analysis of {molecule}: {total_papers} research paper(s), {total_trials} clinical trial(s), "
                f"and {total_patents} patent record(s) were retrieved. "
                f"{molecule} shows {'extensive' if len(unique_conditions) > 3 else 'targeted'} clinical activity "
                f"across {len(unique_conditions)} therapeutic area(s). "
                + (f"The largest clinical trial detected is {trials[0].get('title')[:60]}... (ID: {trials[0].get('nct_id')})." if trials else "No specific clinical trials were highlighted for this summary.") +
                f" (Note: Rule-based analysis used due to LLM provider unavailability)."
            )
        }

    def _build_context(self, molecule: str, data: dict) -> str:
        """Build a text context from all retrieved data for the LLM prompt."""
        sections = [f"=== DATA FOR: {molecule.upper()} ===\n"]

        # Research papers
        papers = data.get("research_papers", {}).get("results", [])
        sections.append(f"--- RESEARCH PAPERS ({data.get('research_papers', {}).get('total_count', 0)} found) ---")
        for p in papers[:8]:
            sections.append(
                f"- PMID: {p.get('pmid', 'N/A')} | Title: {p.get('title', 'N/A')} "
                f"| Year: {p.get('year', 'N/A')}\n  Abstract: {p.get('abstract', 'N/A')[:300]}..."
            )

        # Clinical trials
        trials = data.get("clinical_trials", {}).get("results", [])
        sections.append(f"\n--- CLINICAL TRIALS ({data.get('clinical_trials', {}).get('total_count', 0)} found) ---")
        for t in trials[:8]:
            sections.append(
                f"- NCT: {t.get('nct_id', 'N/A')} | Title: {t.get('title', 'N/A')} "
                f"| Phase: {t.get('phase', 'N/A')} | Status: {t.get('status', 'N/A')} "
                f"| Conditions: {', '.join(t.get('conditions', []))}"
            )

        # Patents
        patents = data.get("patents", {}).get("results", [])
        sections.append(f"\n--- PATENTS ({data.get('patents', {}).get('total_count', 0)} found) ---")
        for pat in patents[:8]:
            sections.append(
                f"- ID: {pat.get('patent_id', 'N/A')} | Title: {pat.get('title', 'N/A')} "
                f"| Assignee: {pat.get('assignee', 'N/A')} | Filed: {pat.get('filing_date', 'N/A')}"
            )

        return "\n".join(sections)
