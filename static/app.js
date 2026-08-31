/* ==========================================================================
   GuardWAF Client Application Logic
   Production-Grade Autonomous AI Security Product Engine
   ========================================================================== */

(function () {
  'use strict';

  // --- State Engine ---
  const state = {
    theme: localStorage.getItem('guardwaf_theme') || 'dark',
    audio: localStorage.getItem('guardwaf_audio') !== 'false',
    activeTab: 'workspace-overview',
    auditLogs: [],
    hitlQueue: [],
    scenarios: [],
    selectedLog: null,
    cmdPaletteOpen: false,
    cmdSelectedIndex: 0,
    metrics: {
      total: 0,
      allowed: 0,
      blocked: 0,
      hitl: 0,
      rate: '0.0%'
    }
  };

  // --- Audio Synthesizer (Web Audio API) ---
  function playAudioChime(freq = 600, type = 'sine', duration = 0.15) {
    if (!state.audio) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.06, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio chime error", e);
    }
  }

  // --- Theme Management ---
  function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      themeBtn.innerHTML = state.theme === 'dark' ? '🌙 Dark Mode' : '☀️ Light Mode';
    }
  }

  function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('guardwaf_theme', state.theme);
    initTheme();
    playAudioChime(700);
  }

  function toggleAudio() {
    state.audio = !state.audio;
    localStorage.setItem('guardwaf_audio', state.audio);
    const audioBtn = document.getElementById('audio-toggle-btn');
    if (audioBtn) {
      audioBtn.innerHTML = state.audio ? '🔊 Sound: ON' : '🔇 Sound: OFF';
    }
  }

  // --- Workspace Tab Router ---
  function switchTab(tabId) {
    state.activeTab = tabId;
    document.querySelectorAll('.workspace-panel').forEach(panel => {
      panel.classList.remove('active');
    });
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.classList.remove('active');
    });

    const targetPanel = document.getElementById(tabId);
    if (targetPanel) targetPanel.classList.add('active');

    const targetBtn = document.querySelector(`[data-tab="${tabId}"]`);
    if (targetBtn) targetBtn.classList.add('active');

    playAudioChime(650);

    // Refresh tab specific data
    if (tabId === 'workspace-overview' || tabId === 'workspace-live') fetchAuditLogs();
    if (tabId === 'workspace-hitl') fetchHitlQueue();
    if (tabId === 'workspace-agent') renderAgentInspector();
    if (tabId === 'workspace-redteam') loadScenarios();
    if (tabId === 'workspace-compliance') fetchComplianceReport();
  }

  // --- SSE Realtime Stream Listener ---
  function initRealtimeStream() {
    try {
      const evtSource = new EventSource('/stream/events');
      evtSource.onmessage = function (e) {
        try {
          const data = JSON.parse(e.data);
          if (data && data.stats) {
            updateKPICounters(data.stats);
          }
        } catch (err) {}
      };
      evtSource.addEventListener('dashboard', function (e) {
        try {
          const data = JSON.parse(e.data);
          if (data && data.stats) {
            updateKPICounters(data.stats);
          }
        } catch (err) {}
      });
      evtSource.onerror = function () {
        document.getElementById('live-status-text').innerText = 'SYSTEM ONLINE (Polling)';
      };
    } catch (e) {
      console.warn("SSE init failed, fallback to HTTP polling", e);
    }
  }

  function updateKPICounters(stats) {
    if (!stats) return;
    const totalEl = document.getElementById('kpi-total-val');
    const allowedEl = document.getElementById('kpi-allowed-val');
    const blockedEl = document.getElementById('kpi-blocked-val');
    const hitlEl = document.getElementById('kpi-hitl-val');
    const rateEl = document.getElementById('kpi-rate-val');

    if (totalEl) totalEl.innerText = stats.total || state.auditLogs.length || 0;
    if (blockedEl) blockedEl.innerText = stats.blocked || 0;
    if (hitlEl) hitlEl.innerText = stats.pending_hitl || 0;
    
    const hitlBadge = document.getElementById('hitl-badge-count');
    if (hitlBadge) {
      hitlBadge.innerText = stats.pending_hitl || 0;
      hitlBadge.style.display = (stats.pending_hitl > 0) ? 'inline-block' : 'none';
    }
  }

  // --- Fetch & Render Audit Logs ---
  async function fetchAuditLogs() {
    try {
      const res = await fetch('/logs?limit=100');
      if (!res.ok) return;
      const logs = await res.json();
      state.auditLogs = logs;

      let allowed = 0, blocked = 0, hitl = 0;
      logs.forEach(l => {
        if (l.status === 'allowed') allowed++;
        if (l.status === 'blocked') blocked++;
        if (l.status === 'pending_hitl') hitl++;
      });

      const total = logs.length;
      const rate = total > 0 ? ((blocked / total) * 100).toFixed(1) + '%' : '0.0%';

      state.metrics = { total, allowed, blocked, hitl, rate };
      updateKPICounters({ total, blocked, pending_hitl: hitl });

      const totalEl = document.getElementById('kpi-total-val');
      const allowedEl = document.getElementById('kpi-allowed-val');
      const rateEl = document.getElementById('kpi-rate-val');
      if (totalEl) totalEl.innerText = total;
      if (allowedEl) allowedEl.innerText = allowed;
      if (rateEl) rateEl.innerText = rate;

      renderAuditTable('overview-logs-tbody', logs.slice(0, 10));
      renderAuditTable('live-logs-tbody', logs);
      renderAgentInspector();

      if (logs.length > 0) {
        animateGuardrailFlow(logs[0]);
      }
    } catch (err) {
      console.error("Failed to fetch logs", err);
    }
  }

  function renderAuditTable(tbodyId, logs) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!logs || logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No security events recorded yet.</td></tr>';
      return;
    }

    logs.forEach(log => {
      let badgeClass = 'badge-allowed';
      if (log.status === 'blocked') badgeClass = 'badge-blocked';
      if (log.status === 'pending_hitl') badgeClass = 'badge-pending';
      if (log.status === 'shadow_blocked') badgeClass = 'badge-shadow';

      const timeStr = log.timestamp ? log.timestamp.split('T')[1].split('.')[0] : '--:--:--';
      const paramsStr = typeof log.parameters === 'object' ? JSON.stringify(log.parameters) : (log.parameters || '{}');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:700;">#${log.id}</td>
        <td style="color:var(--text-muted);">${timeStr}</td>
        <td><strong style="color:var(--text-primary);">${log.agent_id}</strong></td>
        <td style="color:var(--brand-light); font-weight:700;">${log.tool}</td>
        <td style="max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--text-muted);">${escapeHtml(paramsStr)}</td>
        <td><span class="badge-status ${badgeClass}">${log.status}</span></td>
        <td style="font-size:0.75rem;">${log.latency_ms ? log.latency_ms.toFixed(1) + 'ms' : '1.2ms'}</td>
      `;

      tr.addEventListener('click', () => openDecisionExplainer(log));
      tbody.appendChild(tr);
    });
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // --- Guardrail Flow Matrix Animation ---
  function animateGuardrailFlow(latestLog) {
    if (!latestLog) return;
    const nodes = document.querySelectorAll('.flow-node');
    nodes.forEach(n => n.className = 'flow-node');

    // Steps: 0: Agent, 1: RateLimiter, 2: SequenceGuard, 3: DataScope, 4: ParamValidator, 5: ThreatRadar, 6: Decision
    const outcome = latestLog.status;
    const matchedRule = (latestLog.matched_rule || '').toLowerCase();

    // Node highlights
    document.getElementById('node-1')?.classList.add('active-pass');
    document.getElementById('node-2')?.classList.add('active-pass');
    document.getElementById('node-3')?.classList.add('active-pass');
    document.getElementById('node-4')?.classList.add('active-pass');
    document.getElementById('node-5')?.classList.add('active-pass');
    document.getElementById('node-6')?.classList.add('active-pass');

    const decisionNode = document.getElementById('node-7');
    if (decisionNode) {
      if (outcome === 'allowed') decisionNode.classList.add('active-pass');
      else if (outcome === 'blocked') decisionNode.classList.add('active-fail');
      else if (outcome === 'pending_hitl') decisionNode.classList.add('active-hitl');
    }

    if (outcome === 'blocked') {
      if (matchedRule.includes('rate')) document.getElementById('node-2')?.classList.replace('active-pass', 'active-fail');
      else if (matchedRule.includes('sequence')) document.getElementById('node-3')?.classList.replace('active-pass', 'active-fail');
      else if (matchedRule.includes('scope')) document.getElementById('node-4')?.classList.replace('active-pass', 'active-fail');
      else if (matchedRule.includes('blocklist') || matchedRule.includes('param')) document.getElementById('node-5')?.classList.replace('active-pass', 'active-fail');
    }
  }

  // --- Decision Explainer Drawer ---
  function openDecisionExplainer(log) {
    state.selectedLog = log;
    const drawer = document.getElementById('decision-drawer-overlay');
    const content = document.getElementById('drawer-content-box');
    if (!drawer || !content) return;

    let bannerClass = 'outcome-allow';
    let bannerTitle = 'ACTION PERMITTED BY POLICY';
    if (log.status === 'blocked') {
      bannerClass = 'outcome-block';
      bannerTitle = 'INTERCEPTED & BLOCKED BY WAF';
    } else if (log.status === 'pending_hitl') {
      bannerClass = 'outcome-hitl';
      bannerTitle = 'HUMAN APPROVAL REQUIRED (HITL)';
    }

    const paramsPretty = typeof log.parameters === 'object' ? JSON.stringify(log.parameters, null, 2) : log.parameters;

    content.innerHTML = `
      <div class="decision-outcome-banner ${bannerClass}">
        <div>
          <h3 style="font-size:1.05rem; font-weight:800;">${bannerTitle}</h3>
          <p style="font-size:0.75rem;">Security Event ID: #${log.id} | Timestamp: ${log.timestamp}</p>
        </div>
        <span class="badge-status ${bannerClass}">${log.status}</span>
      </div>

      <div class="decision-explainer-panel">
        <h4 style="font-size:0.85rem; font-weight:700; margin-bottom:0.75rem; color:var(--text-primary);">🛡️ WAF Evaluation Breakdown</h4>
        <div class="decision-trace-grid">
          <div class="trace-step-item">
            <div class="label">Agent ID</div>
            <div class="val">${log.agent_id}</div>
          </div>
          <div class="trace-step-item">
            <div class="label">Target Tool</div>
            <div class="val">${log.tool}</div>
          </div>
          <div class="trace-step-item">
            <div class="label">Matched Rule</div>
            <div class="val">${log.matched_rule || 'DEFAULT_ALLOW'}</div>
          </div>
          <div class="trace-step-item">
            <div class="label">Latency</div>
            <div class="val">${log.latency_ms ? log.latency_ms.toFixed(1) : 1.2}ms</div>
          </div>
        </div>

        <div style="margin-bottom: 1rem;">
          <div class="label" style="font-size:0.725rem; color:var(--text-muted); margin-bottom:0.35rem;">Evaluation Outcome Rationale</div>
          <div style="background:var(--bg-surface-elevated); padding:0.75rem; border-radius:var(--radius-md); font-size:0.825rem; font-family:var(--font-mono); color:var(--text-primary); border:1px solid var(--border-subtle);">
            ${log.evaluation_outcome || 'No violations detected.'}
          </div>
        </div>

        <div>
          <div class="label" style="font-size:0.725rem; color:var(--text-muted); margin-bottom:0.35rem;">Tool Request Parameters Payload</div>
          <pre class="code-block">${escapeHtml(paramsPretty)}</pre>
        </div>
      </div>
    `;

    drawer.classList.add('active');
    playAudioChime(750);
  }

  function closeDecisionExplainer() {
    const drawer = document.getElementById('decision-drawer-overlay');
    if (drawer) drawer.classList.remove('active');
  }

  // --- Visual Rule Builder ---
  function updateRuleBuilderPreview() {
    const tool = document.getElementById('rule-target-tool')?.value || 'send_email';
    const condition = document.getElementById('rule-condition-type')?.value || 'rate_limit';
    const action = document.getElementById('rule-enforcement-action')?.value || 'block';

    const diagTool = document.getElementById('diag-tool-val');
    const diagCond = document.getElementById('diag-cond-val');
    const diagAction = document.getElementById('diag-action-val');

    if (diagTool) diagTool.innerText = `Tool: ${tool}`;
    if (diagCond) diagCond.innerText = `Condition: ${condition.replace('_', ' ').toUpperCase()}`;
    if (diagAction) {
      diagAction.innerText = `Enforce: ${action.toUpperCase()}`;
      diagAction.style.borderColor = action === 'block' ? 'var(--color-block)' : action === 'require_hitl' ? 'var(--color-hitl)' : 'var(--color-allow)';
    }
  }

  async function dryRunValidatePolicy() {
    const yamlContent = document.getElementById('policy-yaml-editor')?.value || '';
    const consoleOut = document.getElementById('policy-dryrun-output');
    if (consoleOut) consoleOut.innerText = "Evaluating policy YAML against GuardWAF parser...";

    try {
      const res = await fetch('/policy/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ yaml_content: yamlContent })
      });
      const data = await res.json();
      if (consoleOut) consoleOut.innerText = JSON.stringify(data, null, 2);
      playAudioChime(850);
    } catch (err) {
      if (consoleOut) consoleOut.innerText = "Validation failed: " + err.message;
    }
  }

  // --- HITL Approval Workspace ---
  async function fetchHitlQueue() {
    try {
      let res = await fetch('/hitl/pending');
      if (!res.ok) res = await fetch('/hitl/queue');
      const items = await res.json();
      state.hitlQueue = items;

      const container = document.getElementById('hitl-queue-list');
      if (!container) return;
      container.innerHTML = '';

      updateKPICounters({ total: state.metrics.total, blocked: state.metrics.blocked, pending_hitl: items.length });

      if (!items || items.length === 0) {
        container.innerHTML = '<div class="panel-card" style="text-align:center; padding: 2.5rem; color:var(--text-muted);">✅ All HITL authorization requests have been resolved. No pending queue items.</div>';
        return;
      }

      items.forEach(item => {
        const paramsStr = typeof item.parameters === 'object' ? JSON.stringify(item.parameters, null, 2) : item.parameters;
        const reasonsStr = Array.isArray(item.risk_reasons) ? item.risk_reasons.join(', ') : item.risk_reasons || 'High-Risk Action Flagged';

        const card = document.createElement('div');
        card.className = 'hitl-request-card';
        card.innerHTML = `
          <div class="hitl-card-header">
            <div class="hitl-title-box">
              <h4>HITL Pending Authorization #${item.id} — Tool: <code style="color:var(--brand-light);">${item.tool}</code></h4>
              <p>Agent ID: <strong>${item.agent_id}</strong> | Session: <strong>${item.session_id}</strong> | Timestamp: ${item.timestamp}</p>
            </div>
            <span class="hitl-risk-flag">Risk Score: ${item.fraud_score}% (${item.risk_level})</span>
          </div>

          <div style="font-size:0.8rem; color:var(--color-hitl); font-weight:600;">
            ⚠️ Risk Evaluation Reason: ${reasonsStr}
          </div>

          <pre class="hitl-payload-box">${escapeHtml(paramsStr)}</pre>

          <div class="hitl-actions-bar">
            <input type="text" id="hitl-note-${item.id}" class="input-text" placeholder="Admin authorization rationale note..." style="flex-grow:1;">
            <button class="btn-primary" onclick="window.GuardWAF.decideHitl(${item.id}, 'approve')">✅ Approve Action</button>
            <button class="btn-danger" onclick="window.GuardWAF.decideHitl(${item.id}, 'reject')">❌ Deny Request</button>
          </div>
        `;
        container.appendChild(card);
      });
    } catch (err) {
      console.error("Failed to fetch HITL queue", err);
    }
  }

  async function decideHitl(id, decision) {
    const note = document.getElementById(`hitl-note-${id}`)?.value || `Manual admin decision: ${decision}`;
    try {
      await fetch(`/hitl/decide/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason: note })
      });
      playAudioChime(decision === 'approve' ? 900 : 250);
      fetchHitlQueue();
      fetchAuditLogs();
    } catch (err) {
      alert("Failed to submit HITL decision: " + err.message);
    }
  }

  // --- Agent & Session Inspector ---
  function renderAgentInspector() {
    const tbody = document.getElementById('agent-timeline-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!state.auditLogs || state.auditLogs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 1.5rem;">No agent session activity.</td></tr>';
      return;
    }

    const agentMap = {};
    state.auditLogs.forEach(l => {
      if (!agentMap[l.agent_id]) {
        agentMap[l.agent_id] = { total: 0, blocked: 0, hitl: 0, tools: [] };
      }
      agentMap[l.agent_id].total++;
      if (l.status === 'blocked') agentMap[l.agent_id].blocked++;
      if (l.status === 'pending_hitl') agentMap[l.agent_id].hitl++;
      if (!agentMap[l.agent_id].tools.includes(l.tool)) agentMap[l.agent_id].tools.push(l.tool);
    });

    Object.keys(agentMap).forEach(agentId => {
      const info = agentMap[agentId];
      const sequenceFlow = info.tools.join(' ➔ ');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:700; color:var(--text-primary);">${agentId}</td>
        <td><span class="badge-status badge-allowed">● Active</span></td>
        <td>${info.total} (${info.blocked} blocked, ${info.hitl} HITL)</td>
        <td style="color:var(--brand-light); font-weight:600;">${sequenceFlow}</td>
        <td><button class="btn-utility" onclick="window.GuardWAF.filterByAgent('${agentId}')">🔍 Inspect</button></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function filterByAgent(agentId) {
    const filterInput = document.getElementById('audit-search-input');
    if (filterInput) filterInput.value = agentId;
    switchTab('workspace-live');
    const filtered = state.auditLogs.filter(l => l.agent_id.includes(agentId));
    renderAuditTable('live-logs-tbody', filtered);
  }

  // --- AI Red-Teaming Workbench ---
  async function loadScenarios() {
    try {
      const res = await fetch('/redteam/scenarios');
      if (!res.ok) return;
      const scenarios = await res.json();
      state.scenarios = scenarios;

      const container = document.getElementById('redteam-scenarios-grid');
      if (!container) return;
      container.innerHTML = '';

      scenarios.forEach(sc => {
        const badgeClass = sc.type === 'legitimate' ? 'badge-allowed' : 'badge-blocked';
        const card = document.createElement('div');
        card.className = 'panel-card';
        card.style.cursor = 'pointer';
        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <h4 style="font-size:0.9rem; font-weight:700;">${sc.name}</h4>
            <span class="badge-status ${badgeClass}">${sc.owasp}</span>
          </div>
          <p style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.5rem;">${sc.description}</p>
          <span style="font-size:0.7rem; font-family:var(--font-mono); color:var(--brand-light);">Target Tool: ${sc.sample_tool}</span>
        `;
        card.addEventListener('click', () => selectScenario(sc.id));
        container.appendChild(card);
      });
    } catch (err) {
      console.error("Failed to load red-team scenarios", err);
    }
  }

  async function selectScenario(id) {
    try {
      const res = await fetch(`/redteam/simulate/${id}`, { method: 'POST' });
      const data = await res.json();
      const consoleOut = document.getElementById('redteam-output-box');
      if (consoleOut) consoleOut.innerText = JSON.stringify(data, null, 2);

      if (data.result && data.result.status === 'blocked') {
        playAudioChime(300, 'sawtooth', 0.3);
      } else {
        playAudioChime(950, 'sine', 0.2);
      }

      fetchAuditLogs();
    } catch (err) {
      alert("Scenario execution failed: " + err.message);
    }
  }

  async function executeCustomPayload() {
    const raw = document.getElementById('custom-payload-textarea')?.value;
    const consoleOut = document.getElementById('redteam-output-box');
    try {
      const payload = JSON.parse(raw);
      const res = await fetch('/proxy/tool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (consoleOut) consoleOut.innerText = JSON.stringify(data, null, 2);
      fetchAuditLogs();
    } catch (err) {
      alert("Invalid JSON format in payload text box!");
    }
  }

  // --- Compliance Report ---
  async function fetchComplianceReport() {
    try {
      const res = await fetch('/compliance/report');
      if (!res.ok) return;
      const data = await res.json();
      const box = document.getElementById('compliance-report-box');
      if (box) box.innerText = data.report_markdown;
    } catch (err) {
      console.error("Failed to fetch compliance report", err);
    }
  }

  function downloadComplianceReport() {
    const content = document.getElementById('compliance-report-box')?.innerText || '';
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'GuardWAF_SOC2_OWASP_Compliance_Audit.md';
    a.click();
  }

  function clearLogs() {
    if (confirm("Are you sure you want to clear all audit logs and HITL queues?")) {
      fetch('/admin/clear', { method: 'POST' }).then(() => {
        fetchAuditLogs();
        fetchHitlQueue();
      });
    }
  }

  // --- Command Palette Engine ---
  const cmdActions = [
    { title: '🛡️ View Security Overview', action: () => switchTab('workspace-overview'), shortcut: '⌘1' },
    { title: '⚡ Open Live Protection Stream', action: () => switchTab('workspace-live'), shortcut: '⌘2' },
    { title: '⚖️ Open HITL Approval Queue', action: () => switchTab('workspace-hitl'), shortcut: '⌘3' },
    { title: '🛠️ Launch Firewall Rule Builder', action: () => switchTab('workspace-rulebuilder'), shortcut: '⌘4' },
    { title: '🕵️ Inspect Agent Sessions & Audit Log', action: () => switchTab('workspace-agent'), shortcut: '⌘5' },
    { title: '🚀 Launch Red-Teaming Workbench', action: () => switchTab('workspace-redteam'), shortcut: '⌘6' },
    { title: '🚀 Simulate SQL Injection Attack', action: () => selectScenario('sql_injection'), shortcut: 'ATTACK' },
    { title: '🚀 Simulate Sequence Enforcement Bypass', action: () => selectScenario('sequence_bypass'), shortcut: 'ATTACK' },
    { title: '🌓 Toggle Dark / Light Theme', action: () => toggleTheme(), shortcut: 'THEME' },
    { title: '🗑️ Clear Database Audit Logs', action: () => clearLogs(), shortcut: 'ADMIN' },
    { title: '📥 Export SOC 2 & OWASP Report', action: () => downloadComplianceReport(), shortcut: 'DOCS' }
  ];

  function openCmdPalette() {
    state.cmdPaletteOpen = true;
    state.cmdSelectedIndex = 0;
    const backdrop = document.getElementById('cmd-palette-backdrop');
    if (backdrop) backdrop.classList.add('active');
    renderCmdItems(cmdActions);
    document.getElementById('cmd-search-input')?.focus();
  }

  function closeCmdPalette() {
    state.cmdPaletteOpen = false;
    const backdrop = document.getElementById('cmd-palette-backdrop');
    if (backdrop) backdrop.classList.remove('active');
  }

  function renderCmdItems(items) {
    const list = document.getElementById('cmd-items-list');
    if (!list) return;
    list.innerHTML = '';

    items.forEach((item, index) => {
      const div = document.createElement('div');
      div.className = `cmd-item ${index === state.cmdSelectedIndex ? 'selected' : ''}`;
      div.innerHTML = `
        <span>${item.title}</span>
        <span class="cmd-item-shortcut">${item.shortcut}</span>
      `;
      div.addEventListener('click', () => {
        item.action();
        closeCmdPalette();
      });
      list.appendChild(div);
    });
  }

  // --- Keyboard Shortcuts & Initialization ---
  function initKeyboard() {
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (state.cmdPaletteOpen) closeCmdPalette();
        else openCmdPalette();
      } else if (e.key === 'Escape') {
        closeCmdPalette();
        closeDecisionExplainer();
      }
    });

    document.getElementById('cmd-search-input')?.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const filtered = cmdActions.filter(a => a.title.toLowerCase().includes(query));
      state.cmdSelectedIndex = 0;
      renderCmdItems(filtered);
    });
  }

  // --- Global Namespace API Export ---
  window.GuardWAF = {
    toggleTheme,
    toggleAudio,
    switchTab,
    fetchAuditLogs,
    openDecisionExplainer,
    closeDecisionExplainer,
    updateRuleBuilderPreview,
    dryRunValidatePolicy,
    fetchHitlQueue,
    decideHitl,
    filterByAgent,
    loadScenarios,
    selectScenario,
    executeCustomPayload,
    downloadComplianceReport,
    clearLogs,
    openCmdPalette,
    closeCmdPalette
  };

  // DOM Content Loaded Initializer
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initKeyboard();
    initRealtimeStream();
    fetchAuditLogs();
    fetchHitlQueue();

    // Event listeners for tabs
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tabId = e.currentTarget.getAttribute('data-tab');
        switchTab(tabId);
      });
    });

    // Rule builder preview trigger
    ['rule-target-tool', 'rule-condition-type', 'rule-enforcement-action'].forEach(id => {
      document.getElementById(id)?.addEventListener('change', updateRuleBuilderPreview);
    });
    updateRuleBuilderPreview();
  });

})();
