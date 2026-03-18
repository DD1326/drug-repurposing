"""
Centralized configuration for the Drug Repurposing Intelligence Platform.
Loads secrets from .env file and provides default settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # PubMed E-Utilities
    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PUBMED_API_KEY = os.getenv("PUBMED_API_KEY", "")
    PUBMED_MAX_RESULTS = int(os.getenv("PUBMED_MAX_RESULTS", 10))

    # ClinicalTrials.gov v2
    CLINICAL_TRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"
    CLINICAL_TRIALS_MAX_RESULTS = int(os.getenv("CT_MAX_RESULTS", 10))

    # Google Patents
    PATENTS_SEARCH_URL = "https://patents.google.com"
    PATENTS_MAX_RESULTS = int(os.getenv("PATENTS_MAX_RESULTS", 10))

    # Task Manager
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))

    # Reports
    REPORTS_DIR = os.path.join(os.path.dirname(__file__), "generated_reports")
