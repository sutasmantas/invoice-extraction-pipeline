const state = { documents: [], selectedId: null, selectedField: null };
const invoicePaper = document.querySelector(".invoice-paper");
const seededPaper = invoicePaper.innerHTML;

const elements = {
  documentView: document.querySelector("#document-view"),
  queueView: document.querySelector("#queue-view"),
  pageTitle: document.querySelector("#page-title"),
  reviewInput: document.querySelector("#review-input"),
  reviewMessage: document.querySelector("#review-message"),
  selectedConfidence: document.querySelector("#selected-confidence"),
  confirmField: document.querySelector("#confirm-field"),
  exportButton: document.querySelector("#export-button"),
  toast: document.querySelector("#toast"),
  reviewCount: document.querySelector("#review-count"),
  uploadButton: document.querySelector("#upload-button"),
  documentUpload: document.querySelector("#document-upload"),
  documentCount: document.querySelector("#document-count"),
  queueCount: document.querySelector("#queue-count"),
  serviceState: document.querySelector("#service-state"),
  serviceSummary: document.querySelector("#service-summary"),
  invoiceCount: document.querySelector("#invoice-count"),
  queueStat: document.querySelector("#queue-stat"),
  readyStat: document.querySelector("#ready-stat"),
  fieldsStat: document.querySelector("#fields-stat"),
  processedLabel: document.querySelector("#processed-label"),
  documentSearch: document.querySelector("#document-search"),
  reviewNext: document.querySelector("#review-next"),
  documentList: document.querySelector(".document-list"),
  detailsSection: document.querySelector(".field-section:not(.totals-section)"),
  totalsSection: document.querySelector(".totals-section"),
  fieldCount: document.querySelector(".field-count"),
  queueCard: document.querySelector(".queue-card"),
};

async function api(path, options = {}) {
  if (window.LEDGER_BROWSER_API && (location.hostname.endsWith("github.io") || new URLSearchParams(location.search).has("static"))) {
    return window.LEDGER_BROWSER_API(path, options);
  }
  const response = await fetch(path, options);
  if (response.ok) return response.json();
  let message = `Request failed (${response.status})`;
  try {
    message = (await response.json()).detail || message;
  } catch {
    // Preserve the status when an upstream response is not JSON.
  }
  throw new Error(message);
}

