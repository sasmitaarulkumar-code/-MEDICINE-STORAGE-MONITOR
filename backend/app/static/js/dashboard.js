// ==============================================================================
// MEDGUARD — Operational Intelligence Dashboard Client
// ==============================================================================

let currentStorageUnits = [];
let activeUnitId = 1;
let ws = null;
let audioEnabled = true;

let tempChart = null;
let humidChart = null;
let riskChart = null;

// Audio Context for synthetic alert beeps
let audioCtx = null;

function playAcousticAlarm(beepCount = 2, freq = 880) {
    if (!audioEnabled) return;
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        for (let i = 0; i < beepCount; i++) {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime + i * 0.25);
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime + i * 0.25);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + i * 0.25 + 0.18);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(audioCtx.currentTime + i * 0.25);
            osc.stop(audioCtx.currentTime + i * 0.25 + 0.2);
        }
    } catch (e) {
        console.warn("Audio alarm playback prevented:", e);
    }
}

function toggleAudio() {
    audioEnabled = !audioEnabled;
    const icon = document.getElementById('audio-icon');
    if (audioEnabled) {
        icon.className = "fa-solid fa-volume-high text-slate-600";
    } else {
        icon.className = "fa-solid fa-volume-xmark text-rose-500";
    }
}

// ------------------------------------------------------------------------------
// Initialization & Chart Setup
// ------------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
    initCharts();
    await loadStorageUnits();
    await loadActiveAlerts();
    connectWebSocket();
    // Poll alerts every 10s as a fallback
    setInterval(loadActiveAlerts, 10000);
});

function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        scales: {
            x: {
                grid: { display: false },
                ticks: { font: { size: 10 }, maxTicksLimit: 8 }
            },
            y: {
                grid: { color: '#f1f5f9' },
                ticks: { font: { size: 10 } }
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: { padding: 8, cornerRadius: 8 }
        }
    };

    // 1. Temperature Chart
    const ctxTemp = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(ctxTemp, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                },
                {
                    label: 'Max Threshold (8°C)',
                    data: [],
                    borderColor: '#f43f5e',
                    borderDash: [5, 5],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Min Threshold (2°C)',
                    data: [],
                    borderColor: '#38bdf8',
                    borderDash: [5, 5],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: { ...commonOptions.scales.y, suggestedMin: 0, suggestedMax: 12 }
            }
        }
    });

    // 2. Humidity Chart
    const ctxHumid = document.getElementById('humidChart').getContext('2d');
    humidChart = new Chart(ctxHumid, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humidity (%)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 1.5
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: { ...commonOptions.scales.y, min: 20, max: 85 }
            }
        }
    });

    // 3. Risk Chart
    const ctxRisk = document.getElementById('riskChart').getContext('2d');
    riskChart = new Chart(ctxRisk, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Risk Score (0-100)',
                data: [],
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 1.5
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: { ...commonOptions.scales.y, min: 0, max: 100 }
            }
        }
    });
}

// ------------------------------------------------------------------------------
// Load Storage Units & Telemetry History
// ------------------------------------------------------------------------------
async function loadStorageUnits() {
    try {
        const resp = await fetch('/api/v1/storage-units');
        if (!resp.ok) return;
        currentStorageUnits = await resp.json();
        renderStorageTabs();
        if (currentStorageUnits.length > 0) {
            selectStorageUnit(activeUnitId || currentStorageUnits[0].id);
        }
    } catch (e) {
        console.error("Error loading storage units:", e);
    }
}

function renderStorageTabs() {
    const container = document.getElementById('unit-tabs-container');
    container.innerHTML = '';

    currentStorageUnits.forEach(u => {
        const isActive = u.id === activeUnitId;
        const statusColors = {
            'SAFE': 'border-emerald-200 text-emerald-700 bg-emerald-50',
            'CAUTION': 'border-amber-200 text-amber-700 bg-amber-50',
            'HIGH_RISK': 'border-orange-200 text-orange-700 bg-orange-50',
            'CRITICAL': 'border-rose-200 text-rose-700 bg-rose-50'
        };
        const pillStyle = statusColors[u.status] || 'border-slate-200 text-slate-700 bg-slate-50';

        const btn = document.createElement('button');
        btn.onclick = () => selectStorageUnit(u.id);
        btn.className = `px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 border whitespace-nowrap ${
            isActive 
                ? 'bg-slate-900 text-white border-slate-900 shadow-md' 
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
        }`;

        btn.innerHTML = `
            <span>${u.name}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full font-black border ${isActive ? 'bg-slate-800 text-emerald-400 border-slate-700' : pillStyle}">
                ${u.status}
            </span>
        `;
        container.appendChild(btn);
    });
}

