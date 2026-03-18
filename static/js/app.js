/**
 * DrugRepur — Client-side Application Logic
 * Handles search, loading animation, API calls, and results rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const searchForm = document.getElementById('searchForm');
    const moleculeInput = document.getElementById('moleculeInput');
    const searchBtn = document.getElementById('searchBtn');
    const heroSection = document.getElementById('heroSection');
    const loadingSection = document.getElementById('loadingSection');
    const loadingMolecule = document.getElementById('loadingMolecule');
    const dashboard = document.getElementById('dashboard');
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    const newSearchBtn = document.getElementById('newSearchBtn');
    const errorRetryBtn = document.getElementById('errorRetryBtn');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const rawDataToggle = document.getElementById('rawDataToggle');
    const rawDataBody = document.getElementById('rawDataBody');

    // --- Hero Particles ---
    createParticles();

    // --- Event Listeners ---
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const molecule = moleculeInput.value.trim();
        if (molecule) analyzeMolecule(molecule);
    });

    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const molecule = btn.dataset.molecule;
            moleculeInput.value = molecule;
            analyzeMolecule(molecule);
        });
    });

    newSearchBtn.addEventListener('click', showSearch);
    errorRetryBtn.addEventListener('click', showSearch);

    rawDataToggle.addEventListener('click', () => {
        const isHidden = rawDataBody.style.display === 'none';
        rawDataBody.style.display = isHidden ? 'block' : 'none';
        rawDataToggle.querySelector('.toggle-icon').classList.toggle('open', isHidden);
    });

    // --- Core Functions ---

    async function analyzeMolecule(molecule) {
        showLoading(molecule);

        try {
            // Animate loading steps
            const stepInterval = animateLoadingSteps();

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ molecule })
            });

            clearInterval(stepInterval);
            completeAllSteps();

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Analysis failed');
            }

            const report = await response.json();

            // Small delay for visual polish
            setTimeout(() => showResults(report), 600);

        } catch (err) {
            showError(err.message);
        }
    }

    function showSearch() {
        heroSection.style.display = 'flex';
        loadingSection.style.display = 'none';
        dashboard.style.display = 'none';
        errorSection.style.display = 'none';
        searchBtn.classList.remove('loading');
        searchBtn.disabled = false;
        setStatus('ready');
        moleculeInput.focus();
    }

    function showLoading(molecule) {
        heroSection.style.display = 'none';
        loadingSection.style.display = 'flex';
        dashboard.style.display = 'none';
        errorSection.style.display = 'none';
        loadingMolecule.textContent = molecule;
        searchBtn.classList.add('loading');
        searchBtn.disabled = true;
        setStatus('analyzing');

        // Reset loading steps
        document.querySelectorAll('.loading-step').forEach(step => {
            step.classList.remove('active', 'done');
        });
    }

    function showResults(report) {
        heroSection.style.display = 'none';
        loadingSection.style.display = 'none';
        dashboard.style.display = 'block';
        errorSection.style.display = 'none';
        searchBtn.classList.remove('loading');
        searchBtn.disabled = false;
        setStatus('ready');

        renderReport(report);
    }

    function showError(message) {
        heroSection.style.display = 'none';
        loadingSection.style.display = 'none';
        dashboard.style.display = 'none';
        errorSection.style.display = 'flex';
        errorMessage.textContent = message;
        searchBtn.classList.remove('loading');
        searchBtn.disabled = false;
        setStatus('error');
    }

    function setStatus(state) {
        statusDot.className = 'status-dot';
        if (state === 'analyzing') {
            statusDot.classList.add('analyzing');
            statusText.textContent = 'Analyzing...';
        } else if (state === 'error') {
            statusDot.classList.add('error');
            statusText.textContent = 'Error';
        } else {
            statusText.textContent = 'Ready';
        }
    }

    // --- Loading Animation ---

    function animateLoadingSteps() {
        const steps = document.querySelectorAll('.loading-step');
        let current = 0;

        if (steps[0]) steps[0].classList.add('active');

        return setInterval(() => {
            if (current < steps.length) {
                steps[current].classList.remove('active');
                steps[current].classList.add('done');
                current++;
                if (current < steps.length) {
                    steps[current].classList.add('active');
                }
            }
        }, 1500);
    }

    function completeAllSteps() {
        document.querySelectorAll('.loading-step').forEach(step => {
            step.classList.remove('active');
            step.classList.add('done');
        });
    }

    // --- Render Report ---

    function renderReport(report) {
        const sections = report.sections || {};

        // Header
        document.getElementById('reportMolecule').textContent = report.molecule || 'Unknown';
        document.getElementById('reportIdBadge').textContent = `ID: ${report.report_id || '—'}`;
        document.getElementById('reportTimeBadge').textContent = formatDate(report.generated_at);

        // Confidence badge
        const conf = report.overall_confidence || 'low';
        const confBadge = document.getElementById('confidenceBadge');
        confBadge.textContent = `Confidence: ${conf.charAt(0).toUpperCase() + conf.slice(1)}`;
        confBadge.className = `badge confidence-${conf}`;

        // Executive Summary
        document.getElementById('executiveSummary').textContent = report.executive_summary || 'No summary available.';

        // Stats
        const sources = report.data_sources || {};
        animateCounter('statPapers', sources.pubmed_articles || 0);
        animateCounter('statTrials', sources.clinical_trials || 0);
        animateCounter('statPatents', sources.patent_records || 0);
        animateCounter('statOpportunities', (sections.repurposing_opportunities || []).length);

        // Clinical Status
        renderSectionCard('clinicalBody', sections.clinical_status);

        // Patent Landscape
        renderSectionCard('patentBody', sections.patent_landscape);

        // Regulatory Status
        renderSectionCard('regulatoryBody', sections.regulatory_status);

        // Market Analysis
        renderSectionCard('marketBody', sections.market_analysis);

        // Repurposing Opportunities
        renderOpportunities(sections.repurposing_opportunities || []);

        // Raw Data
        renderRawData(report.raw_data || {});
    }

    function renderSectionCard(elementId, data) {
        const el = document.getElementById(elementId);
        if (!data) {
            el.innerHTML = '<p class="text-muted">No data available.</p>';
            return;
        }

        let html = '';

        // Summary
        if (data.summary) {
            html += `<p class="section-summary">${escapeHtml(data.summary)}</p>`;
        }

        // Key findings / key patents / approvals / unmet needs
        const listKey = data.key_findings || data.key_patents || data.approvals || data.unmet_needs || [];
        if (listKey.length > 0) {
            html += '<ul class="findings-list">';
            listKey.forEach(item => {
                html += `<li><span class="finding-bullet">▸</span> ${escapeHtml(item)}</li>`;
            });
            html += '</ul>';
        }

        // Extra fields
        if (data.active_trials !== undefined) {
            html += `<p style="margin-top:0.5rem;font-size:0.8rem;color:var(--accent-green);">Active Trials: ${data.active_trials}</p>`;
        }
        if (data.expiration_risk) {
            html += `<p style="margin-top:0.5rem;font-size:0.8rem;">Expiration Risk: <span class="opp-strength ${data.expiration_risk}">${data.expiration_risk}</span></p>`;
        }
        if (data.market_potential) {
            html += `<p style="margin-top:0.5rem;font-size:0.8rem;">Market Potential: <span class="opp-strength ${data.market_potential}">${data.market_potential}</span></p>`;
        }

        el.innerHTML = html;
    }

    function renderOpportunities(opportunities) {
        const el = document.getElementById('repurposingBody');
        if (opportunities.length === 0) {
            el.innerHTML = '<p class="text-muted">No repurposing opportunities identified.</p>';
            return;
        }

        let html = '';
        opportunities.forEach(opp => {
            const strength = opp.evidence_strength || 'low';
            html += `
                <div class="opportunity-card">
                    <div class="opp-header">
                        <span class="opp-indication">${escapeHtml(opp.indication || 'Unknown')}</span>
                        <span class="opp-strength ${strength}">${strength}</span>
                    </div>
                    <p class="opp-rationale">${escapeHtml(opp.rationale || '')}</p>
                    <div class="opp-sources">
                        ${(opp.sources || []).map(s => `<span class="source-tag">${escapeHtml(s)}</span>`).join('')}
                    </div>
                </div>
            `;
        });

        el.innerHTML = html;
    }

    function renderRawData(rawData) {
        const el = document.getElementById('rawDataBody');
        let html = '';

        // Research Papers
        const papers = rawData.research_papers || [];
        if (papers.length > 0) {
            html += '<div class="raw-data-section">';
            html += `<h4 class="raw-data-title">📄 Research Papers (${papers.length})</h4>`;
            papers.forEach(p => {
                html += `
                    <div class="data-item">
                        <div class="data-item-title">${escapeHtml(p.title || 'Untitled')}</div>
                        <div class="data-item-meta">
                            PMID: ${p.pmid || 'N/A'} · ${p.year || 'N/A'} · ${(p.authors || []).slice(0, 3).join(', ')}
                        </div>
                        <a href="${p.url || '#'}" target="_blank" rel="noopener">View on PubMed →</a>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Clinical Trials
        const trials = rawData.clinical_trials || [];
        if (trials.length > 0) {
            html += '<div class="raw-data-section">';
            html += `<h4 class="raw-data-title">🏥 Clinical Trials (${trials.length})</h4>`;
            trials.forEach(t => {
                html += `
                    <div class="data-item">
                        <div class="data-item-title">${escapeHtml(t.title || 'Untitled')}</div>
                        <div class="data-item-meta">
                            ${t.nct_id || 'N/A'} · Phase: ${t.phase || 'N/A'} · Status: ${t.status || 'Unknown'}
                            ${t.conditions ? ' · ' + t.conditions.join(', ') : ''}
                        </div>
                        <a href="${t.url || '#'}" target="_blank" rel="noopener">View on ClinicalTrials.gov →</a>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Patents
        const patents = rawData.patents || [];
        if (patents.length > 0) {
            html += '<div class="raw-data-section">';
            html += `<h4 class="raw-data-title">📜 Patents (${patents.length})</h4>`;
            patents.forEach(pat => {
                html += `
                    <div class="data-item">
                        <div class="data-item-title">${escapeHtml(pat.title || 'Untitled')}</div>
                        <div class="data-item-meta">
                            ID: ${pat.patent_id || 'N/A'} · ${pat.assignee || 'N/A'}
                        </div>
                        <a href="${pat.url || '#'}" target="_blank" rel="noopener">View Patent →</a>
                    </div>
                `;
            });
            html += '</div>';
        }

        if (!html) {
            html = '<p style="color:var(--text-muted)">No raw data available.</p>';
        }

        el.innerHTML = html;
    }

    // --- Utilities ---

    function animateCounter(elementId, target) {
        const el = document.getElementById(elementId);
        const duration = 800;
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(start + (target - start) * eased);
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    function formatDate(isoString) {
        if (!isoString) return 'N/A';
        try {
            const d = new Date(isoString);
            return d.toLocaleString('en-IN', {
                day: 'numeric', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch {
            return isoString;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function createParticles() {
        const container = document.getElementById('heroParticles');
        if (!container) return;
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.className = 'hero-particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDuration = (5 + Math.random() * 10) + 's';
            particle.style.animationDelay = (Math.random() * 5) + 's';
            particle.style.opacity = (0.1 + Math.random() * 0.3);
            container.appendChild(particle);
        }
    }
});
