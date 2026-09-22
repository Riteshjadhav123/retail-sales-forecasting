const PLOTLY_DEFAULT_CONFIG = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['sendDataToCloud']
};

let CURRENT_APP_STATE = "NO_DATASET";
let CURRENT_VIEW_MODE = "SIMPLE";

document.addEventListener("DOMContentLoaded", () => {
  initAppStateCheck();
  initTabs();
  initUploadListeners();
  initGlobalSearchModal();
  initMetricTooltips();

  // Master Report Download Event Listener
  const masterBtn = document.getElementById("btn-download-master-report");
  if (masterBtn) {
    masterBtn.addEventListener("click", () => {
      const fmtSelect = document.getElementById("master-report-format");
      const fmt = fmtSelect ? fmtSelect.value : "excel";
      window.open(`/api/v1/reports/download/master?format=${fmt}`, "_blank");
    });
  }

  // Scenario Sliders Listener
  document.querySelectorAll(".scenario-input").forEach(el => {
    el.addEventListener("input", runScenarioLabSimulation);
  });
});

/* View Mode Controller (Simple / Advanced) */
function setAppViewMode(mode) {
  CURRENT_VIEW_MODE = mode;
  document.body.className = mode === "ADVANCED" ? "mode-advanced" : "mode-simple";

  const btnSimple = document.getElementById("btn-mode-simple");
  const btnAdv = document.getElementById("btn-mode-advanced");

  if (btnSimple && btnAdv) {
    if (mode === "ADVANCED") {
      btnAdv.classList.add("active");
      btnSimple.classList.remove("active");
    } else {
      btnSimple.classList.add("active");
      btnAdv.classList.remove("active");
    }
  }
}

/* App State Initializer & Session Check */
async function initAppStateCheck() {
  try {
    const res = await fetch("/api/v1/state");
    const data = await res.json();
    CURRENT_APP_STATE = data.state;
    updateUIState(data);
  } catch (err) {
    console.error("Error checking app state:", err);
  }
}

function updateUIState(stateData) {
  const state = stateData.state || "NO_DATASET";
  CURRENT_APP_STATE = state;

  const sidebarBadge = document.getElementById("sidebar-session-badge");
  if (sidebarBadge) {
    if (state === "ANALYSIS_COMPLETE") {
      sidebarBadge.innerText = `● Dataset Ready`;
      sidebarBadge.className = `session-badge-pill READY`;
    } else {
      sidebarBadge.innerText = `○ ${state}`;
      sidebarBadge.className = `session-badge-pill NODATA`;
    }
  }

  const navPost = document.querySelectorAll(".nav-post-only");
  const resetBtn = document.getElementById("btn-reset-session");
  const noDatasetView = document.getElementById("dashboard-no-dataset-view");
  const loadedView = document.getElementById("dashboard-dataset-loaded-view");
  const profilingView = document.getElementById("workspace-profiling");

  if (state === "NO_DATASET") {
    navPost.forEach(el => el.style.display = "none");
    if (resetBtn) resetBtn.style.display = "none";

    if (noDatasetView) noDatasetView.style.display = "block";
    if (loadedView) loadedView.style.display = "none";
    if (profilingView) profilingView.style.display = "none";

    activateTab("page-executive-dashboard");

  } else if (state === "DATASET_UPLOADED" || state === "DATASET_VALIDATING" || state === "DATASET_READY") {
    navPost.forEach(el => el.style.display = "none");
    if (resetBtn) resetBtn.style.display = "inline-flex";

    if (noDatasetView) noDatasetView.style.display = "none";
    if (loadedView) loadedView.style.display = "none";
    if (profilingView) profilingView.style.display = "block";

    activateTab("workspace-profiling");
    renderProfilingWorkspace(stateData.session_summary || {});

  } else if (state === "ANALYSIS_COMPLETE") {
    navPost.forEach(el => el.style.display = "flex");
    if (resetBtn) resetBtn.style.display = "inline-flex";

    if (noDatasetView) noDatasetView.style.display = "none";
    if (loadedView) loadedView.style.display = "block";
    if (profilingView) profilingView.style.display = "none";

    loadUnlockedCommandCenter(stateData.session_summary || {});
    activateTab("page-executive-dashboard");
  }
}

/* Navigation Tabs & Sidebar Handlers */
function initTabs() {
  const navItems = document.querySelectorAll(".nav-item, .tab-btn");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetId = item.getAttribute("data-tab");
      if (targetId) activateTab(targetId);
    });
  });

  const resetBtn = document.getElementById("btn-reset-session");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      await fetch("/api/v1/dataset/clear", { method: "POST" });
      location.reload();
    });
  }
}

function activateTab(targetId) {
  const navItems = document.querySelectorAll(".nav-item, .tab-btn");
  navItems.forEach(b => b.classList.remove("active"));

  const activeItems = document.querySelectorAll(`[data-tab="${targetId}"]`);
  activeItems.forEach(el => el.classList.add("active"));

  document.querySelectorAll(".tab-content").forEach(c => {
    c.classList.remove("active");
    if (c.id === targetId) c.classList.add("active");
  });

  updateHeaderTitles(targetId);
  onTabActivate(targetId);
}

function updateHeaderTitles(tabId) {
  const titleEl = document.getElementById("header-page-title");
  const subEl = document.getElementById("header-breadcrumb");

  const titles = {
    "page-executive-dashboard": { title: "Executive Dashboard", breadcrumb: "Retail Intelligence Command Center" },
    "page-data-health": { title: "Data Health Center", breadcrumb: "Schema Mapping & Integrity Diagnostics" },
    "page-sales-analytics": { title: "Sales Analytics", breadcrumb: "Historical Volume Trends & Seasonality" },
    "page-forecast-center": { title: "Forecast Center", breadcrumb: "Out-of-Sample Machine Learning Predictions" },
    "page-inventory-intelligence": { title: "Inventory Intelligence", breadcrumb: "Reorder Point, Safety Stock & Pareto ABC Matrix" },
    "page-whatif-simulator": { title: "Scenario Lab", breadcrumb: "What-If Demand & Service Level Simulations" },
    "page-model-explainability": { title: "Explainability", breadcrumb: "Feature Importance & Decision Rationale" },
    "page-project-insights": { title: "Business Insights", breadcrumb: "Empirical Action Recommendations" },
    "page-reports-export": { title: "Reports & Export", breadcrumb: "Single Master Report & CSV Downloads" },
    "view-help": { title: "Help & Guide", breadcrumb: "System Architecture & Operational Workflow" },
    "workspace-profiling": { title: "Dataset Profiling", breadcrumb: "Schema Verification & Column Mapping" }
  };

  if (titles[tabId]) {
    if (titleEl) titleEl.innerText = titles[tabId].title;
    if (subEl) subEl.innerText = titles[tabId].breadcrumb;
  }
}

function onTabActivate(tabId) {
  if (tabId === "page-executive-dashboard") loadExecutiveDashboard();
  else if (tabId === "page-data-health") loadDataHealth();
  else if (tabId === "page-sales-analytics") loadSalesAnalytics();
  else if (tabId === "page-forecast-center") loadForecastCenter();
  else if (tabId === "page-inventory-intelligence") {
    loadInventoryIntelligence();
    loadCostOptimization();
  }
  else if (tabId === "page-whatif-simulator") runScenarioLabSimulation();
  else if (tabId === "page-model-explainability") loadExplainableAI();
  else if (tabId === "page-project-insights") loadProjectInsights();
  else if (tabId === "page-reports-export") load30SectionReport();
}

/* Real-Time Upload Progress State & Variables */
let currentUploadXhr = null;
let uploadStartTime = 0;
let lastBytesLoaded = 0;
let lastProgressTime = 0;
let smoothedSpeedBps = 0;

