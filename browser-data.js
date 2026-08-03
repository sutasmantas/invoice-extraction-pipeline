(() => {
  const field = (name, label, value, confidence = 0.94, status = "confirmed") => ({
    name, label, value, normalized_value: value, confidence, status,
    source_text: value ? `${label}: ${value}` : "Not found", provenance: null,
  });
  const invoice = (id, filename, vendor, number, date, po, terms, subtotal, tax, total, review = false) => ({
    id, filename, document_type: "invoice", status: review ? "needs_review" : "ready",
    fields: [
      field("invoice_number", "Invoice number", number),
      field("vendor", "Vendor", vendor),
      field("vat_id", "VAT ID", vendor.includes("Northstar") ? "DE27844590I" : "EU123456789", review ? 0.71 : 0.94, review ? "needs_review" : "confirmed"),
      field("invoice_date", "Invoice date", date),
      field("po_number", "Purchase order", po, po ? 0.94 : 0, po ? "confirmed" : "needs_review"),
      field("payment_terms", "Payment terms", terms, review ? 0.78 : 0.91, review ? "needs_review" : "confirmed"),
      field("subtotal", "Subtotal", subtotal), field("tax", "Tax", tax), field("total", "Total", total),
    ],
    line_items: [], schema_id: "invoice-v1", extraction_method: "OCR + schema validation", created_at: "2026-08-03T10:32:35Z",
  });
  let documents = [
    invoice("invoice-1048", "northstar-invoice.pdf", "Northstar Technology Services GmbH", "INV-2026-1048", "18 Jul 2026", "PO-7712", "Net 30 days", "$13,200.00", "$1,080.00", "$14,280.00", true),
    invoice("invoice-73018", "meridian-platforms-invoice.pdf", "Meridian Platforms SAS", "MP-73018", "24 Jul 2026", "PO-7301", "Net 45 days", "€21,600.00", "€4,320.00", "€25,920.00"),
    invoice("invoice-041", "cloud-harbor-invoice.pdf", "Cloud Harbor Systems Ltd", "CH-2026-041", "22 Jul 2026", "PO-8841", "Net 15 days", "$8,420.00", "$1,684.00", "$10,104.00"),
    invoice("invoice-882", "westline-renewal-invoice.pdf", "Westline Operations GmbH", "WL-2026-882", "27 Jul 2026", "", "Net 30 days", "€6,800.00", "€1,292.00", "€8,092.00", true),
  ];
  const clone = (value) => structuredClone(value);
  window.LEDGER_BROWSER_API = async (path, options = {}) => {
    await new Promise((resolve) => setTimeout(resolve, 80));
    if (path === "/api/health") return { status: "ok", ocr: "tesseract", pdf: "pdfium" };
    if (path === "/api/documents" && (!options.method || options.method === "GET")) return clone(documents);
    if (path === "/api/documents" && options.method === "POST") {
      const created = invoice(`upload-${Date.now()}`, "uploaded-invoice.pdf", "Uploaded supplier", "PENDING", "03 Aug 2026", "", "Net 30 days", "—", "—", "—", true);
      documents.unshift(created);
      return clone(created);
    }
    const exportMatch = path.match(/^\/api\/documents\/([^/]+)\/export$/);
    if (exportMatch) {
      const item = documents.find((document) => document.id === exportMatch[1]);
      return { document_id: item.id, filename: item.filename, fields: Object.fromEntries(item.fields.map((entry) => [entry.name, entry.normalized_value])) };
    }
    const patchMatch = path.match(/^\/api\/documents\/([^/]+)\/fields\/([^/]+)$/);
    if (patchMatch && options.method === "PATCH") {
      const item = documents.find((document) => document.id === patchMatch[1]);
      const selected = item.fields.find((entry) => entry.name === patchMatch[2]);
      const payload = JSON.parse(options.body || "{}");
      selected.value = payload.value;
      selected.normalized_value = payload.value;
      selected.confidence = 1;
      selected.status = "confirmed";
      item.status = item.fields.some((entry) => entry.status === "needs_review") ? "needs_review" : "ready";
      return clone(item);
    }
    throw new Error(`Unknown browser-workspace route: ${path}`);
  };
})();