async function selectStorageUnit(unitId) {
    activeUnitId = unitId;
    renderStorageTabs();
    const unit = currentStorageUnits.find(u => u.id === unitId);
    if (!unit) return;

    // Update range labels
    document.getElementById('lbl-temp-range').textContent = `${unit.default_min_temp}°C – ${unit.default_max_temp}°C`;
    document.getElementById('lbl-humid-limit').textContent = `${unit.default_max_humidity}%`;

    // Load time-series history
    try {
        const resp = await fetch(`/api/v1/telemetry/history/${unitId}?limit=25`);
        if (resp.ok) {
            const history = await resp.json();
            updateChartHistory(history, unit);
            if (history.length > 0) {
                const latest = history[history.length - 1];
                updateMetricCards({
                    temperature: latest.temperature,
                    humidity: latest.humidity,
                    light_lux: latest.light_lux,
                    door_open: latest.door_open,
                    power_connected: latest.power_connected,
                    battery_level: latest.battery_level,
                    risk_score: unit.current_risk_score,
                    status: unit.status
                }, unit);
            }
        }
    } catch (e) {
        console.error("Error loading telemetry history:", e);
    }

    // Refresh affected count
    checkAffectedInventoryCount(unitId);
}

function updateChartHistory(history, unit) {
    const labels = history.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    const temps = history.map(h => h.temperature);
    const humids = history.map(h => h.humidity);
    const maxLimits = history.map(() => unit.default_max_temp);
    const minLimits = history.map(() => unit.default_min_temp);

    // Update Temp Chart
    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temps;
    tempChart.data.datasets[1].data = maxLimits;
    tempChart.data.datasets[2].data = minLimits;
    tempChart.update('none');

    // Update Humid Chart
    humidChart.data.labels = labels;
    humidChart.data.datasets[0].data = humids;
    humidChart.update('none');

    // Update Risk Chart with simulated points
    const risks = history.map((_, i) => Math.min(100, Math.max(5, (unit.current_risk_score || 12) + (i % 3 - 1) * 2)));
    riskChart.data.labels = labels;
    riskChart.data.datasets[0].data = risks;
    riskChart.update('none');
}