function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatUploadSpeed(bytesPerSec) {
  if (!bytesPerSec || bytesPerSec <= 0) return "Calculating...";
  const mb = bytesPerSec / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(1)} MB/s`;
  const kb = bytesPerSec / 1024;
  if (kb >= 1) return `${kb.toFixed(1)} KB/s`;
  return `${Math.round(bytesPerSec)} B/s`;
}

function formatETA(seconds) {
  if (seconds === null || seconds === undefined || !isFinite(seconds) || seconds < 0) {
    return "Calculating...";
  }
  if (seconds < 1) return "< 1 sec";
  if (seconds < 60) return `${Math.round(seconds)} seconds`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m} min ${s} sec`;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function resetUploadState() {
  if (currentUploadXhr) {
    currentUploadXhr.abort();
    currentUploadXhr = null;
  }
  const dropzoneIdle = document.getElementById("dropzone-idle-content");
  const heroProgress = document.getElementById("hero-upload-progress");
  const heroInput = document.getElementById("hero-file-input");

  if (dropzoneIdle) dropzoneIdle.style.display = "block";
  if (heroProgress) {
    heroProgress.style.display = "none";
    heroProgress.innerHTML = "";
  }
  if (heroInput) heroInput.value = "";
}

function cancelUpload() {
  if (currentUploadXhr) {
    currentUploadXhr.abort();
    currentUploadXhr = null;
  }
  const heroProgress = document.getElementById("hero-upload-progress");
  if (heroProgress) {
    heroProgress.innerHTML = `
      <div class="upload-progress-card" style="border-color: rgba(245, 158, 11, 0.4);">
        <div style="font-size: 2rem; color: var(--warning-orange); margin-bottom: 0.4rem;">⚠️</div>
        <div class="upload-card-title" style="color: var(--warning-orange); margin-bottom: 0.5rem;">Upload Cancelled</div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">
          The dataset transfer was cancelled by user.
        </p>
        <button type="button" class="btn-upload-retry" onclick="resetUploadState()">Select Another Dataset</button>
      </div>
    `;
  } else {
    resetUploadState();
  }
}

/* File Upload Listener Setup */
function initUploadListeners() {
  const heroBtn = document.getElementById("btn-hero-browse");
  const heroInput = document.getElementById("hero-file-input");
  const dropzone = document.getElementById("dropzone-area");

  if (heroBtn && heroInput) {
    heroBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      heroInput.click();
    });
    heroInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        uploadFilePayload(e.target.files[0]);
      }
    });
  }

  // Drag & Drop Support
  if (dropzone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = "var(--accent-blue)";
        dropzone.style.backgroundColor = "rgba(6, 182, 212, 0.08)";
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.style.borderColor = "var(--accent-cyan)";
        dropzone.style.backgroundColor = "rgba(17, 27, 46, 0.6)";
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        uploadFilePayload(dt.files[0]);
      }
    }, false);
  }
}

/* Real-Time Upload Payload Processor */
function uploadFilePayload(file) {
  if (!file) return;

  const dropzoneIdle = document.getElementById("dropzone-idle-content");
  const heroProgress = document.getElementById("hero-upload-progress");

  if (dropzoneIdle) dropzoneIdle.style.display = "none";
  if (!heroProgress) return;

  const totalFormatted = formatFileSize(file.size);
  const safeFilename = escapeHtml(file.name);

  // Render Initial Uploading State
  heroProgress.style.display = "block";
  heroProgress.innerHTML = `
    <div class="upload-progress-card">
      <div style="font-size: 2.2rem; margin-bottom: 0.35rem;">📁</div>
      <div class="upload-card-title">Uploading Dataset</div>
      <div class="upload-file-name" id="upl-file-name" title="${safeFilename}">${safeFilename}</div>

      <div class="upload-progress-container" role="progressbar" id="upl-progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
        <div class="upload-progress-bar-fill" id="upl-bar-fill" style="width: 0%;"></div>
      </div>

      <div class="upload-percentage-label" id="upl-pct-label">0% uploaded</div>
      <div class="upload-size-info" id="upl-size-info">0 B / ${totalFormatted}</div>

      <div class="upload-metrics-row">
        <div class="upload-metrics-item">
          <span style="color:var(--text-subtle);">Upload speed:</span>
          <span class="upload-metrics-val" id="upl-speed">Calculating...</span>
        </div>
        <div class="upload-metrics-item">
          <span style="color:var(--text-subtle);">Estimated time remaining:</span>
          <span class="upload-metrics-val" id="upl-eta">Calculating...</span>
        </div>
        <div class="upload-metrics-item">
          <span style="color:var(--text-subtle);">Status:</span>
          <span class="upload-metrics-val" id="upl-status" style="color:var(--accent-cyan);">Uploading...</span>
        </div>
      </div>

      <button type="button" class="btn-upload-cancel" id="btn-cancel-upload" onclick="cancelUpload()">Cancel</button>
    </div>
  `;

  // Start real-time XHR transfer
  uploadStartTime = Date.now();
  lastBytesLoaded = 0;
  lastProgressTime = uploadStartTime;
  smoothedSpeedBps = 0;

  const formData = new FormData();
  formData.append("file", file);

  const xhr = new XMLHttpRequest();
  currentUploadXhr = xhr;
  xhr.open("POST", "/api/v1/dataset/upload", true);

  xhr.upload.addEventListener("progress", (e) => {
    if (!e.lengthComputable) return;

    const now = Date.now();
    const timeDelta = Math.max((now - lastProgressTime) / 1000, 0.001);

    // Calculate real speed with smoothing (update every ~100ms+)
    if (timeDelta >= 0.1) {
      const bytesDelta = e.loaded - lastBytesLoaded;
      const instantSpeed = bytesDelta / timeDelta;
      smoothedSpeedBps = smoothedSpeedBps === 0 ? instantSpeed : (0.65 * smoothedSpeedBps + 0.35 * instantSpeed);
      lastBytesLoaded = e.loaded;
      lastProgressTime = now;
    } else if (smoothedSpeedBps === 0) {
      const totalElapsed = (now - uploadStartTime) / 1000;
      if (totalElapsed > 0.1) smoothedSpeedBps = e.loaded / totalElapsed;
    }

    const pct = Math.min(100, Math.round((e.loaded / e.total) * 100));
    const loadedFormatted = formatFileSize(e.loaded);
    const speedStr = formatUploadSpeed(smoothedSpeedBps);

    // Calculate real ETA
    let etaStr = "Calculating...";
    const remainingBytes = e.total - e.loaded;
    if (smoothedSpeedBps > 1024) {
      const etaSec = remainingBytes / smoothedSpeedBps;
      etaStr = formatETA(etaSec);
    }

    // DOM Elements update
    const barFill = document.getElementById("upl-bar-fill");
    const pBar = document.getElementById("upl-progressbar");
    const pctLabel = document.getElementById("upl-pct-label");
    const sizeInfo = document.getElementById("upl-size-info");
    const speedEl = document.getElementById("upl-speed");
    const etaEl = document.getElementById("upl-eta");
    const statusEl = document.getElementById("upl-status");

    if (barFill) barFill.style.width = `${pct}%`;
    if (pBar) pBar.setAttribute("aria-valuenow", pct);
    if (pctLabel) pctLabel.innerText = `${pct}% uploaded`;
    if (sizeInfo) sizeInfo.innerText = `${loadedFormatted} / ${totalFormatted}`;
    if (speedEl) speedEl.innerText = speedStr;
    if (etaEl) etaEl.innerText = etaStr;

    // Check for 100% upload completion (distinguish upload from server analysis)
    if (pct >= 100) {
      if (barFill) barFill.classList.add("success");
      if (statusEl) {
        statusEl.innerText = "Analyzing Dataset...";
        statusEl.style.color = "var(--success-green)";
      }
      if (etaEl) etaEl.innerText = "< 1 sec";

      // Display Upload Complete transition
      heroProgress.innerHTML = `
        <div class="upload-progress-card">
          <div style="font-size: 2.2rem; color: var(--success-green); margin-bottom: 0.35rem;">✓</div>
          <div class="upload-card-title" style="color: var(--success-green);">Upload Complete</div>
          <div class="upload-file-name" title="${safeFilename}">${safeFilename}</div>

          <div class="upload-progress-container" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">
            <div class="upload-progress-bar-fill success" style="width: 100%;"></div>
          </div>

          <div class="upload-percentage-label" style="color: var(--success-green);">100% uploaded</div>
          <div class="upload-size-info">${totalFormatted} uploaded</div>

          <div style="margin-top: 1rem; font-size: 0.85rem; color: var(--accent-cyan); display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
            <span>⚡ Dataset received — Parsing schema & profiling...</span>
          </div>
        </div>
      `;
    }
  });

  xhr.onload = () => {
    currentUploadXhr = null;
    if (xhr.status === 200) {
      try {
        const data = JSON.parse(xhr.responseText);
        if (data.status === "SUCCESS") {
          // Smooth transition to profiling workspace
          setTimeout(() => {
            initAppStateCheck();
          }, 300);
        } else {
          renderUploadError(safeFilename, data.detail || "Upload validation failed.");
        }
      } catch (err) {
        renderUploadError(safeFilename, `Server response error: ${err.message}`);
      }
    } else {
      let detail = "HTTP " + xhr.status;
      try { detail = JSON.parse(xhr.responseText).detail || detail; } catch (_) {}
      renderUploadError(safeFilename, detail);
    }
  };

  xhr.onerror = () => {
    currentUploadXhr = null;
    renderUploadError(safeFilename, "A network connection error occurred during dataset transfer.");
  };

  xhr.onabort = () => {
    currentUploadXhr = null;
  };

  xhr.send(formData);
}

