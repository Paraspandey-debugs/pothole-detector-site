/**
 * app.js - Client Application Logic for Pothole Detection & Severity Audit
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentFile = null;
  let currentSampleName = null;
  let currentResult = null;
  let activeTab = "annotated"; // 'annotated' | 'original' | 'split'

  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileInfoBanner = document.getElementById("fileInfoBanner");
  const fileName = document.getElementById("fileName");
  const btnClearFile = document.getElementById("btnClearFile");

  const confSlider = document.getElementById("confSlider");
  const confValue = document.getElementById("confValue");
  const iouSlider = document.getElementById("iouSlider");
  const iouValue = document.getElementById("iouValue");
  const btnResetParams = document.getElementById("btnResetParams");
  const checkMask = document.getElementById("checkMask");
  const checkLabels = document.getElementById("checkLabels");

  const btnAnalyze = document.getElementById("btnAnalyze");
  const btnSpinner = document.getElementById("btnSpinner");
  const btnText = document.getElementById("btnText");
  const scannerLine = document.getElementById("scannerLine");

  const samplesContainer = document.getElementById("samplesContainer");

  const tabAnnotated = document.getElementById("tabAnnotated");
  const tabOriginal = document.getElementById("tabOriginal");
  const tabSplit = document.getElementById("tabSplit");

  const mainImage = document.getElementById("mainImage");
  const splitViewContainer = document.getElementById("splitViewContainer");
  const splitOriginal = document.getElementById("splitOriginal");
  const splitAnnotated = document.getElementById("splitAnnotated");
  const emptyPlaceholder = document.getElementById("emptyPlaceholder");
  const imageMetaBadge = document.getElementById("imageMetaBadge");

  // Metric elements
  const metricCount = document.getElementById("metricCount");
  const metricCountBadge = document.getElementById("metricCountBadge");
  const metricDamage = document.getElementById("metricDamage");
  const metricSeverity = document.getElementById("metricSeverity");
  const metricSeverityScore = document.getElementById("metricSeverityScore");
  const metricLatency = document.getElementById("metricLatency");

  // Maintenance recommendation
  const maintenanceCard = document.getElementById("maintenanceCard");
  const maintenanceText = document.getElementById("maintenanceText");
  const priorityBadge = document.getElementById("priorityBadge");

  // Table & Exports
  const detectionsTableBody = document.getElementById("detectionsTableBody");
  const btnDownloadImg = document.getElementById("btnDownloadImg");
  const btnDownloadCsv = document.getElementById("btnDownloadCsv");
  const btnDownloadJson = document.getElementById("btnDownloadJson");

  // Render modal
  const renderModal = document.getElementById("renderModal");
  const btnRenderGuide = document.getElementById("btnRenderGuide");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnDismissModal = document.getElementById("btnDismissModal");

  // -------------------------------------------------------------
  // Sliders & Controls
  // -------------------------------------------------------------
  confSlider.addEventListener("input", (e) => {
    confValue.textContent = `${e.target.value}%`;
  });

  iouSlider.addEventListener("input", (e) => {
    iouValue.textContent = `${e.target.value}%`;
  });

  btnResetParams.addEventListener("click", () => {
    confSlider.value = 20;
    confValue.textContent = "20%";
    iouSlider.value = 45;
    iouValue.textContent = "45%";
    checkMask.checked = true;
    checkLabels.checked = true;
  });

  // -------------------------------------------------------------
  // File Upload & Drag-and-Drop
  // -------------------------------------------------------------
  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dropzone-active");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dropzone-active");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dropzone-active");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  function handleSelectedFile(file) {
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file (JPEG, PNG, WEBP).");
      return;
    }
    currentFile = file;
    currentSampleName = null;
    fileName.textContent = file.name;
    fileInfoBanner.classList.remove("hidden");

    // Clear active sample styling
    document.querySelectorAll(".sample-card").forEach((c) => {
      c.classList.remove("ring-2", "ring-amber-500", "bg-amber-500/10");
    });

    // Auto-trigger analysis
    runAnalysis();
  }

  btnClearFile.addEventListener("click", () => {
    currentFile = null;
    fileInput.value = "";
    fileInfoBanner.classList.add("hidden");
  });

  // -------------------------------------------------------------
  // Load Sample Images
  // -------------------------------------------------------------
  async function loadSamples() {
    try {
      const res = await fetch("/api/samples");
      const data = await res.json();
      samplesContainer.innerHTML = "";

      data.samples.forEach((sample, idx) => {
        const card = document.createElement("div");
        card.className =
          "sample-card group cursor-pointer p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-amber-500/50 transition-all flex flex-col justify-between";
        card.innerHTML = `
          <div class="flex items-center gap-2">
            <img src="${sample.url}" alt="${sample.title}" class="w-10 h-10 rounded object-cover border border-slate-800">
            <div class="overflow-hidden">
              <p class="text-xs font-semibold text-slate-200 group-hover:text-amber-400 truncate">${sample.title}</p>
              <span class="text-[10px] text-slate-400">${sample.category}</span>
            </div>
          </div>
        `;
        card.addEventListener("click", () => {
          document.querySelectorAll(".sample-card").forEach((c) => {
            c.classList.remove("ring-2", "ring-amber-500", "bg-amber-500/10");
          });
          card.classList.add("ring-2", "ring-amber-500", "bg-amber-500/10");
          currentSampleName = sample.filename;
          currentFile = null;
          fileInfoBanner.classList.add("hidden");
          fileInput.value = "";
          runAnalysis();
        });
        samplesContainer.appendChild(card);
      });

      // Auto-select first sample for initial presentation
      if (data.samples.length > 0) {
        const firstCard = samplesContainer.querySelector(".sample-card");
        if (firstCard) {
          firstCard.classList.add("ring-2", "ring-amber-500", "bg-amber-500/10");
          currentSampleName = data.samples[0].filename;
          runAnalysis();
        }
      }
    } catch (err) {
      console.error("Failed to load samples:", err);
    }
  }

  // -------------------------------------------------------------
  // Tab Switcher
  // -------------------------------------------------------------
  tabAnnotated.addEventListener("click", () => switchTab("annotated"));
  tabOriginal.addEventListener("click", () => switchTab("original"));
  tabSplit.addEventListener("click", () => switchTab("split"));

  function switchTab(tab) {
    activeTab = tab;
    tabAnnotated.className = "px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition-all";
    tabOriginal.className = "px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition-all";
    tabSplit.className = "px-3 py-1 text-xs font-medium rounded-md text-slate-400 hover:text-white transition-all";

    if (tab === "annotated") {
      tabAnnotated.className = "px-3 py-1 text-xs font-semibold rounded-md bg-amber-500 text-slate-950 transition-all";
      mainImage.classList.remove("hidden");
      splitViewContainer.classList.add("hidden");
      if (currentResult) mainImage.src = currentResult.annotated_image;
    } else if (tab === "original") {
      tabOriginal.className = "px-3 py-1 text-xs font-semibold rounded-md bg-amber-500 text-slate-950 transition-all";
      mainImage.classList.remove("hidden");
      splitViewContainer.classList.add("hidden");
      if (currentResult) mainImage.src = currentResult.original_image;
    } else if (tab === "split") {
      tabSplit.className = "px-3 py-1 text-xs font-semibold rounded-md bg-amber-500 text-slate-950 transition-all";
      mainImage.classList.add("hidden");
      splitViewContainer.classList.remove("hidden");
      splitViewContainer.classList.add("grid");
      if (currentResult) {
        splitOriginal.src = currentResult.original_image;
        splitAnnotated.src = currentResult.annotated_image;
      }
    }
  }

  // -------------------------------------------------------------
  // Run Analysis (POST /api/detect or /api/detect-sample)
  // -------------------------------------------------------------
  btnAnalyze.addEventListener("click", runAnalysis);

  async function runAnalysis() {
    if (!currentFile && !currentSampleName) {
      alert("Please upload a road image or click one of the quick test samples.");
      return;
    }

    const conf = parseFloat(confSlider.value) / 100.0;
    const iou = parseFloat(iouSlider.value) / 100.0;
    const drawLabels = checkLabels.checked;
    const drawMask = checkMask.checked;

    // UI Loading state
    btnSpinner.classList.remove("hidden");
    btnText.textContent = "Detecting Cavities...";
    btnAnalyze.disabled = true;
    scannerLine.classList.remove("hidden");

    try {
      let response;
      if (currentFile) {
        const formData = new FormData();
        formData.append("file", currentFile);
        formData.append("conf", conf.toString());
        formData.append("iou", iou.toString());
        formData.append("draw_labels", drawLabels ? "true" : "false");
        formData.append("draw_mask", drawMask ? "true" : "false");

        response = await fetch("/api/detect", {
          method: "POST",
          body: formData,
        });
      } else {
        const params = new URLSearchParams({
          sample_name: currentSampleName,
          conf: conf.toString(),
          iou: iou.toString(),
          draw_labels: drawLabels ? "true" : "false",
          draw_mask: drawMask ? "true" : "false",
        });
        response = await fetch(`/api/detect-sample?${params.toString()}`, {
          method: "POST",
        });
      }

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Analysis failed.");
      }

      const data = await response.json();
      currentResult = data;
      renderResults(data);

    } catch (err) {
      console.error("Detection error:", err);
      alert(`Error during detection: ${err.message}`);
    } finally {
      btnSpinner.classList.add("hidden");
      btnText.textContent = "Analyze Road Imagery";
      btnAnalyze.disabled = false;
      scannerLine.classList.add("hidden");
    }
  }

  // -------------------------------------------------------------
  // Render Detection Results
  // -------------------------------------------------------------
  function renderResults(data) {
    emptyPlaceholder.classList.add("hidden");

    // Display image based on active tab
    if (activeTab === "split") {
      splitOriginal.src = data.original_image;
      splitAnnotated.src = data.annotated_image;
      splitViewContainer.classList.remove("hidden");
      splitViewContainer.classList.add("grid");
      mainImage.classList.add("hidden");
    } else {
      mainImage.src = activeTab === "original" ? data.original_image : data.annotated_image;
      mainImage.classList.remove("hidden");
      splitViewContainer.classList.add("hidden");
    }

    // Image resolution badge
    if (data.image_metadata) {
      imageMetaBadge.textContent = `${data.image_metadata.width} × ${data.image_metadata.height} px`;
      imageMetaBadge.classList.remove("hidden");
    }

    // 1. Metric: Pothole count
    metricCount.textContent = data.pothole_count;
    if (data.pothole_count === 0) {
      metricCountBadge.textContent = "No potholes detected";
      metricCountBadge.className = "mt-1 text-[10px] text-emerald-400 font-medium";
    } else {
      metricCountBadge.textContent = `${data.pothole_count} cavity region(s)`;
      metricCountBadge.className = "mt-1 text-[10px] text-amber-400 font-medium";
    }

    // 2. Metric: Surface damage percentage
    metricDamage.textContent = `${data.surface_damage_percentage}%`;

    // 3. Metric: Severity
    const sev = data.severity;
    metricSeverity.textContent = sev.level;
    metricSeverity.className = `inline-flex px-2 py-0.5 text-xs font-bold rounded-md border ${sev.badge_class}`;
    metricSeverityScore.textContent = `Index: ${sev.score} / 100`;

    // 4. Metric: Latency
    metricLatency.textContent = data.timing.inference_time_ms;

    // Maintenance recommendation card
    maintenanceCard.classList.remove("hidden");
    maintenanceText.textContent = sev.action;
    priorityBadge.textContent = sev.priority;
    priorityBadge.className = `px-2 py-0.5 text-[10px] font-bold rounded-full border ${sev.badge_class}`;

    // Populate Detections Table
    detectionsTableBody.innerHTML = "";
    if (data.detections.length === 0) {
      detectionsTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="py-6 text-center text-slate-500 font-sans">
            No pothole cavities detected at ${confSlider.value}% confidence threshold.
          </td>
        </tr>
      `;
    } else {
      data.detections.forEach((d) => {
        const row = document.createElement("tr");
        row.className = "table-row-highlight hover:bg-slate-800/50 transition-colors";
        row.innerHTML = `
          <td class="py-2.5 px-3 font-bold text-amber-400">#${d.id}</td>
          <td class="py-2.5 px-3 font-semibold text-slate-200">${d.confidence_percentage}</td>
          <td class="py-2.5 px-3 text-slate-400">[${d.bbox.xmin}, ${d.bbox.ymin}, ${d.bbox.xmax}, ${d.bbox.ymax}]</td>
          <td class="py-2.5 px-3 text-slate-300">${d.bbox.width} × ${d.bbox.height} px</td>
          <td class="py-2.5 px-3 text-amber-300">${d.area_percentage}% <span class="text-slate-500 text-[10px]">(${d.area_pixels} px)</span></td>
          <td class="py-2.5 px-3 font-sans text-slate-300">${d.location}</td>
        `;
        detectionsTableBody.appendChild(row);
      });
    }
  }

  // -------------------------------------------------------------
  // Exports: Image, JSON, CSV
  // -------------------------------------------------------------
  btnDownloadImg.addEventListener("click", () => {
    if (!currentResult) return;
    const link = document.createElement("a");
    link.href = currentResult.annotated_image;
    link.download = `pothole_audit_${Date.now()}.jpg`;
    link.click();
  });

  btnDownloadJson.addEventListener("click", () => {
    if (!currentResult) {
      alert("Run an inspection first to download audit data.");
      return;
    }
    // Prepare export json (strip huge base64 strings to keep JSON lightweight)
    const exportData = { ...currentResult };
    delete exportData.annotated_image;
    delete exportData.original_image;

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `pothole_audit_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  });

  btnDownloadCsv.addEventListener("click", () => {
    if (!currentResult || !currentResult.detections) {
      alert("Run an inspection first to export CSV.");
      return;
    }

    const headers = [
      "Pothole_ID",
      "Confidence",
      "Xmin",
      "Ymin",
      "Xmax",
      "Ymax",
      "Width_px",
      "Height_px",
      "Area_px",
      "Area_Percentage",
      "Location_Quadrant",
      "Severity_Level",
      "Severity_Score",
    ];

    const rows = currentResult.detections.map((d) => [
      d.id,
      d.confidence,
      d.bbox.xmin,
      d.bbox.ymin,
      d.bbox.xmax,
      d.bbox.ymax,
      d.bbox.width,
      d.bbox.height,
      d.area_pixels,
      d.area_percentage,
      `"${d.location}"`,
      currentResult.severity.level,
      currentResult.severity.score,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `pothole_audit_report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // -------------------------------------------------------------
  // Render Deployment Modal
  // -------------------------------------------------------------
  btnRenderGuide.addEventListener("click", () => renderModal.classList.remove("hidden"));
  btnCloseModal.addEventListener("click", () => renderModal.classList.add("hidden"));
  btnDismissModal.addEventListener("click", () => renderModal.classList.add("hidden"));
  renderModal.addEventListener("click", (e) => {
    if (e.target === renderModal) renderModal.classList.add("hidden");
  });

  // Start by loading sample images
  loadSamples();
});
