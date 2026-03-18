"""
Task Manager — Parallel Sub-task Coordination
Breaks a molecule research query into parallel sub-tasks and executes them concurrently.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config


class TaskManager:
    """Orchestrates parallel data retrieval for a given molecule."""

    def __init__(self):
        self.max_workers = Config.MAX_WORKERS

    def execute(self, molecule: str) -> dict:
        """
        Run all data retrieval tasks in parallel for the given molecule.
        Returns aggregated results from all sources.
        """
        from data.pubmed import PubMedConnector
        from data.clinical_trials import ClinicalTrialsConnector
        from data.patent_scraper import PatentScraper

        tasks = {
            "research_papers": PubMedConnector().search,
            "clinical_trials": ClinicalTrialsConnector().search,
            "patents": PatentScraper().search,
        }

        results = {}
        errors = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(func, molecule): name
                for name, func in tasks.items()
            }

            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    results[task_name] = future.result()
                except Exception as e:
                    errors[task_name] = str(e)
                    results[task_name] = []

        if errors:
            results["_errors"] = errors

        return results