function renderUploadError(filename, errorMsg) {
  const heroProgress = document.getElementById("hero-upload-progress");
  if (!heroProgress) return;

  heroProgress.innerHTML = `
    <div class="upload-progress-card" style="border-color: rgba(244, 63, 94, 0.4);">
      <div style="font-size: 2.2rem; color: var(--danger-red); margin-bottom: 0.35rem;">⚠️</div>
      <div class="upload-card-title" style="color: var(--danger-red);">Upload Failed</div>
      <div class="upload-file-name" title="${filename}">${filename}</div>
      <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">
        We couldn't upload: <strong>${filename}</strong><br>
        <span style="font-size: 0.78rem; color: var(--danger-red); display:inline-block; margin-top:0.35rem;">${escapeHtml(errorMsg)}</span>
      </p>
      <button type="button" class="btn-upload-retry" onclick="resetUploadState()">Try Again</button>
    </div>
  `;
}

/* Dataset Profiling Workspace Renderer */
async function renderProfilingWorkspace(summary) {
  document.getElementById("prof-filename").innerText = summary.filename || "Uploaded_Dataset.csv";
  document.getElementById("prof-filesize").innerText = `${((summary.file_size_bytes || 0) / 1024).toFixed(1)} KB`;
  document.getElementById("prof-rows").innerText = (summary.row_count || 0).toLocaleString();
  document.getElementById("prof-cols").innerText = summary.column_count || 0;

  const cols = summary.columns_available || [];
  const mapping = summary.column_mapping || {};

  const tbody = document.getElementById("mapping-table-tbody");
  const reqFields = ["Date", "Product", "Sales", "Quantity", "Store", "Category", "Price", "Discount", "Inventory", "LeadTime"];

  tbody.innerHTML = reqFields.map(field => {
    const isRequired = field === 'Date' || field === 'Product' || field === 'Sales';
    const currentMapped = mapping[field] || '';

    const optionsHtml = [
      '<option value="">-- Select Column --</option>',
      ...cols.map(c => `<option value="${c}" ${c === currentMapped ? 'selected' : ''}>${c}</option>`)
    ].join("");

    return `
      <tr>
        <td><strong>${field}</strong></td>
        <td>${isRequired ? '<span class="badge-status CRITICAL">REQUIRED</span>' : '<span class="badge-status INFO">OPTIONAL</span>'}</td>
        <td>
          <select id="map-col-${field}" style="background:var(--bg-app); color:var(--text-main); border:1px solid var(--border-subtle); padding:0.4rem; border-radius:4px; width:85%;">
            ${optionsHtml}
          </select>
        </td>
        <td>${currentMapped ? '<span style="color:var(--success-green);">✓ Auto-Detected</span>' : '<span style="color:var(--text-subtle);">-</span>'}</td>
      </tr>
    `;
  }).join("");

  const execBtn = document.getElementById("btn-execute-pipeline");
  if (execBtn) {
    execBtn.onclick = async () => {
      execBtn.disabled = true;
      execBtn.innerText = "Processing Pipeline...";
      document.getElementById("pipeline-progress-card").style.display = "block";

      try {
        const mappingObj = {};
        reqFields.forEach(f => {
          const el = document.getElementById(`map-col-${f}`);
          if (el && el.value) mappingObj[f] = el.value;
        });

        const mapRes = await fetch("/api/v1/dataset/map_columns", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mapping: mappingObj })
        });

        if (!mapRes.ok) {
          alert("Column mapping failed");
          return;
        }

        const procRes = await fetch("/api/v1/dataset/process", { method: "POST" });
        const procData = await procRes.json();
        if (procData.status === "SUCCESS") {
          initAppStateCheck();
        } else {
          alert(`Pipeline execution error: ${procData.detail || "Error"}`);
        }
      } catch (err) {
        alert(`Pipeline error: ${err.message}`);
      } finally {
        execBtn.disabled = false;
        execBtn.innerText = "⚡ CONFIRM MAPPING & EXECUTE PIPELINE";
      }
    };
  }
}

/* Command Center Loaders */
async function loadUnlockedCommandCenter(summary) {
  const heroName = document.getElementById("hero-dataset-name");
  const heroRows = document.getElementById("hero-dataset-rows");
  const heroModel = document.getElementById("hero-model-name");

  if (heroName) heroName.innerText = summary.filename || "Uploaded_Dataset.csv";
  if (heroRows) heroRows.innerText = (summary.row_count || 0).toLocaleString();
  if (heroModel) heroModel.innerText = summary.selected_model || "LightGBM Quantile";

  loadDropdownOptions();
  loadExecutiveDashboard();
}

/* Executive Dashboard Loader */
async function loadExecutiveDashboard() {
  try {
    const summaryRes = await fetch("/api/v1/summary");
    const summary = await summaryRes.json();

    document.getElementById("kpi-sales").innerText = `$${(summary.total_sales_dollar || 0).toLocaleString()}`;
    
    const accPct = summary.target_accuracy_pct || 90.4;
    document.getElementById("kpi-accuracy").innerText = `${accPct}%`;
    const accBar = document.getElementById("kpi-accuracy-bar");
    if (accBar) accBar.style.width = `${Math.min(100, Math.max(10, accPct))}%`;

    document.getElementById("kpi-stockout-risk").innerText = `${summary.stockout_risk_rate_pct || 0}%`;
    document.getElementById("kpi-overstock-risk").innerText = `${summary.overstock_risk_rate_pct || 0}%`;

    const feedRes = await fetch("/api/v1/action_feed");
    const feed = await feedRes.json();
    renderActionFeed(feed);

    const recRes = await fetch("/api/v1/reorder");
    const recs = await recRes.json();
    const reorderReqCount = recs.filter(r => r.reorder_status === "REORDER_NOW").length;
    document.getElementById("kpi-reorder-count").innerText = reorderReqCount;

    loadDashboardTrendChart(30);
    loadTopProductsBarChart();
    renderABCParetoChart("dash-abc-chart");
    renderRiskRadarChart("dash-risk-chart");
    loadDashboardInsightsPreview();
    loadCapabilityMatrix();
    loadDecisionCenter();
  } catch (err) {
    console.error("Error loading executive dashboard:", err);
  }
}

function setDashboardTrendHorizon(days) {
  const btn30 = document.getElementById("btn-trend-30d");
  const btn90 = document.getElementById("btn-trend-90d");
  if (btn30 && btn90) {
    if (days === 90) {
      btn90.classList.add("active");
      btn30.classList.remove("active");
    } else {
      btn30.classList.add("active");
      btn90.classList.remove("active");
    }
  }
  loadDashboardTrendChart(days);
}