// ------------------------------------------------------------------------------
// Metric Cards & Banner Updates
// ------------------------------------------------------------------------------
function updateMetricCards(data, unit) {
    // 1. Temperature
    const tVal = document.getElementById('val-temperature');
    tVal.textContent = data.temperature.toFixed(1);
    const isTempSafe = data.temperature >= unit.default_min_temp && data.temperature <= unit.default_max_temp;
    tVal.className = `text-3xl font-black ${isTempSafe ? 'text-slate-900' : 'text-rose-600'}`;

    // 2. Humidity
    const hVal = document.getElementById('val-humidity');
    hVal.textContent = data.humidity.toFixed(0);

    // 3. Light
    const lVal = document.getElementById('val-light');
    lVal.textContent = data.light_lux ? data.light_lux.toFixed(0) : '0';
    const lStatus = document.getElementById('lbl-light-status');
    if (data.light_lux > 150 || data.door_open) {
        lStatus.textContent = "Light Intrusion!";
        lStatus.className = "font-bold text-amber-600";
    } else {
        lStatus.textContent = "Dark / Sealed";
        lStatus.className = "font-bold text-emerald-600";
    }

    // 4. Door Latch
    const dVal = document.getElementById('val-door');
    const dIcon = document.getElementById('icon-door');
    if (data.door_open) {
        dVal.textContent = "OPEN";
        dVal.className = "text-2xl font-black text-rose-600 animate-pulse";
        dIcon.className = "fa-solid fa-door-open text-rose-500";
    } else {
        dVal.textContent = "CLOSED";
        dVal.className = "text-2xl font-black text-emerald-600";
        dIcon.className = "fa-solid fa-door-closed text-slate-400";
    }

    // 5. Power
    const pVal = document.getElementById('val-power');
    const pIcon = document.getElementById('icon-power');
    const emgBanner = document.getElementById('emergency-banner');
    const emgText = document.getElementById('emergency-banner-text');

    if (!data.power_connected) {
        pVal.textContent = "POWER CUT";
        pVal.className = "text-xl font-black text-rose-600 animate-pulse";
        pIcon.className = "fa-solid fa-triangle-exclamation text-rose-600";
        emgBanner.classList.remove('hidden');
        emgText.textContent = "POWER INTERRUPTION DETECTED: UNIT RUNNING ON BACKUP BATTERY";
        playAcousticAlarm(3, 440);
    } else {
        pVal.textContent = "HEALTHY";
        pVal.className = "text-xl font-black text-emerald-600";
        pIcon.className = "fa-solid fa-plug-circle-bolt text-emerald-500";
        if (data.status !== "CRITICAL") {
            emgBanner.classList.add('hidden');
        }
    }

    // 6. Risk Score
    const rVal = document.getElementById('val-risk-score');
    const rBadge = document.getElementById('badge-risk-status');
    const rSub = document.getElementById('lbl-risk-subtext');
    const rFill = document.getElementById('bar-risk-fill');
    const rCard = document.getElementById('card-risk');

    const score = data.risk_score || 0;
    rVal.textContent = Math.round(score);
    rBadge.textContent = data.status;
    rFill.style.width = `${Math.min(100, Math.max(8, score))}%`;

    // Remove glows
    rCard.classList.remove('danger-glow', 'caution-glow');

    if (data.status === "SAFE") {
        rVal.className = "text-3xl font-black text-emerald-600";
        rBadge.className = "ml-auto text-[10px] font-black uppercase px-2 py-0.5 rounded bg-emerald-100 text-emerald-800";
        rSub.textContent = "All Optimal";
        rSub.className = "font-bold text-emerald-700";
        rFill.className = "bg-emerald-500 h-full transition-all";
    } else if (data.status === "CAUTION") {
        rVal.className = "text-3xl font-black text-amber-600";
        rBadge.className = "ml-auto text-[10px] font-black uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800";
        rSub.textContent = "Approaching Limit";
        rSub.className = "font-bold text-amber-700";
        rFill.className = "bg-amber-500 h-full transition-all";
        rCard.classList.add('caution-glow');
    } else if (data.status === "HIGH_RISK") {
        rVal.className = "text-3xl font-black text-orange-600";
        rBadge.className = "ml-auto text-[10px] font-black uppercase px-2 py-0.5 rounded bg-orange-100 text-orange-800";
        rSub.textContent = "Excursion Ongoing";
        rSub.className = "font-bold text-orange-700";
        rFill.className = "bg-orange-500 h-full transition-all";
        rCard.classList.add('danger-glow');
        playAcousticAlarm(2, 600);
    } else {
        rVal.className = "text-3xl font-black text-rose-600";
        rBadge.className = "ml-auto text-[10px] font-black uppercase px-2 py-0.5 rounded bg-rose-100 text-rose-800 animate-pulse";
        rSub.textContent = "Critical Danger";
        rSub.className = "font-bold text-rose-700";
        rFill.className = "bg-rose-600 h-full transition-all";
        rCard.classList.add('danger-glow');
        emgBanner.classList.remove('hidden');
        emgText.textContent = `CRITICAL EXCURSION DETECTED ON ${unit.name.toUpperCase()} (RISK: ${Math.round(score)}/100)`;
        playAcousticAlarm(3, 750);
    }
}

// ------------------------------------------------------------------------------
// Active Alerts Management
// ------------------------------------------------------------------------------
async function loadActiveAlerts() {
    try {
        const resp = await fetch('/api/v1/alerts/active');
        if (!resp.ok) return;
        const alerts = await resp.json();
        renderAlerts(alerts);
    } catch (e) {
        console.error("Error loading alerts:", e);
    }
}

