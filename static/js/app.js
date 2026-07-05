// AI Fraud Shield - Dashboard Controller
document.addEventListener("DOMContentLoaded", () => {
    
    // --- Application State ---
    const state = {
        agents: [],
        scenarios: [],
        history: [], // stores previous run results: { timestamp, query, category, risk, response }
        logsAutoScroll: true,
        pollingInterval: null
    };

    // --- DOM Elements Cache ---
    const elements = {
        navItems: document.querySelectorAll(".menu-item"),
        panels: document.querySelectorAll(".panel"),
        pageTitle: document.getElementById("page-title"),
        pageSubtitle: document.getElementById("page-subtitle"),
        
        // Overview Stats
        statAgentsCount: document.getElementById("stat-agents-count"),
        statQueriesCount: document.getElementById("stat-queries-count"),
        statThreatsCount: document.getElementById("stat-threats-count"),
        statAvgConfidence: document.getElementById("stat-avg-confidence"),
        agentsListOverview: document.getElementById("agents-list-overview"),
        
        // Detection Form
        formDetection: document.getElementById("form-fraud-detection"),
        inputText: document.getElementById("detection-input-text"),
        btnClearDetection: document.getElementById("btn-clear-detection"),
        btnSubmitDetection: document.getElementById("btn-submit-detection"),
        toggleAdvanced: document.getElementById("toggle-advanced-options"),
        advancedBody: document.getElementById("advanced-options-body"),
        agentCheckboxesContainer: document.getElementById("agent-checkboxes-container"),
        
        // Verdict Display
        resultPlaceholder: document.getElementById("detection-result-placeholder"),
        resultLoading: document.getElementById("detection-result-loading"),
        resultContent: document.getElementById("detection-result-content"),
        verdictRiskBadge: document.getElementById("verdict-risk-badge"),
        verdictCategory: document.getElementById("verdict-category"),
        verdictStatus: document.getElementById("verdict-status"),
        verdictAgentsUsed: document.getElementById("verdict-agents-used"),
        verdictRecommendation: document.getElementById("verdict-recommendation"),
        verdictNextSteps: document.getElementById("verdict-next-steps"),
        verdictSubAgentCards: document.getElementById("verdict-sub-agent-cards"),
        scannerStatus: document.getElementById("scanner-status"),
        
        // Scenarios Section
        btnRunAllScenarios: document.getElementById("btn-run-all-scenarios"),
        scenariosGrid: document.getElementById("scenarios-grid-container"),
        batchResultsCard: document.getElementById("batch-results-card"),
        batchProgressFill: document.getElementById("batch-progress-fill"),
        batchResultsTbody: document.getElementById("batch-results-tbody"),
        btnCloseBatchReport: document.getElementById("btn-close-batch-report"),
        
        // Analytics Section
        analTotalRuns: document.getElementById("anal-total-runs"),
        analCriticalRuns: document.getElementById("anal-critical-runs"),
        analHighRuns: document.getElementById("anal-high-runs"),
        analSafeRuns: document.getElementById("anal-safe-runs"),
        historyTbody: document.getElementById("history-tbody"),
        btnClearHistory: document.getElementById("btn-clear-history"),
        distCriticalPct: document.getElementById("dist-critical-pct"),
        distCriticalFill: document.getElementById("dist-critical-fill"),
        distHighPct: document.getElementById("dist-high-pct"),
        distHighFill: document.getElementById("dist-high-fill"),
        distMediumPct: document.getElementById("dist-medium-pct"),
        distMediumFill: document.getElementById("dist-medium-fill"),
        distLowPct: document.getElementById("dist-low-pct"),
        distLowFill: document.getElementById("dist-low-fill"),
        
        // Logs Section
        logsConsole: document.getElementById("logs-console-body"),
        logsLevelFilter: document.getElementById("logs-level-filter"),
        btnClearLogs: document.getElementById("btn-clear-logs"),
        btnToggleLogsScroll: document.getElementById("btn-toggle-logs-scroll"),
        logsCountBadge: document.getElementById("logs-count"),
        logsStatusText: document.getElementById("logs-status-text"),
        
        btnRefreshDashboard: document.getElementById("btn-refresh-dashboard")
    };

    // --- Toast Notifications System ---
    function showToast(message, type = "info") {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let icon = "fa-info-circle";
        if (type === "success") icon = "fa-check-circle";
        if (type === "error") icon = "fa-exclamation-triangle";
        
        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = "slideIn 0.3s ease reverse";
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // --- Navigation Routing (SPA) ---
    function navigateToPanel(panelId) {
        // Remove active class from menu items & panels
        elements.navItems.forEach(item => item.classList.remove("active"));
        elements.panels.forEach(panel => panel.classList.remove("active"));
        
        const targetMenu = document.getElementById(`nav-${panelId}`);
        const targetPanel = document.getElementById(`panel-${panelId}`);
        
        if (targetPanel) {
            targetPanel.classList.add("active");
            if (targetMenu) targetMenu.classList.add("active");
            
            // Set Header Titles
            const titleMap = {
                home: { title: "Dashboard Overview", sub: "Multi-Agent Orchestration & Threat Intelligence" },
                detection: { title: "Fraud & Threat Detector", sub: "Custom scam and phishing verification interface" },
                scenarios: { title: "Capstone Scenario Tester", sub: "Verify orchestrator behavior on preset security cases" },
                analytics: { title: "Results & Analytics Hub", sub: "Threat frequency data and inspection history" },
                logs: { title: "Engine System Logs", sub: "Live raw logs console interceptor" }
            };
            
            elements.pageTitle.textContent = titleMap[panelId].title;
            elements.pageSubtitle.textContent = titleMap[panelId].sub;
            
            // Manage log polling loop
            if (panelId === "logs") {
                startLogsPolling();
            } else {
                stopLogsPolling();
            }
            
            // Auto update statistics when loading panels
            updateStatsAndAnalytics();
        }
    }

    // Bind hashchange listener and initial route
    window.addEventListener("hashchange", () => {
        const hash = window.location.hash.substring(1) || "home";
        navigateToPanel(hash);
    });

    // Check initial hash route
    const initialHash = window.location.hash.substring(1) || "home";
    navigateToPanel(initialHash);

    // Sidebar navigation click override
    elements.navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const panelId = item.id.replace("nav-", "");
            window.location.hash = panelId;
        });
    });

    // --- Collapsible advanced panel ---
    elements.toggleAdvanced.addEventListener("click", () => {
        elements.toggleAdvanced.classList.toggle("open");
    });

    // --- Load Metadata from Backend ---
    async function loadBackendMetadata() {
        try {
            // Load sub-agents
            const agentsRes = await fetch("/api/agents");
            if (!agentsRes.ok) throw new Error("Could not load agents metadata.");
            const agentsData = await agentsRes.json();
            state.agents = agentsData.agents;
            
            renderAgentsMetadata();
            
            // Load scenarios
            const scenariosRes = await fetch("/api/scenarios");
            if (!scenariosRes.ok) throw new Error("Could not load scenarios list.");
            const scenariosData = await scenariosRes.json();
            state.scenarios = scenariosData.scenarios;
            
            renderScenariosGrid();
            
            showToast("System metadata loaded successfully", "success");
        } catch (err) {
            console.error(err);
            showToast(`Backend connection failed: ${err.message}`, "error");
        }
    }

    function renderAgentsMetadata() {
        // Render in Home Panel overview list
        elements.agentsListOverview.innerHTML = "";
        
        // Render in Checkboxes overrides list in Detection page
        elements.agentCheckboxesContainer.innerHTML = "";
        
        // Map agent names to unique FA icons
        const agentIconMap = {
            "Email": "fa-envelope-circle-check",
            "SMS":   "fa-comment-sms",
            "WhatsApp": "fa-comment-sms",
            "URL":   "fa-link-slash",
            "Shopping": "fa-bag-shopping",
            "Internship": "fa-user-tie",
            "Job": "fa-user-tie",
            "Risk Score": "fa-chart-simple",
            "Safety": "fa-shield-virus",
        };
        
        function getAgentIcon(name) {
            for (const [keyword, icon] of Object.entries(agentIconMap)) {
                if (name.includes(keyword)) return icon;
            }
            return "fa-robot";
        }
        
        state.agents.forEach(agent => {
            const icon = getAgentIcon(agent.name);
            
            // Home overview
            const overviewItem = document.createElement("div");
            overviewItem.className = "agent-small-item";
            overviewItem.innerHTML = `
                <div class="agent-small-item-icon">
                    <i class="fa-solid ${icon}"></i>
                </div>
                <div class="agent-small-item-info">
                    <h4>${agent.name}</h4>
                    <p>${agent.description}</p>
                </div>
            `;
            elements.agentsListOverview.appendChild(overviewItem);
            
            // Checkbox override card
            const checkboxLabel = document.createElement("label");
            checkboxLabel.className = "checkbox-card";
            checkboxLabel.innerHTML = `
                <input type="checkbox" name="selected_agents" value="${agent.name}">
                <i class="fa-solid ${icon}" style="color:var(--color-primary);margin-right:4px;"></i>
                <span>${agent.name}</span>
            `;
            elements.agentCheckboxesContainer.appendChild(checkboxLabel);
        });
        
        elements.statAgentsCount.textContent = state.agents.length;
    }

    function renderScenariosGrid() {
        elements.scenariosGrid.innerHTML = "";
        
        state.scenarios.forEach((scenarioText, index) => {
            const card = document.createElement("div");
            card.className = "scenario-card";
            
            // Short snippet
            let cleanSnippet = scenarioText.replace(/Analyze this email:|Is this WhatsApp message a scam\?|Check this URL:|Is this internship genuine\?|Is this shopping website trustworthy\?|My bank called and asked for my OTP verification code because of an unusual login.|Analyze everything and give me a risk report:/g, "").trim();
            if (cleanSnippet.length > 100) {
                cleanSnippet = cleanSnippet.substring(0, 100) + "...";
            }
            
            card.innerHTML = `
                <div>
                    <div class="scenario-card-header">
                        <span class="scenario-num">SCENARIO ${index + 1}</span>
                        <span class="badge badge-info">CAPSTONE</span>
                    </div>
                    <p class="scenario-text">"${cleanSnippet}"</p>
                </div>
                <div class="flex gap-sm">
                    <button class="btn btn-secondary btn-small btn-run-single-scen" data-index="${index}">
                        <i class="fa-solid fa-play"></i> Run Test
                    </button>
                </div>
            `;
            elements.scenariosGrid.appendChild(card);
        });

        // Attach run event listeners to single scenario buttons
        document.querySelectorAll(".btn-run-single-scen").forEach(btn => {
            btn.addEventListener("click", () => {
                const index = parseInt(btn.getAttribute("data-index"));
                runScenarioDirect(index);
            });
        });
    }

    // --- Scenario Runners ---
    function runScenarioDirect(index) {
        const text = state.scenarios[index];
        elements.inputText.value = text;
        
        // Switch to detection panel
        window.location.hash = "detection";
        
        // Trigger submit
        setTimeout(() => {
            elements.formDetection.dispatchEvent(new Event("submit"));
        }, 150);
    }

    // --- Submit Custom Scam Query ---
    elements.formDetection.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const queryText = elements.inputText.value.trim();
        if (!queryText) return;
        
        // Selected agents overrides
        const checkedBoxes = document.querySelectorAll("input[name='selected_agents']:checked");
        const selectedAgents = Array.from(checkedBoxes).map(box => box.value);
        
        // Hide placeholder and details, show loading spinner
        elements.resultPlaceholder.classList.add("hidden");
        elements.resultContent.classList.add("hidden");
        elements.resultLoading.classList.remove("hidden");
        
        // Change loading texts based on overrides
        if (selectedAgents.length > 0) {
            elements.scannerStatus.textContent = "Bypassing router... executing chosen agents...";
        } else {
            elements.scannerStatus.textContent = "Classifying query & selecting sub-agents...";
        }
        
        try {
            const start = Date.now();
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: queryText,
                    selected_agents: selectedAgents.length > 0 ? selectedAgents : null
                })
            });
            
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Query analysis failed.");
            }
            
            const result = await res.json();
            const duration = ((Date.now() - start) / 1000).toFixed(2);
            
            // Save run to local state history
            const historyItem = {
                timestamp: new Date().toLocaleTimeString(),
                query: queryText,
                category: result.input_type,
                risk: result.overall_risk,
                response: result,
                duration: duration
            };
            
            state.history.unshift(historyItem);
            
            // Render results
            renderAnalysisResults(result);
            showToast(`Threat evaluation complete in ${duration}s`, "success");
            
            // Update counts
            updateStatsAndAnalytics();
            
        } catch (err) {
            console.error(err);
            elements.resultLoading.classList.add("hidden");
            elements.resultPlaceholder.classList.remove("hidden");
            showToast(`Analysis Error: ${err.message}`, "error");
        }
    });

    elements.btnClearDetection.addEventListener("click", () => {
        elements.inputText.value = "";
        
        // Reset checkboxes
        document.querySelectorAll("input[name='selected_agents']").forEach(box => box.checked = false);
        
        // Clear results
        elements.resultContent.classList.add("hidden");
        elements.resultLoading.classList.add("hidden");
        elements.resultPlaceholder.classList.remove("hidden");
        
        // Reset risk glow styling on card
        const resultContainer = document.getElementById("detection-result-container");
        resultContainer.className = resultContainer.className.replace(/risk-glow-\w+/g, "").trim();
    });

    // --- Render Analysis Results Card ---
    function renderAnalysisResults(data) {
        elements.resultPlaceholder.classList.add("hidden");
        elements.resultLoading.classList.add("hidden");
        elements.resultContent.classList.remove("hidden");
        
        // Set Risk badge level
        elements.verdictRiskBadge.className = `risk-badge risk-${data.overall_risk}`;
        elements.verdictRiskBadge.textContent = `${data.overall_risk} RISK`;
        
        // Apply dynamic risk glow to the container card
        const resultContainer = document.getElementById("detection-result-container");
        resultContainer.className = resultContainer.className
            .replace(/risk-glow-\w+/g, "").trim();
        resultContainer.classList.add(`risk-glow-${data.overall_risk}`);
        
        // Apply risk color to recommendation card border
        const recCard = document.querySelector(".verdict-recommendation-card");
        if (recCard) {
            recCard.className = recCard.className.replace(/risk-\w+/g, "").trim();
            recCard.classList.add(`risk-${data.overall_risk}`);
        }
        
        // Set info
        elements.verdictCategory.textContent = data.input_type;

        
        // Status with color indication
        elements.verdictStatus.textContent = data.analysis_status;
        elements.verdictStatus.className = "value";
        if (data.analysis_status === "success") elements.verdictStatus.classList.add("text-success");
        else if (data.analysis_status === "partial_success") elements.verdictStatus.classList.add("text-warning");
        else elements.verdictStatus.classList.add("text-danger");
        
        const count = data.selected_agents ? data.selected_agents.length : 0;
        elements.verdictAgentsUsed.textContent = `${count} Sub-Agent(s) Executed`;
        
        // Set recommendation
        elements.verdictRecommendation.textContent = data.recommendation;
        
        // Set next steps list
        elements.verdictNextSteps.innerHTML = "";
        data.next_steps.forEach(step => {
            const li = document.createElement("li");
            li.textContent = step;
            elements.verdictNextSteps.appendChild(li);
        });
        
        // Set agent detailed breakdown cards
        elements.verdictSubAgentCards.innerHTML = "";
        
        const resultsMap = data.agent_results || {};
        const agentNames = Object.keys(resultsMap);
        
        if (agentNames.length === 0) {
            elements.verdictSubAgentCards.innerHTML = `
                <div class="text-muted text-sm text-center">No individual agent reports generated.</div>
            `;
        } else {
            agentNames.forEach(name => {
                const report = resultsMap[name];
                const card = document.createElement("div");
                card.className = "agent-assessment-card";
                
                // Color for agent confidence
                const scorePct = Math.round(report.confidence * 100);
                
                let riskClass = "badge-info";
                if (report.risk_level === "LOW") riskClass = "badge-success";
                if (report.risk_level === "MEDIUM") riskClass = "badge-warning";
                if (report.risk_level === "HIGH" || report.risk_level === "CRITICAL") riskClass = "badge-danger";
                
                let findingsList = "";
                if (report.findings && report.findings.length > 0) {
                    findingsList = `<ul class="agent-assessment-findings">` +
                        report.findings.map(f => `<li>${f}</li>`).join("") +
                        `</ul>`;
                } else {
                    findingsList = `<p class="text-sm text-muted">No specific threat patterns isolated.</p>`;
                }
                
                card.innerHTML = `
                    <div class="agent-assessment-header">
                        <span class="agent-assessment-name">${name}</span>
                        <div class="agent-assessment-meta">
                            <span class="badge ${riskClass}">${report.risk_level}</span>
                            <span class="badge badge-info">Conf: ${scorePct}%</span>
                        </div>
                    </div>
                    ${findingsList}
                `;
                elements.verdictSubAgentCards.appendChild(card);
            });
        }
    }

    // --- Run All Scenarios (Batch Analysis) ---
    elements.btnRunAllScenarios.addEventListener("click", async () => {
        elements.batchResultsCard.classList.remove("hidden");
        elements.batchProgressFill.style.width = "0%";
        elements.batchResultsTbody.innerHTML = `
            <tr><td colspan="6" class="text-center">Initializing batch coordinator... Running all 7 capstones sequentially.</td></tr>
        `;
        
        showToast("Initiating batch scenarios test...", "info");
        
        try {
            // Animate progress to show sequential feel
            let progress = 10;
            const progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += 5;
                    elements.batchProgressFill.style.width = `${progress}%`;
                }
            }, 300);

            const res = await fetch("/api/run-all", { method: "POST" });
            clearInterval(progressInterval);
            
            if (!res.ok) throw new Error("Batch execution failed on backend.");
            const data = await res.json();
            
            elements.batchProgressFill.style.width = "100%";
            elements.batchResultsTbody.innerHTML = "";
            
            data.results.forEach((item) => {
                const tr = document.createElement("tr");
                
                if (item.error) {
                    tr.innerHTML = `
                        <td>${item.index}</td>
                        <td class="text-muted italic">"${item.scenario.substring(0, 75)}..."</td>
                        <td>UNKNOWN</td>
                        <td><span class="badge badge-danger">ERROR</span></td>
                        <td><span class="text-critical">Execution Failed</span></td>
                        <td>-</td>
                    `;
                } else {
                    const resp = item.response;
                    
                    let riskClass = "text-safe";
                    if (resp.overall_risk === "MEDIUM") riskClass = "text-high";
                    if (resp.overall_risk === "HIGH" || resp.overall_risk === "CRITICAL") riskClass = "text-critical";
                    
                    // Add result to history so analytics can parse it
                    const historyItem = {
                        timestamp: new Date().toLocaleTimeString(),
                        query: item.scenario,
                        category: resp.input_type,
                        risk: resp.overall_risk,
                        response: resp,
                        duration: "0.50"
                    };
                    state.history.unshift(historyItem);
                    
                    tr.innerHTML = `
                        <td>${item.index}</td>
                        <td class="text-muted font-sans" title="${item.scenario}">"${item.scenario.substring(0, 75)}..."</td>
                        <td class="text-uppercase"><span class="badge badge-info">${resp.input_type}</span></td>
                        <td><span class="badge text-uppercase ${resp.overall_risk === 'LOW' ? 'badge-success' : resp.overall_risk === 'MEDIUM' ? 'badge-warning' : 'badge-danger'}">${resp.overall_risk}</span></td>
                        <td><span class="${riskClass} font-sans font-weight-700">${resp.analysis_status}</span></td>
                        <td>
                            <button class="btn btn-secondary btn-small btn-inspect-scenario" data-scenario-text="${encodeURIComponent(item.scenario)}">
                                Inspect
                            </button>
                        </td>
                    `;
                }
                elements.batchResultsTbody.appendChild(tr);
            });
            
            // Attach event listener to inspect buttons
            document.querySelectorAll(".btn-inspect-scenario").forEach(btn => {
                btn.addEventListener("click", () => {
                    const text = decodeURIComponent(btn.getAttribute("data-scenario-text"));
                    elements.inputText.value = text;
                    window.location.hash = "detection";
                    setTimeout(() => {
                        elements.formDetection.dispatchEvent(new Event("submit"));
                    }, 150);
                });
            });
            
            updateStatsAndAnalytics();
            showToast("Batch scenarios run complete!", "success");
            
        } catch (err) {
            console.error(err);
            elements.batchResultsTbody.innerHTML = `
                <tr><td colspan="6" class="text-center text-critical">Batch Run Error: ${err.message}</td></tr>
            `;
            showToast(`Batch execution failed: ${err.message}`, "error");
        }
    });

    elements.btnCloseBatchReport.addEventListener("click", () => {
        elements.batchResultsCard.classList.add("hidden");
    });

    // --- Statistics & Analytics Update ---
    function updateStatsAndAnalytics() {
        const total = state.history.length;
        elements.statQueriesCount.textContent = total;
        elements.analTotalRuns.textContent = total;
        
        let critical = 0;
        let high = 0;
        let medium = 0;
        let low = 0;
        let confidenceSum = 0;
        let confidenceCount = 0;
        
        state.history.forEach(item => {
            if (item.risk === "CRITICAL") critical++;
            else if (item.risk === "HIGH") high++;
            else if (item.risk === "MEDIUM") medium++;
            else if (item.risk === "LOW") low++;
            
            // Calculate avg confidence
            const results = item.response.agent_results || {};
            Object.values(results).forEach(r => {
                confidenceSum += r.confidence;
                confidenceCount++;
            });
        });
        
        elements.statThreatsCount.textContent = critical + high;
        elements.analCriticalRuns.textContent = critical;
        elements.analHighRuns.textContent = high;
        elements.analSafeRuns.textContent = medium + low;
        
        const avgConf = confidenceCount > 0 ? (confidenceSum / confidenceCount * 100).toFixed(1) : "0.0";
        elements.statAvgConfidence.textContent = `${avgConf}%`;
        
        // Distribution percent rates
        const critPct = total > 0 ? Math.round(critical / total * 100) : 0;
        const highPct = total > 0 ? Math.round(high / total * 100) : 0;
        const medPct = total > 0 ? Math.round(medium / total * 100) : 0;
        const lowPct = total > 0 ? Math.round(low / total * 100) : 0;
        
        elements.distCriticalPct.textContent = `${critPct}%`;
        elements.distCriticalFill.style.width = `${critPct}%`;
        
        elements.distHighPct.textContent = `${highPct}%`;
        elements.distHighFill.style.width = `${highPct}%`;
        
        elements.distMediumPct.textContent = `${medPct}%`;
        elements.distMediumFill.style.width = `${medPct}%`;
        
        elements.distLowPct.textContent = `${lowPct}%`;
        elements.distLowFill.style.width = `${lowPct}%`;
        
        // Render History Table
        elements.historyTbody.innerHTML = "";
        
        if (state.history.length === 0) {
            elements.historyTbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">No runs registered in this session. Go to Fraud Detection to run.</td>
                </tr>
            `;
        } else {
            state.history.forEach((item, index) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${item.timestamp}</td>
                    <td class="font-sans" title="${item.query}">"${item.query.substring(0, 60)}${item.query.length > 60 ? '...' : ''}"</td>
                    <td class="text-uppercase"><span class="badge badge-info">${item.category}</span></td>
                    <td><span class="badge ${item.risk === 'LOW' ? 'badge-success' : item.risk === 'MEDIUM' ? 'badge-warning' : 'badge-danger'}">${item.risk}</span></td>
                    <td>
                        <button class="btn btn-secondary btn-small btn-view-hist" data-index="${index}">View</button>
                    </td>
                `;
                elements.historyTbody.appendChild(tr);
            });
            
            // Attach history inspect action
            document.querySelectorAll(".btn-view-hist").forEach(btn => {
                btn.addEventListener("click", () => {
                    const index = parseInt(btn.getAttribute("data-index"));
                    const histItem = state.history[index];
                    
                    elements.inputText.value = histItem.query;
                    window.location.hash = "detection";
                    renderAnalysisResults(histItem.response);
                });
            });
        }
    }

    elements.btnClearHistory.addEventListener("click", () => {
        state.history = [];
        updateStatsAndAnalytics();
        showToast("History log cleared.", "info");
    });

    // --- Logs Console Streams ---
    async function startLogsPolling() {
        if (state.pollingInterval) return;
        
        // Load logs immediately
        await fetchLogs();
        
        // Poll every 2 seconds
        state.pollingInterval = setInterval(fetchLogs, 2000);
        elements.logsStatusText.textContent = "Live Feed Connected";
        elements.logsStatusText.className = "text-muted text-sm font-sans";
    }

    function stopLogsPolling() {
        if (state.pollingInterval) {
            clearInterval(state.pollingInterval);
            state.pollingInterval = null;
            elements.logsStatusText.textContent = "Paused";
            elements.logsStatusText.className = "text-muted text-sm font-sans italic";
        }
    }

    async function fetchLogs() {
        const level = elements.logsLevelFilter.value;
        try {
            const res = await fetch(`/api/logs?level=${level}`);
            if (!res.ok) throw new Error("Could not poll backend logs.");
            const data = await res.json();
            
            renderLogsConsole(data.logs);
        } catch (err) {
            console.error(err);
        }
    }

    function renderLogsConsole(logs) {
        elements.logsConsole.innerHTML = "";
        
        if (logs.length === 0) {
            elements.logsConsole.innerHTML = `
                <div class="log-line text-muted">[CONSOLE] No backend logs matching filter. Trigger tests to generate backend activity.</div>
            `;
            elements.logsCountBadge.textContent = 0;
            return;
        }
        
        elements.logsCountBadge.textContent = logs.length;
        
        logs.forEach(log => {
            const line = document.createElement("div");
            line.className = `log-line ${log.level}`;
            line.innerHTML = `
                <span class="log-line-time">${log.timestamp}</span>
                <span class="log-line-level">[${log.level}]</span>
                <span class="log-line-logger font-sans text-muted">(${log.logger})</span>
                <span class="log-line-msg">${log.message}</span>
            `;
            elements.logsConsole.appendChild(line);
        });
        
        if (state.logsAutoScroll) {
            elements.logsConsole.scrollTop = elements.logsConsole.scrollHeight;
        }
    }

    elements.btnClearLogs.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/logs/clear", { method: "POST" });
            if (!res.ok) throw new Error("Clear call failed.");
            elements.logsConsole.innerHTML = `<div class="log-line text-muted">[SYSTEM] Console logs cleared.</div>`;
            elements.logsCountBadge.textContent = 0;
            showToast("Backend logs cleared", "info");
        } catch (err) {
            showToast("Failed to clear logs", "error");
        }
    });

    elements.btnToggleLogsScroll.addEventListener("click", () => {
        state.logsAutoScroll = !state.logsAutoScroll;
        elements.btnToggleLogsScroll.classList.toggle("btn-primary", state.logsAutoScroll);
        elements.btnToggleLogsScroll.classList.toggle("btn-secondary", !state.logsAutoScroll);
        showToast(`Console Autoscroll ${state.logsAutoScroll ? 'Enabled' : 'Disabled'}`, "info");
    });

    elements.logsLevelFilter.addEventListener("change", () => {
        fetchLogs();
    });

    elements.btnRefreshDashboard.addEventListener("click", () => {
        loadBackendMetadata();
        showToast("Stats refreshed", "info");
    });

    // --- Startup ---
    loadBackendMetadata();
});