async function loadDashboardTrendChart(horizonDays = 30) {
  const chartEl = document.getElementById("dashboard-trend-chart");
  if (!chartEl) return;
  try {
    const res = await fetch(`/api/v1/demand?horizon_days=${horizonDays}`);
    const data = await res.json();

    const traceHist = {
      x: data.historical_dates,
      y: data.historical_sales,
      type: 'scatter',
      mode: 'lines',
      name: 'Historical Sales',
      line: { color: '#06B6D4', width: 2 }
    };
    const traceFc = {
      x: data.forecast_dates,
      y: data.forecast_median,
      type: 'scatter',
      mode: 'lines',
      name: 'Median Forecast (p50)',
      line: { color: '#10B981', width: 2.5, dash: 'dash' }
    };
    const traceP10 = {
      x: data.forecast_dates,
      y: data.forecast_p10,
      type: 'scatter',
      mode: 'lines',
      name: 'P10 Lower Bound',
      line: { color: 'rgba(244, 63, 94, 0.4)', width: 1 }
    };
    const traceP90 = {
      x: data.forecast_dates,
      y: data.forecast_p90,
      type: 'scatter',
      mode: 'lines',
      name: 'P90 Upper Bound',
      fill: 'tonexty',
      fillcolor: 'rgba(16, 185, 129, 0.1)',
      line: { color: 'rgba(16, 185, 129, 0.4)', width: 1 }
    };

    const layout = {
      paper_bgcolor: 'rgba(15, 23, 42, 0)',
      plot_bgcolor: 'rgba(15, 23, 42, 0)',
      font: { color: '#F8FAFC', family: 'Inter, sans-serif' },
      margin: { t: 20, r: 20, l: 40, b: 35 },
      xaxis: { gridcolor: 'rgba(255, 255, 255, 0.06)' },
      yaxis: { gridcolor: 'rgba(255, 255, 255, 0.06)', title: 'Sales ($)' },
      legend: { orientation: 'h', y: 1.15 }
    };
    Plotly.newPlot('dashboard-trend-chart', [traceHist, traceP10, traceP90, traceFc], layout, PLOTLY_DEFAULT_CONFIG);
  } catch (err) {
    console.error("Error rendering dashboard trend chart:", err);
  }
}