function create(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function uiName(name) {
  return name.replaceAll("_", "-");
}

function selectedDocument() {
  return state.documents.find((document) => document.id === state.selectedId);
}

function showToast(title, message) {
  elements.toast.querySelector("strong").textContent = title;
  elements.toast.querySelector("small").textContent = message;
  elements.toast.classList.add("show");
  window.setTimeout(() => elements.toast.classList.remove("show"), 3500);
}

function alignSourceHighlights() {
  if (invoicePaper.classList.contains("generic-preview")) return;
  const paperRect = invoicePaper.getBoundingClientRect();
  invoicePaper.querySelectorAll(".bounding-box[data-field]").forEach((box) => {
    const source = invoicePaper.querySelector(`[data-source-field="${box.dataset.field}"]`);
    if (!source) return;
    const sourceRect = source.getBoundingClientRect();
    box.style.left = `${sourceRect.left - paperRect.left - 4}px`;
    box.style.top = `${sourceRect.top - paperRect.top - 3}px`;
    box.style.width = `${sourceRect.width + 8}px`;
    box.style.height = `${sourceRect.height + 6}px`;
  });
}

function setView(view) {
  const showQueue = view === "queue";
  elements.documentView.hidden = showQueue;
  elements.queueView.hidden = !showQueue;
  elements.pageTitle.textContent = showQueue ? "Review queue" : "Document review";
  elements.exportButton.hidden = showQueue;
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  if (!showQueue) window.requestAnimationFrame(alignSourceHighlights);
}

function renderDocumentList() {
  elements.documentList.querySelectorAll(".document-item").forEach((item) => item.remove());
  const query = elements.documentSearch.value.trim().toLowerCase();
  state.documents
    .filter((document) => document.filename.toLowerCase().includes(query))
    .forEach((document) => {
    const item = create(
      "article",
      `document-item${document.id === state.selectedId ? " selected" : ""}`,
    );
    item.dataset.documentId = document.id;
    const copy = create("div", "document-copy");
    const flagged = document.fields.filter((field) => field.status === "needs_review").length;
    const status = create(
      "em",
      flagged ? "needs-review" : "complete",
      flagged ? `${flagged} need review` : "Ready",
    );
    const meta = create("div");
    meta.append(status, create("small", "", new Date(document.created_at).toLocaleDateString()));
    copy.append(
      create("strong", "", document.filename),
      create("span", "", `${document.document_type} · ${document.fields.length} fields`),
      meta,
    );
    item.append(create("div", "file-badge pdf", document.filename.split(".").pop().toUpperCase()), copy);
    elements.documentList.append(item);
    });
}

function fieldRow(field) {
  const row = create(
    "button",
    `field-row${field.status === "needs_review" ? " review-field" : ""}`,
  );
  row.dataset.field = uiName(field.name);
  const copy = create("span");
  copy.append(create("small", "", field.label), create("strong", "", field.value || "Not found"));
  row.append(copy);
  if (field.status === "needs_review") row.append(create("i", "warning", "!"));
  row.append(
    create(
      "em",
      `confidence ${field.status === "needs_review" ? "low" : "high"}`,
      `${Math.round(field.confidence * 100)}%`,
    ),
  );
  row.addEventListener("click", () => selectField(field.name));
  return row;
}

function renderFields(document) {
  elements.detailsSection.querySelectorAll(".field-row").forEach((row) => row.remove());
  elements.totalsSection.querySelectorAll(".field-row").forEach((row) => row.remove());
  const amountNames = new Set(["subtotal", "tax", "total"]);
  document.fields.forEach((field) => {
    (amountNames.has(field.name) ? elements.totalsSection : elements.detailsSection).append(
      fieldRow(field),
    );
  });
  elements.fieldCount.textContent = `${document.fields.length} fields`;
  const flagged = document.fields.filter((field) => field.status === "needs_review").length;
  elements.reviewCount.textContent = `${flagged} field${flagged === 1 ? "" : "s"}`;
  elements.reviewCount.className = flagged ? "amber-text" : "green-text";
}

function renderPreview(document) {
  if (document.filename === "sample-invoice.txt") {
    if (invoicePaper.classList.contains("generic-preview")) {
      invoicePaper.classList.remove("generic-preview");
      invoicePaper.innerHTML = seededPaper;
    }
    window.requestAnimationFrame(alignSourceHighlights);
    return;
  }
  invoicePaper.classList.add("generic-preview");
  invoicePaper.replaceChildren();
  invoicePaper.append(
    create("div", "generic-title", document.filename),
    create("p", "generic-note", "Extracted source matches from the uploaded document"),
  );
  document.fields
    .filter((field) => field.source_text !== "Not found")
    .forEach((field) => {
      const line = create("div", "source-line");
      line.dataset.field = uiName(field.name);
      line.append(create("span", "", field.label), create("strong", "", field.source_text));
      line.addEventListener("click", () => selectField(field.name));
      invoicePaper.append(line);
    });
}

function selectField(fieldName) {
  const selected = selectedDocument();
  const field = selected?.fields.find((candidate) => candidate.name === fieldName);
  if (!field) return;
  state.selectedField = fieldName;
  const fieldId = uiName(fieldName);
  window.document.querySelectorAll("[data-field]").forEach((node) => {
    node.classList.toggle("active", node.dataset.field === fieldId);
  });
  elements.reviewInput.value = field.value;
  elements.selectedConfidence.textContent = `${Math.round(field.confidence * 100)}% confidence`;
  elements.reviewMessage.textContent =
    field.status === "needs_review"
      ? `Review against source: ${field.source_text}`
      : "This value passed extraction validation.";
  elements.confirmField.textContent =
    field.status === "confirmed" ? "Field confirmed" : "Confirm correction";
  elements.confirmField.disabled = field.status === "confirmed";
}

function renderSelected() {
  const document = selectedDocument();
  if (!document) return;
  renderDocumentList();
  renderFields(document);
  renderPreview(document);
  const preferred =
    document.fields.find((field) => field.status === "needs_review") || document.fields[0];
  selectField(preferred.name);
}

function renderQueue() {
  elements.queueCard
    .querySelectorAll(".queue-row:not(.queue-labels)")
    .forEach((row) => row.remove());
  state.documents.forEach((document) => {
    const flagged = document.fields.filter((field) => field.status === "needs_review");
    const lowest = [...document.fields].sort((a, b) => a.confidence - b.confidence)[0];
    const row = create("div", `queue-row${flagged.length ? " highlighted" : ""}`);
    const file = create("span", "queue-document");
    const copy = create("span");
    copy.append(create("strong", "", document.filename), create("small", "", document.id.slice(0, 8)));
    file.append(create("i", "file-badge pdf", "DOC"), copy);
    row.append(
      file,
      create("span", "", document.document_type),
      create("span", "", `${document.fields.length} extracted · ${flagged.length} flagged`),
      create("span", "", `${Math.round(lowest.confidence * 100)}% ${lowest.label}`),
      create("span", "", new Date(document.created_at).toLocaleDateString()),
      create("span", "", flagged.length ? "Needs review" : "Ready"),
      create("span", "", "→"),
    );
    row.dataset.documentId = document.id;
    elements.queueCard.append(row);
  });
}

function updateMetrics() {
  const queued = state.documents.filter((document) => document.status === "needs_review").length;
  elements.documentCount.textContent = String(state.documents.length);
  elements.queueCount.textContent = String(queued);
  elements.invoiceCount.textContent = String(state.documents.length);
  elements.queueStat.textContent = String(queued);
  elements.readyStat.textContent = String(state.documents.length - queued);
  elements.fieldsStat.textContent = String(
    state.documents.reduce((total, document) => total + document.fields.length, 0),
  );
  elements.serviceState.textContent = "API healthy";
  elements.serviceSummary.textContent = `${queued} need review · ${state.documents.length - queued} ready`;
  elements.processedLabel.textContent = `${state.documents.length} persistent document${state.documents.length === 1 ? "" : "s"}`;
  elements.reviewNext.disabled = queued === 0;
}

async function refresh(preferredId = state.selectedId) {
  state.documents = await api("/api/documents");
  state.selectedId =
    state.documents.find((document) => document.id === preferredId)?.id ||
    state.documents[0]?.id ||
    null;
  updateMetrics();
  renderQueue();
  renderSelected();
}

async function confirmCorrection() {
  if (!state.selectedId || !state.selectedField) return;
  elements.confirmField.disabled = true;
  try {
    const updated = await api(
      `/api/documents/${state.selectedId}/fields/${state.selectedField}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: elements.reviewInput.value }),
      },
    );
    state.documents = state.documents.map((document) =>
      document.id === updated.id ? updated : document,
    );
    renderQueue();
    renderSelected();
    showToast("Correction saved", "The reviewed value is persisted and ready for export.");
  } catch (error) {
    elements.confirmField.disabled = false;
    showToast("Correction failed", error.message);
  }
}

async function exportData() {
  if (!state.selectedId) return;
  try {
    const payload = await api(`/api/documents/${state.selectedId}/export`);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${selectedDocument().filename}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    showToast("Structured data exported", `${Object.keys(payload.data).length} normalized fields`);
  } catch (error) {
    showToast("Export failed", error.message);
  }
}

async function uploadDocument() {
  const [file] = elements.documentUpload.files;
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  elements.uploadButton.disabled = true;
  elements.uploadButton.textContent = "Extracting…";
  try {
    const created = await api("/api/documents", { method: "POST", body });
    await refresh(created.id);
    showToast("Document extracted", `${created.fields.length} fields added to the review queue.`);
  } catch (error) {
    showToast("Extraction failed", error.message);
  } finally {
    elements.uploadButton.disabled = false;
    elements.uploadButton.textContent = "Upload document";
    elements.documentUpload.value = "";
  }
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});
elements.documentList.addEventListener("click", (event) => {
  const item = event.target.closest("[data-document-id]");
  if (!item) return;
  state.selectedId = item.dataset.documentId;
  renderSelected();
});
elements.queueCard.addEventListener("click", (event) => {
  const row = event.target.closest("[data-document-id]");
  if (!row) return;
  state.selectedId = row.dataset.documentId;
  setView("document");
  renderSelected();
});
elements.confirmField.addEventListener("click", confirmCorrection);
elements.exportButton.addEventListener("click", exportData);
elements.uploadButton.addEventListener("click", () => elements.documentUpload.click());
elements.documentUpload.addEventListener("change", uploadDocument);
elements.documentSearch.addEventListener("input", renderDocumentList);
elements.reviewNext.addEventListener("click", () => {
  const next = state.documents.find((document) => document.status === "needs_review");
  if (!next) return;
  state.selectedId = next.id;
  setView("document");
  renderSelected();
});
invoicePaper.addEventListener("click", (event) => {
  const source = event.target.closest("[data-field]");
  if (!source) return;
  const field = selectedDocument()?.fields.find(
    (candidate) => uiName(candidate.name) === source.dataset.field,
  );
  if (field) selectField(field.name);
});
window.addEventListener("resize", alignSourceHighlights);

if (window.LEDGER_BROWSER_API && (location.hostname.endsWith("github.io") || new URLSearchParams(location.search).has("static"))) {
  const apiReference = document.getElementById("api-reference");
  apiReference.href = "https://github.com/sutasmantas/invoice-extraction-pipeline";
  apiReference.innerHTML = "<span>↗</span> View code";
}

api("/api/health")
  .then(() => refresh())
  .catch((error) => {
    elements.serviceState.textContent = "API unavailable";
    elements.serviceSummary.textContent = error.message;
  });
