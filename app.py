"""
Drug Repurposing Intelligence Platform — Flask Application
Main entry point. Provides the web interface and API endpoints.
"""

import os
from flask import Flask, render_template, request, jsonify
from config import Config
from task_manager import TaskManager
from ai.analyzer import DrugAnalyzer
from ai.citation_engine import CitationEngine
from reports.generator import ReportGenerator

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize components
task_manager = TaskManager()
analyzer = DrugAnalyzer()
citation_engine = CitationEngine()
report_generator = ReportGenerator()

# In-memory store of recent reports
recent_reports = {}


@app.route("/")
def index():
    """Serve the main web interface."""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze_molecule():
    """
    POST /api/analyze
    Body: { "molecule": "Aspirin" }
    Runs the full pipeline: data retrieval → AI analysis → report generation.
    """
    data = request.get_json()
    if not data or not data.get("molecule"):
        return jsonify({"error": "Please provide a molecule name."}), 400

    molecule = data["molecule"].strip()
    if not molecule:
        return jsonify({"error": "Molecule name cannot be empty."}), 400

    try:
        # Step 1: Parallel data retrieval
        raw_data = task_manager.execute(molecule)

        # Step 2: AI analysis (GPT or rule-based fallback)
        analysis = analyzer.analyze(molecule, raw_data)

        # Step 3: Build citation registry
        citations = citation_engine.build_citations(raw_data)
        citation_validation = citation_engine.validate_citations(analysis)

        # Step 4: Generate report
        report = report_generator.generate(molecule, raw_data, analysis, citations)

        # Add citation validation to report
        report["citation_validation"] = citation_validation

        # Cache report
        recent_reports[report["report_id"]] = report

        return jsonify(report), 200

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/api/report/<report_id>", methods=["GET"])
def get_report(report_id):
    """GET /api/report/<id> — Retrieve a previously generated report."""
    # Check in-memory cache first
    if report_id in recent_reports:
        return jsonify(recent_reports[report_id]), 200

    # Check disk
    report = report_generator.get_report(report_id)
    if "error" in report:
        return jsonify(report), 404

    return jsonify(report), 200


@app.route("/api/reports", methods=["GET"])
def list_reports():
    """GET /api/reports — List all generated reports."""
    reports = report_generator.list_reports()
    return jsonify({"reports": reports}), 200


if __name__ == "__main__":
    os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Drug Repurposing Intelligence Platform")
    print(f"  Running on http://{Config.HOST}:{Config.PORT}")
    print(f"  OpenAI: {'Enabled' if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'your-openai-api-key-here' else 'Disabled (rule-based mode)'}")
    print(f"{'='*60}\n")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