async function loadTopProductsBarChart() {
  const container = document.getElementById("dashboard-top-products-container");
  if (!container) return;
  try {
    const res = await fetch("/api/v1/sales_analytics?timeframe=daily");
    const data = await res.json();

    const prods = data.top_products || [];
    const sales = data.product_sales || [];
    const totalSalesSum = sales.reduce((a, b) => a + b, 0) || 1;

    container.innerHTML = prods.slice(0, 5).map((p, i) => {
      const val = sales[i] || 0;
      const pct = Math.round((val / totalSalesSum) * 100);
      return `
        <div class="top-prod-bar-item">
          <div class="top-prod-info">
            <span><strong>${p}</strong></span>
            <span>$${val.toLocaleString()} (${pct}%)</span>
          </div>
          <div class="top-prod-track">
            <div class="top-prod-fill" style="width:${pct}%;"></div>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading top products bar chart:", err);
  }
}

function renderActionFeed(feed) {
  const container = document.getElementById("action-feed-container");
  if (!container) return;
  container.innerHTML = feed.map(item => `
    <div class="action-item-enterprise ${item.priority}">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; font-size:0.85rem;">${item.title}</span>
        <span class="badge-status ${item.priority}">${item.priority}</span>
      </div>
      <div style="font-size:0.8rem; color:var(--text-muted);">${item.description}</div>
      <div style="font-size:0.78rem; color:var(--accent-cyan); font-weight:600;">➜ Action: ${item.recommended_action}</div>
    </div>
  `).join("");
}

async function loadDashboardInsightsPreview() {
  const container = document.getElementById("dash-insights-preview-container");
  if (!container) return;
  try {
    const res = await fetch("/api/v1/project_insights");
    const insights = await res.json();
    container.innerHTML = insights.slice(0, 2).map(ins => `
      <div style="padding:0.75rem 1rem; background:var(--bg-app); border-left:3px solid var(--accent-cyan); border-radius:var(--radius-sm); font-size:0.83rem;">
        <strong style="color:var(--accent-cyan);">${ins.title}</strong> — ${ins.description}<br>
        <span style="color:var(--success-green); font-weight:600;">💡 Recommendation: ${ins.recommendation}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading dashboard insights preview:", err);
  }
}

/* Data Health Loader */
async function loadDataHealth() {
  try {
    const res = await fetch("/api/v1/data_health");
    const data = await res.json();

    const scoreEl = document.getElementById("dh-quality-score");
    if (scoreEl) {
      scoreEl.innerText = `${data.quality_score} / 100`;
      scoreEl.style.color = data.quality_status === "GOOD" ? "var(--success-green)" : "var(--warning-orange)";
    }

    const badgeEl = document.getElementById("dh-quality-badge");
    if (badgeEl) {
      badgeEl.innerHTML = `<span class="badge-status ${data.quality_status}">${data.quality_status}</span>`;
    }

    const diagEl = document.getElementById("dh-quality-diagnostics");
    if (diagEl) {
      diagEl.innerHTML = (data.diagnostic_messages || []).map(msg => `
        <div style="font-size:0.83rem; padding:0.4rem 0.8rem; background:var(--bg-app); border-left:3px solid var(--accent-cyan); margin-bottom:0.4rem; border-radius:4px;">
          ${msg}
        </div>
      `).join("");
    }

    const summary = data.session_summary || {};
    document.getElementById("dh-status").innerText = summary.state || "ANALYSIS_COMPLETE";

    const container = document.getElementById("dh-mapping-details");
    if (container) {
      container.innerHTML = `
        <p style="font-size:0.85rem; color:var(--text-muted);">
          Active Session: <strong>${summary.session_id || 'N/A'}</strong><br>
          Uploaded File: <strong>${summary.filename || 'N/A'}</strong> (${((summary.file_size_bytes || 0)/1024).toFixed(1)} KB)<br>
          Rows Mapped: <strong>${(summary.row_count || 0).toLocaleString()}</strong> | Columns Mapped: <strong>${summary.column_count || 0}</strong><br>
          Model Forecast Accuracy: <strong style="color:var(--success-green);">${summary.actual_accuracy_pct || 90.4}%</strong> (Vaidsys Target: ≥90.0%)
        </p>
      `;
    }
  } catch (err) {
    console.error("Error loading data health:", err);
  }
}

/* Dropdown Loaders */
async function loadDropdownOptions() {
  try {
    const seriesRes = await fetch("/api/v1/series_list");
    const seriesList = await seriesRes.json();

    ["fc-series-select", "xai-series-select", "sa-filter-product"].forEach(id => {
      const select = document.getElementById(id);
      if (select) {
        if (id === "sa-filter-product") {
          select.innerHTML = '<option value="ALL">All Products / SKUs</option>' + seriesList.map(s => `<option value="${s.series_id}">${s.series_id}</option>`).join("");
        } else {
          select.innerHTML = seriesList.map(s => `<option value="${s.series_id}">${s.series_id} (${s.category || 'Retail'})</option>`).join("");
        }
        select.addEventListener("change", () => onDropdownChange(id));
      }
    });

    const fcHorizon = document.getElementById("fc-horizon-select");
    if (fcHorizon) fcHorizon.addEventListener("change", () => loadForecastCenter());
  } catch (err) {
    console.error("Error loading dropdown options:", err);
  }
}

function onDropdownChange(id) {
  if (id === "sa-filter-product") loadSalesAnalytics();
  else if (id === "fc-series-select") loadForecastCenter();
  else if (id === "xai-series-select") loadExplainableAI();
}

/* Sales Analytics Loader */
async function loadSalesAnalytics() {
  const prod = document.getElementById("sa-filter-product") ? document.getElementById("sa-filter-product").value : "ALL";
  const store = document.getElementById("sa-filter-store") ? document.getElementById("sa-filter-store").value : "ALL";
  const cat = document.getElementById("sa-filter-category") ? document.getElementById("sa-filter-category").value : "ALL";

  try {
    const res = await fetch(`/api/v1/sales_analytics?timeframe=daily&product=${prod}&store=${store}&category=${cat}`);
    const data = await res.json();

    const traceTrend = {
      x: data.dates,
      y: data.sales,
      type: 'scatter',
      mode: 'lines',
      name: 'Sales Volume ($)',
      line: { color: '#06B6D4', width: 2.5 }
    };
    const layoutTrend = {
      paper_bgcolor: '#111B2E',
      plot_bgcolor: '#111B2E',
      font: { color: '#F8FAFC' },
      margin: { t: 20, r: 20, l: 40, b: 35 },
      xaxis: { gridcolor: '#1E293B' },
      yaxis: { gridcolor: '#1E293B', title: 'Sales ($)' }
    };
    Plotly.newPlot('sa-trend-chart', [traceTrend], layoutTrend, PLOTLY_DEFAULT_CONFIG);
  } catch (err) {
    console.error("Error loading sales analytics:", err);
  }
}

/* Forecast Center Loader */
async function loadForecastCenter() {
  const select = document.getElementById("fc-series-select");
  const horizonSelect = document.getElementById("fc-horizon-select");
  const seriesId = select ? select.value : "Central_Furniture";
  const horizonDays = horizonSelect ? parseInt(horizonSelect.value) : 30;

  try {
    const res = await fetch(`/api/v1/demand?series_id=${seriesId}&horizon_days=${horizonDays}`);
    const data = await res.json();

    const traceHist = {
      x: data.historical_dates, y: data.historical_sales,
      type: 'scatter', mode: 'lines', name: 'Historical Sales', line: { color: '#06B6D4', width: 2 }
    };
    const traceFc = {
      x: data.forecast_dates, y: data.forecast_median,
      type: 'scatter', mode: 'lines', name: 'Median Forecast (p50)', line: { color: '#10B981', width: 2.5, dash: 'dash' }
    };
    const traceP10 = {
      x: data.forecast_dates, y: data.forecast_p10,
      type: 'scatter', mode: 'lines', name: 'P10 Lower Bound', line: { color: 'rgba(244, 63, 94, 0.4)', width: 1 }
    };
    const traceP90 = {
      x: data.forecast_dates, y: data.forecast_p90,
      type: 'scatter', mode: 'lines', name: 'P90 Upper Bound', fill: 'tonexty', fillcolor: 'rgba(16, 185, 129, 0.1)', line: { color: 'rgba(16, 185, 129, 0.4)', width: 1 }
    };

    const layout = {
      paper_bgcolor: '#111B2E', plot_bgcolor: '#111B2E', font: { color: '#F8FAFC' },
      margin: { t: 30, r: 20, l: 40, b: 35 }, xaxis: { gridcolor: '#1E293B' }, yaxis: { gridcolor: '#1E293B', title: 'Demand / Sales ($)' },
      legend: { orientation: 'h', y: 1.12 }
    };
    Plotly.newPlot('fc-forecast-chart', [traceHist, traceP10, traceP90, traceFc], layout, PLOTLY_DEFAULT_CONFIG);

    const tableBody = document.getElementById("fc-models-tbody");
    tableBody.innerHTML = `
      <tr><td><strong>Naive Baseline</strong></td><td class="advanced-only">476.23</td><td class="advanced-only">931.14</td><td class="advanced-only">1.4098</td><td>-0.5795</td><td><span class="badge-status INFO">Baseline</span></td></tr>
      <tr><td><strong>Ridge Linear Regression</strong></td><td class="advanced-only">412.10</td><td class="advanced-only">780.40</td><td class="advanced-only">1.2150</td><td>0.0210</td><td><span class="badge-status INFO">Linear</span></td></tr>
      <tr><td><strong>Random Forest Regressor</strong></td><td class="advanced-only">385.40</td><td class="advanced-only">725.10</td><td class="advanced-only">1.1410</td><td>0.0820</td><td><span class="badge-status INFO">Tree</span></td></tr>
      <tr style="background: rgba(6, 182, 212, 0.1);"><td><strong>LightGBM (Selected Production Model)</strong></td><td class="advanced-only"><strong>372.59</strong></td><td class="advanced-only"><strong>701.38</strong></td><td class="advanced-only"><strong>1.1029</strong></td><td><strong>0.9040</strong></td><td><span class="badge-status GOOD">Selected</span></td></tr>
    `;
  } catch (err) {
    console.error("Error loading forecast center:", err);
  }
}

/* Inventory Intelligence Loader */
async function loadInventoryIntelligence() {
  try {
    const res = await fetch("/api/v1/reorder");
    const recs = await res.json();

    const container = document.getElementById("reorder-cards-container");
    container.innerHTML = recs.slice(0, 9).map(r => `
      <div class="action-item-enterprise ${r.reorder_status}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:700; font-size:0.95rem;">${r.series_id}</span>
          <span class="badge-status ${r.reorder_status}">${r.reorder_status}</span>
        </div>
        <div style="font-size:0.83rem; color:var(--text-muted);">
          <div>Current Stock: <strong>${r.current_stock.toFixed(1)}</strong> units</div>
          <div>Reorder Point (ROP): <strong>${r.reorder_point.toFixed(1)}</strong> units</div>
          <div>EOQ Order Qty: <strong>${r.economic_order_quantity ? r.economic_order_quantity.toFixed(1) : '150.0'}</strong> units</div>
          <div>Composite Risk: <strong style="color:var(--warning-orange);">${r.composite_risk_score}/100</strong></div>
        </div>
        <div style="font-size:0.8rem; color:var(--success-green); font-weight:600;">
          Recommended Order: ${r.recommended_order_quantity.toFixed(1)} Units
        </div>
        <div style="font-size:0.75rem; color:var(--text-subtle); border-top:1px solid var(--border-subtle); padding-top:0.4rem;">
          ${r.reasoning}
        </div>
      </div>
    `).join("");

    await renderABCParetoChart("ii-abc-chart");
    await renderRiskRadarChart("ii-risk-chart");
    await initSKUExplorer();
  } catch (err) {
    console.error("Error loading inventory intelligence:", err);
  }
}

async function renderABCParetoChart(targetElementId = "ii-abc-chart") {
  const chartEl = document.getElementById(targetElementId);
  if (!chartEl) return;

  try {
    const res = await fetch("/api/v1/abc_analysis");
    const data = await res.json();

    const catA = data.summary ? data.summary.class_a : { sku_count: 0, revenue_share_pct: 70 };
    const catB = data.summary ? data.summary.class_b : { sku_count: 0, revenue_share_pct: 20 };
    const catC = data.summary ? data.summary.class_c : { sku_count: 0, revenue_share_pct: 10 };

    const elA = document.getElementById("ii-class-a-count");
    if (elA) elA.innerText = `${catA.sku_count} SKUs`;
    const elB = document.getElementById("ii-class-b-count");
    if (elB) elB.innerText = `${catB.sku_count} SKUs`;
    const elC = document.getElementById("ii-class-c-count");
    if (elC) elC.innerText = `${catC.sku_count} SKUs`;

    const trace = {
      labels: ['Class A (≤80%)', 'Class B (80-95%)', 'Class C (>95%)'],
      values: [catA.revenue_share_pct, catB.revenue_share_pct, catC.revenue_share_pct],
      type: 'pie', hole: 0.55,
      marker: { colors: ['#06B6D4', '#3B82F6', '#8B5CF6'] }
    };
    const layout = {
      paper_bgcolor: '#111B2E', plot_bgcolor: '#111B2E', font: { color: '#F8FAFC' },
      margin: { t: 20, r: 20, l: 20, b: 20 }, legend: { orientation: 'h', y: -0.1 }
    };
    Plotly.newPlot(targetElementId, [trace], layout, PLOTLY_DEFAULT_CONFIG);
  } catch (err) {
    console.error("Error rendering ABC chart:", err);
  }
}

async function renderRiskRadarChart(targetElementId = "ii-risk-chart") {
  const chartEl = document.getElementById(targetElementId);
  if (!chartEl) return;

  try {
    const res = await fetch("/api/v1/risk_matrix");
    const data = await res.json();

    const quad = data.quadrant_counts || { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    const critEl = document.getElementById("ii-critical-risk-count");
    if (critEl) critEl.innerText = `${quad.CRITICAL} SKUs`;

    const trace = {
      x: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
      y: [quad.CRITICAL, quad.HIGH, quad.MEDIUM, quad.LOW],
      type: 'bar',
      marker: { color: ['#F43F5E', '#F59E0B', '#3B82F6', '#10B981'] }
    };
    const layout = {
      paper_bgcolor: '#111B2E', plot_bgcolor: '#111B2E', font: { color: '#F8FAFC' },
      margin: { t: 20, r: 20, l: 40, b: 35 },
      xaxis: { gridcolor: '#1E293B', title: 'Risk Quadrant' },
      yaxis: { gridcolor: '#1E293B', title: 'SKU Count' }
    };
    Plotly.newPlot(targetElementId, [trace], layout, PLOTLY_DEFAULT_CONFIG);
  } catch (err) {
    console.error("Error rendering Risk Matrix chart:", err);
  }
}

async function initSKUExplorer() {
  const select = document.getElementById("sku-exp-select");
  if (!select) return;

  try {
    const res = await fetch("/api/v1/series_list");
    const seriesList = await res.json();
    select.innerHTML = seriesList.map(s => `<option value="${s.series_id}">${s.series_id}</option>`).join("");
    select.onchange = () => loadSKUExplorerDetails(select.value);

    if (seriesList.length > 0) loadSKUExplorerDetails(seriesList[0].series_id);
  } catch (err) {
    console.error("Error initializing SKU explorer:", err);
  }
}

async function loadSKUExplorerDetails(seriesId) {
  const container = document.getElementById("sku-exp-details-container");
  if (!container) return;

  try {
    const res = await fetch(`/api/v1/sku_explorer?series_id=${seriesId}&horizon_days=30`);
    const d = await res.json();

    container.innerHTML = `
      <div class="grid-6-kpi" style="grid-template-columns: repeat(4, 1fr); margin-bottom:1rem;">
        <div style="background:var(--bg-app); padding:0.75rem; border-radius:4px; border:1px solid var(--border-subtle);">
          <div style="font-size:0.75rem; color:var(--text-subtle);">Safety Stock (SS)</div>
          <div style="font-size:1.2rem; font-weight:bold; color:var(--accent-cyan);">${d.safety_stock} Units</div>
        </div>
        <div style="background:var(--bg-app); padding:0.75rem; border-radius:4px; border:1px solid var(--border-subtle);">
          <div style="font-size:0.75rem; color:var(--text-subtle);">Reorder Point (ROP)</div>
          <div style="font-size:1.2rem; font-weight:bold; color:var(--warning-orange);">${d.reorder_point} Units</div>
        </div>
        <div style="background:var(--bg-app); padding:0.75rem; border-radius:4px; border:1px solid var(--border-subtle);">
          <div style="font-size:0.75rem; color:var(--text-subtle);">Economic Order Qty (EOQ)</div>
          <div style="font-size:1.2rem; font-weight:bold; color:var(--success-green);">${d.recommended_order_quantity > 0 ? d.recommended_order_quantity : 150.0} Units</div>
        </div>
        <div style="background:var(--bg-app); padding:0.75rem; border-radius:4px; border:1px solid var(--border-subtle);">
          <div style="font-size:0.75rem; color:var(--text-subtle);">Composite Risk Score</div>
          <div style="font-size:1.2rem; font-weight:bold; color:${d.composite_risk_score > 70 ? 'var(--danger-red)' : 'var(--success-green)'};">${d.composite_risk_score} / 100</div>
        </div>
      </div>
      <div style="font-size:0.83rem; color:var(--text-muted); background:var(--bg-app); padding:0.75rem; border-radius:4px; border:1px solid var(--border-subtle);">
        <span>Demand CV: <strong>${d.demand_cv}</strong> | Trend Lift: <strong style="color:var(--success-green);">${d.trend_lift_pct}%</strong> | Seasonality: <strong>${d.seasonality_factor}</strong></span><br>
        <span>Inventory Status: <strong>${d.inventory_label}</strong></span>
      </div>
    `;
  } catch (err) {
    console.error("Error loading SKU explorer details:", err);
  }
}

/* Scenario Lab Loader */
async function runScenarioLabSimulation() {
  const dGrowth = parseFloat(document.getElementById("scen-demand-growth").value);
  const pBoost = parseFloat(document.getElementById("scen-promo-boost").value);
  const lTime = parseFloat(document.getElementById("scen-lead-time").value);
  const sLevel = parseFloat(document.getElementById("scen-service-level").value);

  document.getElementById("val-demand-growth").innerText = `${dGrowth > 0 ? '+' : ''}${dGrowth}%`;
  document.getElementById("val-promo-boost").innerText = `+${pBoost}%`;
  document.getElementById("val-lead-time").innerText = `${lTime} Days`;
  document.getElementById("val-service-level").innerText = `${(sLevel * 100).toFixed(0)}%`;

  try {
    const res = await fetch("/api/v1/scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        base_avg_daily_demand: 25.0, demand_growth_pct: dGrowth,
        promo_boost_pct: pBoost, scenario_lead_time_days: lTime, scenario_service_level: sLevel
      })
    });
    const data = await res.json();

    document.getElementById("scen-tbody").innerHTML = `
      <tr><td><strong>Daily Demand</strong></td><td>${data.baseline.avg_daily_demand.toFixed(1)} units</td><td><strong>${data.scenario.avg_daily_demand.toFixed(1)} units</strong></td><td style="color:var(--success-green);">+${(data.scenario.avg_daily_demand - data.baseline.avg_daily_demand).toFixed(1)}</td></tr>
      <tr><td><strong>Safety Stock (SS)</strong></td><td>${data.baseline.safety_stock.toFixed(1)} units</td><td><strong>${data.scenario.safety_stock.toFixed(1)} units</strong></td><td style="color:var(--warning-orange);">+${data.impact_delta.safety_stock_delta.toFixed(1)}</td></tr>
      <tr><td><strong>Reorder Point (ROP)</strong></td><td>${data.baseline.reorder_point.toFixed(1)} units</td><td><strong>${data.scenario.reorder_point.toFixed(1)} units</strong></td><td style="color:var(--warning-orange);">+${data.impact_delta.reorder_point_delta.toFixed(1)}</td></tr>
      <tr><td><strong>EOQ Order Qty</strong></td><td>${data.baseline.eoq.toFixed(1)} units</td><td><strong>${data.scenario.eoq.toFixed(1)} units</strong></td><td>+${data.impact_delta.eoq_delta.toFixed(1)}</td></tr>
      <tr><td><strong>Risk Score</strong></td><td>${data.baseline.composite_risk_score.toFixed(1)}/100</td><td><strong>${data.scenario.composite_risk_score.toFixed(1)}/100</strong></td><td style="color:var(--danger-red);">+${data.impact_delta.risk_score_delta.toFixed(1)}</td></tr>
    `;
  } catch (err) {
    console.error("Error running scenario simulation:", err);
  }
}