function renderAlerts(alerts) {
    const container = document.getElementById('alerts-container');
    const countBadge = document.getElementById('count-active-alerts');
    countBadge.textContent = `${alerts.length} Active`;

    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="text-center py-10 text-slate-400">
                <i class="fa-regular fa-circle-check text-4xl text-emerald-400 mb-2"></i>
                <div class="text-sm font-semibold text-slate-600">All storage conditions safe</div>
                <div class="text-xs text-slate-400">No active excursions detected.</div>
            </div>
        `;
        return;
    }

    container.innerHTML = '';
    alerts.forEach(a => {
        const levelColors = {
            'WARNING': 'border-amber-200 bg-amber-50/70 text-amber-900 badge-amber',
            'HIGH_RISK': 'border-orange-200 bg-orange-50/70 text-orange-900 badge-orange',
            'CRITICAL': 'border-rose-200 bg-rose-50/70 text-rose-900 badge-rose'
        };
        const cardStyle = levelColors[a.alert_level] || 'border-slate-200 bg-slate-50 text-slate-900';

        const div = document.createElement('div');
        div.className = `p-3.5 rounded-xl border ${cardStyle} transition-all space-y-2`;
        div.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                    a.alert_level === 'CRITICAL' ? 'bg-rose-200 text-rose-900' : (a.alert_level === 'HIGH_RISK' ? 'bg-orange-200 text-orange-900' : 'bg-amber-200 text-amber-900')
                }">
                    ${a.alert_level}
                </span>
                <span class="text-[10px] text-slate-500 font-medium">
                    ${new Date(a.triggered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
            <div class="text-xs font-bold text-slate-900">${a.description}</div>
            <div class="text-[11px] text-slate-600 bg-white/60 p-2 rounded-lg border border-slate-200/50">
                <strong>Action:</strong> ${a.recommended_action}
            </div>
            <div class="flex items-center justify-end space-x-2 pt-1">
                ${a.status === 'ACTIVE' ? `
                    <button onclick="openAckModal(${a.id})" class="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 transition">
                        <i class="fa-solid fa-signature mr-1 text-emerald-600"></i> Acknowledge
                    </button>
                ` : `
                    <span class="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                        <i class="fa-solid fa-check mr-1"></i> Acknowledged
                    </span>
                `}
                <button onclick="resolveAlert(${a.id})" class="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-slate-900 hover:bg-slate-800 text-white transition">
                    Resolve
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

// ------------------------------------------------------------------------------
// WebSockets Hub & Real-time Broadcast Handling
// ------------------------------------------------------------------------------
function connectWebSocket() {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${window.location.host}/api/v1/ws/live`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        document.getElementById('ws-indicator').className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200";
        document.getElementById('ws-text').textContent = "Live Telemetry";
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleWebSocketMessage(msg);
        } catch (e) {
            console.error("WS Parse Error:", e);
        }
    };

    ws.onclose = () => {
        document.getElementById('ws-indicator').className = "flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200";
        document.getElementById('ws-text').textContent = "Reconnecting...";
        setTimeout(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(msg) {
    if (msg.event_type === "TELEMETRY_UPDATE" || msg.event_type === "DEMO_SCENARIO_APPLIED") {
        // Check if message belongs to currently active storage unit
        if (msg.storage_unit_id === activeUnitId) {
            const unit = currentStorageUnits.find(u => u.id === activeUnitId);
            if (unit) {
                unit.current_risk_score = msg.risk_score;
                unit.status = msg.status;
                unit.power_status = msg.power_connected;
                unit.door_open_state = msg.door_open;

                updateMetricCards(msg, unit);

                // Append new point to charts
                const timeLabel = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                appendChartPoint(tempChart, timeLabel, msg.temperature, unit.default_max_temp, unit.default_min_temp);
                appendChartPoint(humidChart, timeLabel, msg.humidity);
                appendChartPoint(riskChart, timeLabel, msg.risk_score);

                // Show predictive early warning if present
                if (msg.trend && msg.trend.has_warning) {
                    showAIBanner({
                        title: "Predictive Early Warning — Continuous Drift Detected",
                        message: msg.trend.description,
                        action: "Inspect door seals, check condenser ventilation, and prepare secondary cold storage transfer.",
                        confidence: msg.trend.confidence_percent,
                        level: "CAUTION"
                    });
                } else if (msg.anomaly && msg.anomaly.is_anomaly) {
                    showAIBanner({
                        title: "Statistical Anomaly Detected (Z-Score: " + msg.anomaly.z_score + ")",
                        message: msg.anomaly.details,
                        action: "Check sensor probe attachment and inspect for rapid internal thermal shock.",
                        confidence: 90,
                        level: "WARNING"
                    });
                } else {
                    hideAIBanner();
                }

                // Refresh affected batch count
                checkAffectedInventoryCount(activeUnitId);
            }
        }
        // Refresh unit tabs & active alerts
        loadStorageUnits();
        loadActiveAlerts();
    } else if (msg.event_type === "ALERT_ACKNOWLEDGED" || msg.event_type === "ALERT_RESOLVED" || msg.event_type === "DEMO_RESET") {
        loadActiveAlerts();
        loadStorageUnits();
    }
}

function appendChartPoint(chart, label, value, maxLimit = null, minLimit = null) {
    if (!chart) return;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    if (maxLimit !== null) chart.data.datasets[1].data.push(maxLimit);
    if (minLimit !== null) chart.data.datasets[2].data.push(minLimit);

    if (chart.data.labels.length > 25) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
        if (maxLimit !== null) chart.data.datasets[1].data.shift();
        if (minLimit !== null) chart.data.datasets[2].data.shift();
    }
    chart.update('none');
}

function showAIBanner(info) {
    const banner = document.getElementById('ai-alert-banner');
    const title = document.getElementById('ai-alert-title');
    const msg = document.getElementById('ai-alert-message');
    const action = document.getElementById('ai-alert-action');
    const conf = document.getElementById('ai-alert-confidence');
    const wrap = document.getElementById('ai-alert-icon-wrap');

    banner.classList.remove('hidden');
    title.textContent = info.title;
    msg.textContent = info.message;
    action.innerHTML = `<i class="fa-solid fa-circle-info mr-1 text-emerald-600"></i> Recommended Action: ${info.action}`;
    conf.textContent = `Confidence: ${info.confidence}%`;

    if (info.level === 'CAUTION') {
        banner.className = "rounded-xl p-4 border bg-amber-50 border-amber-200 transition-all duration-300 flex items-start space-x-3";
        wrap.className = "w-9 h-9 rounded-lg flex items-center justify-center text-white bg-amber-500 flex-shrink-0 mt-0.5";
    } else {
        banner.className = "rounded-xl p-4 border bg-rose-50 border-rose-200 transition-all duration-300 flex items-start space-x-3";
        wrap.className = "w-9 h-9 rounded-lg flex items-center justify-center text-white bg-rose-600 flex-shrink-0 mt-0.5";
    }
}

function hideAIBanner() {
    document.getElementById('ai-alert-banner').classList.add('hidden');
}

// ------------------------------------------------------------------------------
// Affected Inventory Modal
// ------------------------------------------------------------------------------
async function checkAffectedInventoryCount(unitId) {
    try {
        const resp = await fetch(`/api/v1/inventory/affected/${unitId}`);
        if (!resp.ok) return;
        const report = await resp.json();
        document.getElementById('btn-affected-count').textContent = report.affected_batches_count;
    } catch (e) {
        console.error("Error fetching affected count:", e);
    }
}

async function openAffectedInventoryModal() {
    const modal = document.getElementById('modal-affected-inventory');
    const tbody = document.getElementById('modal-affected-table-body');
    const unitTitle = document.getElementById('modal-affected-unit');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-6 text-slate-400">Loading affected batches...</td></tr>';
    modal.classList.remove('hidden');

    try {
        const resp = await fetch(`/api/v1/inventory/affected/${activeUnitId}`);
        if (!resp.ok) return;
        const report = await resp.json();

        unitTitle.textContent = `${report.storage_unit_name} (${report.storage_unit_code})`;
        document.getElementById('modal-affected-batch-count').textContent = report.affected_batches_count;
        document.getElementById('modal-affected-dose-count').textContent = report.total_doses_at_risk;
        document.getElementById('modal-affected-status-pill').textContent = report.risk_level;

        if (report.affected_items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-8 text-emerald-600 font-bold">
                        <i class="fa-regular fa-circle-check text-2xl block mb-1"></i>
                        No medicines currently affected. All batches within safe storage thresholds.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = '';
        report.affected_items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2.5 font-bold text-slate-900">${item.medicine_name}</td>
                <td class="px-3 py-2.5 font-mono text-slate-600">${item.batch_number}</td>
                <td class="px-3 py-2.5 font-bold">${item.quantity} doses</td>
                <td class="px-3 py-2.5 text-slate-500">${item.expiry_date}</td>
                <td class="px-3 py-2.5 text-rose-600 font-semibold">${item.deviation_description}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading affected inventory:", e);
    }
}

// ------------------------------------------------------------------------------
// Alert Acknowledgement & Resolution
// ------------------------------------------------------------------------------
function openAckModal(alertId) {
    document.getElementById('ack-alert-id').value = alertId;
    document.getElementById('ack-notes').value = '';
    document.getElementById('modal-ack-alert').classList.remove('hidden');
}

async function submitAlertAcknowledgement() {
    const alertId = document.getElementById('ack-alert-id').value;
    const notes = document.getElementById('ack-notes').value.trim();
    if (!notes) {
        alert("Please enter inspection or corrective action notes.");
        return;
    }

    try {
        const resp = await fetch(`/api/v1/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes })
        });
        if (resp.ok) {
            closeModal('modal-ack-alert');
            loadActiveAlerts();
        }
    } catch (e) {
        console.error("Error acknowledging alert:", e);
    }
}

async function resolveAlert(alertId) {
    const resolution_notes = prompt("Enter resolution summary notes (e.g. Unit inspected, latch closed properly):");
    if (!resolution_notes) return;

    try {
        const resp = await fetch(`/api/v1/alerts/${alertId}/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resolution_notes })
        });
        if (resp.ok) {
            loadActiveAlerts();
        }
    } catch (e) {
        console.error("Error resolving alert:", e);
    }
}