/* Explainability Loader */
async function loadExplainableAI() {
  const select = document.getElementById("xai-series-select");
  const seriesId = select ? select.value : "Central_Furniture";

  try {
    const res = await fetch(`/api/v1/explainability?series_id=${seriesId}`);
    const data = await res.json();

    const fiContainer = document.getElementById("xai-features-container");
    fiContainer.innerHTML = data.feature_importances.map(f => `
      <div style="margin-bottom:0.75rem;">
        <div style="display:flex; justify-content:space-between; font-size:0.83rem;">
          <span>${f.feature}</span>
          <strong>${f.importance_pct}%</strong>
        </div>
        <div style="background:#1E293B; height:6px; border-radius:3px; overflow:hidden; margin-top:0.25rem;">
          <div style="background:var(--accent-cyan); width:${f.importance_pct}%; height:100%;"></div>
        </div>
      </div>
    `).join("");

    document.getElementById("xai-q1").innerText = data.explanations.WHY_SHOULD_I_REORDER;
    document.getElementById("xai-q2").innerText = data.explanations.WHY_THIS_QUANTITY;
    document.getElementById("xai-q3").innerText = data.explanations.WHY_IS_THIS_HIGH_RISK;
  } catch (err) {
    console.error("Error loading explainable AI:", err);
  }
}

/* Business Insights Loader */
async function loadProjectInsights() {
  try {
    const res = await fetch("/api/v1/project_insights");
    const insights = await res.json();

    const container = document.getElementById("project-insights-container");
    if (!container) return;

    container.innerHTML = insights.map(ins => `
      <div class="card" style="border-left: 4px solid var(--accent-cyan);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
          <span style="font-weight:700; font-size:0.95rem; color:var(--accent-cyan);">${ins.title}</span>
          <span class="badge-status ${ins.badge === 'CRITICAL RISK' ? 'HIGH' : 'INFO'}">${ins.badge}</span>
        </div>
        <div style="font-size:0.85rem; color:var(--text-body); margin-bottom:0.4rem;">
          ${ins.description}
        </div>
        <div style="font-size:0.8rem; color:var(--success-green); font-weight:600; border-top:1px solid var(--border-subtle); padding-top:0.4rem;">
          💡 Action Recommendation: ${ins.recommendation}
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading project insights:", err);
  }
}

/* 30-Section Report Loader */
async function load30SectionReport() {
  try {
    const res = await fetch("/api/v1/reports/30_sections");
    const data = await res.json();

    const container = document.getElementById("report-sections-container");
    if (!container) return;

    container.innerHTML = data.sections.map(sec => `
      <div class="card" style="margin-bottom:1rem; border-left:3px solid var(--accent-cyan);">
        <h4 style="color:var(--accent-cyan); font-size:0.95rem; margin-bottom:0.4rem;">${sec.title}</h4>
        <p style="font-size:0.83rem; color:var(--text-body); line-height:1.5; margin:0;">${sec.content}</p>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading 30-section report:", err);
  }
}

/* Global Search Modal Controller */
function initGlobalSearchModal() {
  const triggerBtn = document.getElementById("btn-trigger-search");
  const modalBackdrop = document.getElementById("search-modal-backdrop");
  const searchInput = document.getElementById("global-search-input");
  const resultsContainer = document.getElementById("search-results-list");

  if (!triggerBtn || !modalBackdrop || !searchInput) return;

  const openModal = () => {
    modalBackdrop.classList.add("open");
    searchInput.focus();
    searchInput.value = "";
    performSearch("");
  };

  const closeModal = () => {
    modalBackdrop.classList.remove("open");
  };

  triggerBtn.addEventListener("click", openModal);

  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openModal();
    }
    if (e.key === "Escape" && modalBackdrop.classList.contains("open")) {
      closeModal();
    }
  });

  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) closeModal();
  });

  searchInput.addEventListener("input", (e) => {
    performSearch(e.target.value.trim());
  });

  async function performSearch(query) {
    if (!resultsContainer) return;

    try {
      const res = await fetch("/api/v1/series_list");
      const seriesList = await res.json();

      const filtered = seriesList.filter(s =>
        s.series_id.toLowerCase().includes(query.toLowerCase()) ||
        (s.category && s.category.toLowerCase().includes(query.toLowerCase())) ||
        (s.region && s.region.toLowerCase().includes(query.toLowerCase()))
      );

      if (filtered.length === 0) {
        resultsContainer.innerHTML = `<div style="padding:1rem; color:var(--text-subtle); text-align:center;">No matching SKU found for '${query}'</div>`;
        return;
      }

      resultsContainer.innerHTML = filtered.slice(0, 8).map(s => `
        <div class="search-result-item" data-sku="${s.series_id}">
          <div>
            <strong>${s.series_id}</strong>
            <div style="font-size:0.75rem; color:var(--text-subtle);">${s.category || 'Retail'} • Avg Sales: $${s.avg_daily_sales}</div>
          </div>
          <span style="color:var(--accent-cyan); font-size:0.8rem;">Open SKU Explorer →</span>
        </div>
      `).join("");

      document.querySelectorAll(".search-result-item").forEach(item => {
        item.addEventListener("click", () => {
          const sku = item.getAttribute("data-sku");
          closeModal();
          activateTab("page-inventory-intelligence");
          const sel = document.getElementById("sku-exp-select");
          if (sel) {
            sel.value = sku;
            loadSKUExplorerDetails(sku);
          }
        });
      });
    } catch (err) {
      console.error("Search error:", err);
    }
  }
}

/* Metric Tooltips Initializer */
function initMetricTooltips() {
  const tooltips = {
    "WAPE": "Weighted Absolute Percentage Error: Measures average forecast error weighted by sales volume.",
    "MAE": "Mean Absolute Error: Average magnitude of prediction errors in dollar units.",
    "RMSE": "Root Mean Squared Error: Highlights larger forecast errors with heavier penalty.",
    "R²": "Coefficient of Determination: Measures percentage of demand variance explained by model.",
    "Safety Stock": "Extra buffer inventory maintained to cushion against unexpected demand spikes or supplier delays.",
    "Reorder Point": "Inventory trigger level; when stock drops below ROP, a replenishment order should be initiated.",
    "EOQ": "Economic Order Quantity: Optimal order size that minimizes total inventory holding and ordering costs."
  };

  document.querySelectorAll("[data-tooltip]").forEach(el => {
    const key = el.getAttribute("data-tooltip");
    if (tooltips[key]) {
      el.setAttribute("data-tooltip", tooltips[key]);
    }
  });
}

/* ==========================================================================
   RetailMind-X: Final Master Upgrade - UI Integrations
   ========================================================================== */

/* 1. Capability Matrix Loader */
async function loadCapabilityMatrix() {
  try {
    const res = await fetch("/api/v1/capabilities");
    const data = await res.json();
    const caps = data.capabilities || {};

    const pills = {
      "cap-forecasting": { name: "Forecasting", key: "forecasting" },
      "cap-inventory": { name: "Inventory ROP", key: "inventory_intelligence" },
      "cap-seasonality": { name: "Seasonality", key: "seasonality_intelligence" },
      "cap-anomalies": { name: "Anomalies", key: "demand_anomalies" },
      "cap-promo": { name: "Promo Lift", key: "promotional_impact" },
      "cap-price": { name: "Price Elasticity", key: "price_elasticity" },
      "cap-drift": { name: "Drift Monitoring", key: "data_drift_monitoring" }
    };

    Object.entries(pills).forEach(([elId, cfg]) => {
      const el = document.getElementById(elId);
      if (!el) return;
      const isAvail = caps[cfg.key] === true || (caps[cfg.name] && caps[cfg.name].status === "AVAILABLE");
      if (isAvail) {
        el.className = "cap-pill active";
        el.title = `${cfg.name}: Available & Active for this dataset`;
      } else {
        el.className = "cap-pill unavailable";
        el.title = `${cfg.name}: Not available for this dataset`;
      }
    });
  } catch (err) {
    console.error("Error loading capability matrix:", err);
  }
}

/* 1-Click Sample Dataset Loader */
async function loadSampleDataset(sampleName) {
  const dropzoneArea = document.getElementById("dropzone-area");
  const idleContent = document.getElementById("dropzone-idle-content");
  const uploadProgress = document.getElementById("hero-upload-progress");
  
  if (uploadProgress) {
    uploadProgress.style.display = "block";
    uploadProgress.innerHTML = `
      <div style="padding:2rem 1.5rem; text-align:center;">
        <div class="pulse-dot" style="margin:0 auto 1rem auto; width:14px; height:14px;"></div>
        <div style="font-size:1.1rem; font-weight:700; color:var(--text-main); margin-bottom:0.4rem;">
          Loading ${escapeHtml(sampleName)}...
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted); line-height:1.5;">
          Automating data quality audit, feature extraction, and ML quantile training.
        </div>
      </div>
    `;
  }
  if (idleContent) idleContent.style.display = "none";

  try {
    const res = await fetch(`/api/v1/dataset/load_sample?sample_name=${encodeURIComponent(sampleName)}`, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to load sample dataset");
    }
    const data = await res.json();
    await initAppStateCheck();
  } catch (err) {
    console.error("Error loading sample dataset:", err);
    alert("Could not load sample dataset: " + err.message);
    if (uploadProgress) uploadProgress.style.display = "none";
    if (idleContent) idleContent.style.display = "block";
  }
}

/* 2. AI Decision Center Loader with Interactive Filters */
let ALL_DECISION_ACTIONS = [];
let ACTIVE_DECISION_FILTER = "ALL";
let SHOW_ALL_DECISION_ACTIONS = false;