// ------------------------------------------------------------------------------
// Reports & Audit Modal
// ------------------------------------------------------------------------------
async function openReportModal() {
    const modal = document.getElementById('modal-report');
    const body = document.getElementById('report-modal-body');
    modal.classList.remove('hidden');
    body.innerHTML = '<div class="text-center py-8 text-slate-400">Loading audit statistics...</div>';

    try {
        const resp = await fetch(`/api/v1/reports/storage-summary?days=7`);
        if (!resp.ok) return;
        const report = await resp.json();

        body.innerHTML = '';
        report.units.forEach(u => {
            const div = document.createElement('div');
            div.className = "p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs";
            div.innerHTML = `
                <div class="flex items-center justify-between">
                    <h4 class="font-bold text-sm text-slate-900">${u.unit_name} (${u.unit_code})</h4>
                    <span class="px-2 py-0.5 rounded font-bold ${u.compliance_status === 'COMPLIANT' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                        ${u.compliance_status}
                    </span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-700 pt-1">
                    <div><strong>Avg Temp:</strong> ${u.temperature_stats.average_c}°C</div>
                    <div><strong>Max Temp:</strong> ${u.temperature_stats.maximum_c}°C</div>
                    <div><strong>Min Temp:</strong> ${u.temperature_stats.minimum_c}°C</div>
                    <div><strong>Avg Humidity:</strong> ${u.humidity_stats.average_percent}%</div>
                </div>
                <div class="pt-2 border-t border-slate-200 flex justify-between text-slate-600">
                    <span>Total Alerts: <strong>${u.incident_and_alert_metrics.total_alerts}</strong></span>
                    <span>Deviation Duration: <strong>${u.incident_and_alert_metrics.total_deviation_duration_minutes} mins</strong></span>
                    <span>Door Openings: <strong>${u.incident_and_alert_metrics.door_open_samples}</strong></span>
                </div>
            `;
            body.appendChild(div);
        });
    } catch (e) {
        console.error("Error loading report:", e);
    }
}