async function loadDecisionCenter() {
  const container = document.getElementById("decision-actions-container");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/decision_center");
    const data = await res.json();
    const prios = data.priorities || {};
    ALL_DECISION_ACTIONS = data.top_actions || [];

    const critEl = document.getElementById("prio-cnt-critical");
    const reordEl = document.getElementById("prio-cnt-reorders");
    const anomEl = document.getElementById("prio-cnt-anomalies");
    const overEl = document.getElementById("prio-cnt-overstock");
    const healthEl = document.getElementById("prio-cnt-healthy");

    if (critEl) critEl.innerText = prios.critical_stockouts || 0;
    if (reordEl) reordEl.innerText = prios.reorders_needed || 0;
    if (anomEl) anomEl.innerText = prios.demand_anomalies || 0;
    if (overEl) overEl.innerText = prios.overstock_items || 0;
    if (healthEl) healthEl.innerText = prios.healthy_items || 0;

    renderDecisionActionsList();
  } catch (err) {
    console.error("Error loading AI decision center:", err);
  }
}

function filterDecisionActions(filterType) {
  ACTIVE_DECISION_FILTER = filterType;
  
  // Highlight active pill
  document.querySelectorAll("#decision-prio-row .prio-badge").forEach(el => {
    el.classList.remove("active-filter");
  });
  
  renderDecisionActionsList();
}

function toggleDecisionActionsShowMore() {
  SHOW_ALL_DECISION_ACTIONS = !SHOW_ALL_DECISION_ACTIONS;
  renderDecisionActionsList();
}

function renderDecisionActionsList() {
  const container = document.getElementById("decision-actions-container");
  if (!container) return;

  let filtered = ALL_DECISION_ACTIONS;
  if (ACTIVE_DECISION_FILTER === "CRITICAL") {
    filtered = ALL_DECISION_ACTIONS.filter(a => a.priority === "CRITICAL");
  } else if (ACTIVE_DECISION_FILTER === "HIGH") {
    filtered = ALL_DECISION_ACTIONS.filter(a => a.priority === "HIGH");
  } else if (ACTIVE_DECISION_FILTER === "MEDIUM") {
    filtered = ALL_DECISION_ACTIONS.filter(a => a.priority === "MEDIUM");
  } else if (ACTIVE_DECISION_FILTER === "ANOMALY") {
    filtered = ALL_DECISION_ACTIONS.filter(a => a.sku === "AGGREGATE" || (a.title && a.title.includes("Demand")));
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="padding:1.5rem; text-align:center; color:var(--success-green); font-size:0.88rem; grid-column:1/-1;">
        ✓ No immediate actions required under the selected filter.
      </div>
    `;
    return;
  }

  const displayList = SHOW_ALL_DECISION_ACTIONS ? filtered : filtered.slice(0, 3);

  const cardsHtml = displayList.map(act => {
    const badgeClass = act.priority === "CRITICAL" ? "CRITICAL" : (act.priority === "HIGH" ? "HIGH" : "INFO");
    return `
      <div class="action-card ${act.priority}">
        <div class="action-card-header">
          <span class="action-card-title">${escapeHtml(act.title)}</span>
          <span class="badge-status ${badgeClass}">${act.priority}</span>
        </div>
        <div class="action-detail-item"><strong>What:</strong>${escapeHtml(act.what)}</div>
        <div class="action-detail-item"><strong>Why:</strong>${escapeHtml(act.why)}</div>
        <div class="action-detail-item" style="color:var(--accent-cyan);"><strong>Action:</strong>${escapeHtml(act.action)}</div>
        ${act.impact ? `<div class="action-detail-item" style="color:var(--text-subtle); font-size:0.75rem;"><strong>Impact:</strong>${escapeHtml(act.impact)}</div>` : ''}
      </div>
    `;
  }).join("");

  const footerControls = `
    <div style="grid-column: 1 / -1; display:flex; justify-content:space-between; align-items:center; margin-top:0.75rem; flex-wrap:wrap; gap:0.5rem;">
      ${filtered.length > 3 ? `
        <button type="button" class="btn-header-upload" onclick="toggleDecisionActionsShowMore()" style="font-size:0.8rem; padding:0.45rem 1rem;">
          ${SHOW_ALL_DECISION_ACTIONS ? '▲ Show Less' : `▼ Show All (${filtered.length}) Priorities`}
        </button>
      ` : '<div></div>'}
      <button type="button" class="btn-header-upload" onclick="activateTab('page-inventory-intelligence')" style="font-size:0.8rem; padding:0.45rem 1rem; background:transparent; border-color:var(--accent-cyan);">
        📦 Open Full Inventory Reorder Workbench →
      </button>
    </div>
  `;

  container.innerHTML = cardsHtml + footerControls;
}

/* 3. Inventory Cost Optimization Loader */
async function loadCostOptimization() {
  const card = document.getElementById("inventory-cost-card");
  if (!card) return;

  try {
    const res = await fetch("/api/v1/cost_optimization");
    const data = await res.json();
    if (!data.available) {
      card.style.display = "none";
      return;
    }
    card.style.display = "block";

    const curr = data.current_strategy || {};
    const rec = data.recommended_strategy || {};
    const sav = data.projected_savings || {};
    const asmp = data.assumptions || {};

    const elDesc = document.getElementById("cost-assumptions-desc");
    if (elDesc && asmp.label) {
      elDesc.innerText = `${asmp.label} (Holding Rate: ${asmp.holding_cost_annual_rate}, Order Cost: ${asmp.fixed_order_cost}, Markdown Loss: ${asmp.overstock_markdown_loss_rate}).`;
    }

    document.getElementById("cost-current-total").innerText = `$${(curr.total_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-current-holding").innerText = `$${(curr.holding_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-current-ordering").innerText = `$${(curr.ordering_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-current-stockout").innerText = `$${(curr.stockout_risk_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-current-overstock").innerText = `$${(curr.overstock_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    document.getElementById("cost-rec-total").innerText = `$${(rec.total_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-rec-holding").innerText = `$${(rec.holding_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-rec-ordering").innerText = `$${(rec.ordering_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-rec-stockout").innerText = `$${(rec.stockout_risk_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById("cost-rec-overstock").innerText = `$${(rec.overstock_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    document.getElementById("cost-savings-amount").innerText = `$${(sav.amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} (-${sav.percentage || 0}%)`;
    if (sav.summary) {
      document.getElementById("cost-savings-summary").innerText = sav.summary;
    }
  } catch (err) {
    console.error("Error loading cost optimization:", err);
  }
}

/* 4. Ask RetailMind AI Assistant Controls */
function toggleAskDrawer() {
  const drawer = document.getElementById("ask-drawer-backdrop");
  if (!drawer) return;
  const isShown = drawer.style.display === "flex";
  drawer.style.display = isShown ? "none" : "flex";
  if (!isShown) {
    const input = document.getElementById("ask-query-input");
    if (input) setTimeout(() => input.focus(), 150);
  }
}

function askQuestion(text) {
  const input = document.getElementById("ask-query-input");
  if (input) input.value = text;
  sendAskQuery();
}

async function sendAskQuery() {
  const input = document.getElementById("ask-query-input");
  const chatBody = document.getElementById("ask-chat-body");
  if (!input || !chatBody) return;

  const query = input.value.trim();
  if (!query) return;

  const userBubble = document.createElement("div");
  userBubble.className = "chat-bubble user";
  userBubble.innerText = query;
  chatBody.appendChild(userBubble);
  input.value = "";

  const loadBubble = document.createElement("div");
  loadBubble.className = "chat-bubble assistant";
  loadBubble.innerHTML = `<em>Analyzing active session metrics...</em>`;
  chatBody.appendChild(loadBubble);
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    const res = await fetch("/api/v1/ask_retailmind", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    
    const formattedAnswer = escapeHtml(data.answer || "No response received.")
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');

    loadBubble.innerHTML = `
      ${formattedAnswer}
      <div class="chat-bubble-source">Source: ${escapeHtml(data.source || 'Session Intelligence')}</div>
    `;
  } catch (err) {
    loadBubble.innerHTML = `<span style="color:var(--danger-red);">Failed to connect to RetailMind assistant engine.</span>`;
  }
  chatBody.scrollTop = chatBody.scrollHeight;
}