function downloadCSVReport() {
    window.location.href = `/api/v1/reports/export-csv?storage_unit_id=${activeUnitId}&days=7`;
}

async function openAuditModal() {
    const modal = document.getElementById('modal-audit');
    const tbody = document.getElementById('audit-table-body');
    modal.classList.remove('hidden');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-6 text-slate-400">Loading audit log...</td></tr>';

    try {
        const resp = await fetch('/api/v1/audit/logs?limit=30');
        if (!resp.ok) return;
        const logs = await resp.json();

        tbody.innerHTML = '';
        logs.forEach(l => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-3 py-2 text-slate-500 whitespace-nowrap">${new Date(l.timestamp).toLocaleString()}</td>
                <td class="px-3 py-2 font-bold text-slate-800">${l.user_name}</td>
                <td class="px-3 py-2 font-mono text-emerald-700 font-semibold">${l.action}</td>
                <td class="px-3 py-2 text-slate-600 truncate max-w-xs">${l.details || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading audit logs:", e);
    }
}

// ------------------------------------------------------------------------------
// Storage Configuration Modal
// ------------------------------------------------------------------------------
function openConfigModal() {
    const unit = currentStorageUnits.find(u => u.id === activeUnitId);
    if (!unit) return;
    document.getElementById('cfg-min-temp').value = unit.default_min_temp;
    document.getElementById('cfg-max-temp').value = unit.default_max_temp;
    document.getElementById('cfg-min-humid').value = unit.default_min_humidity;
    document.getElementById('cfg-max-humid').value = unit.default_max_humidity;
    document.getElementById('modal-config').classList.remove('hidden');
}

async function saveStorageConfig() {
    const min_temp = parseFloat(document.getElementById('cfg-min-temp').value);
    const max_temp = parseFloat(document.getElementById('cfg-max-temp').value);
    const min_humid = parseFloat(document.getElementById('cfg-min-humid').value);
    const max_humid = parseFloat(document.getElementById('cfg-max-humid').value);

    try {
        const resp = await fetch(`/api/v1/storage-units/${activeUnitId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                default_min_temp: min_temp,
                default_max_temp: max_temp,
                default_min_humidity: min_humid,
                default_max_humidity: max_humid
            })
        });
        if (resp.ok) {
            closeModal('modal-config');
            await loadStorageUnits();
        }
    } catch (e) {
        console.error("Error saving storage config:", e);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// ------------------------------------------------------------------------------
// Hackathon 3-Minute Demo Controller Execution (Section 23)
// ------------------------------------------------------------------------------
async function triggerDemoScenario(scenarioId) {
    const unit = currentStorageUnits.find(u => u.id === activeUnitId) || currentStorageUnits[0];
    const unitCode = unit ? unit.unit_code : "UNIT-A-FRIDGE";

    try {
        const resp = await fetch('/api/v1/demo/trigger-scenario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario_id: scenarioId, unit_code: unitCode })
        });
        const data = await resp.json();
        console.log(`[DEMO CONTROLLER] Scenario ${scenarioId} executed:`, data);
    } catch (e) {
        console.error("Error executing demo scenario:", e);
    }
}

async function resetDemoSystem() {
    try {
        await fetch('/api/v1/demo/reset', { method: 'POST' });
        loadActiveAlerts();
        loadStorageUnits();
        hideAIBanner();
    } catch (e) {
        console.error("Error resetting demo:", e);
    }
}

function toggleDemoMinimize() {
    const body = document.getElementById('demo-body');
    const icon = document.getElementById('demo-min-icon');
    if (body.classList.contains('hidden')) {
        body.classList.remove('hidden');
        icon.className = "fa-solid fa-chevron-down";
    } else {
        body.classList.add('hidden');
        icon.className = "fa-solid fa-chevron-up";
    }
}
