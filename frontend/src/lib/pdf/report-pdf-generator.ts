/**
 * AI Infrastructure Report PDF Generator.
 *
 * Generates an evidence-grounded, production-grade PDF document
 * from the live generated InfrastructureReport state using jsPDF.
 */

import { jsPDF } from "jspdf";
import type { InfrastructureReport, PriorityLevel, ReportFilters } from "@/lib/api/infrastructure";

const PRIORITY_COLORS: Record<PriorityLevel, [number, number, number]> = {
  critical: [220, 38, 38], // #dc2626
  high: [234, 88, 12], // #ea580c
  moderate: [217, 119, 6], // #d97706
  low: [79, 70, 229], // #4f46e5
};

export function exportInfrastructureReportPdf(
  report: InfrastructureReport,
  filters: ReportFilters,
): void {
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 14;
  const contentWidth = pageWidth - margin * 2;
  let y = margin;

  const checkPageBreak = (neededHeight: number) => {
    if (y + neededHeight > pageHeight - margin - 8) {
      doc.addPage();
      y = margin;
      drawHeaderFooter();
    }
  };

  const drawHeaderFooter = () => {
    const pageNum = doc.getNumberOfPages();
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(140, 140, 140);
    // Running header (on pages > 1)
    if (pageNum > 1) {
      doc.text("AI Infrastructure Report — Road Safety Decision Support", margin, 9);
      doc.text(report.generatedLabel, pageWidth - margin, 9, { align: "right" });
      doc.setDrawColor(220, 220, 220);
      doc.setLineWidth(0.2);
      doc.line(margin, 11, pageWidth - margin, 11);
    }
    // Running footer
    doc.setDrawColor(220, 220, 220);
    doc.setLineWidth(0.2);
    doc.line(margin, pageHeight - 10, pageWidth - margin, pageHeight - 10);
    doc.text(
      "Confidential — For Transport Planning and Road Safety Engineering Review",
      margin,
      pageHeight - 6,
    );
    doc.text(`Page ${pageNum}`, pageWidth - margin, pageHeight - 6, { align: "right" });
  };

  // ==========================================
  // 1. TITLE & DOCUMENT HEADER
  // ==========================================
  doc.setFillColor(15, 23, 42); // #0f172a slate-900
  doc.rect(margin, y, contentWidth, 24, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(255, 255, 255);
  doc.text("AI Infrastructure & Road Safety Report", margin + 5, y + 9);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8.5);
  doc.setTextColor(203, 213, 225); // slate-300
  doc.text(
    "Multi-Model Evidence Synthesis (Student A Severity, Student B Hotspots, Student C GNN Risk)",
    margin + 5,
    y + 15,
  );
  doc.text(report.generatedLabel, margin + 5, y + 20);

  y += 28;

  // ==========================================
  // 2. SCOPE & FILTER METADATA
  // ==========================================
  doc.setFillColor(248, 250, 252); // slate-50
  doc.setDrawColor(226, 232, 240); // slate-200
  doc.setLineWidth(0.3);
  doc.rect(margin, y, contentWidth, 14, "FD");

  const filterItems = [
    `Region: ${filters.region.toUpperCase()}`,
    `Period: ${filters.period.replace(/_/g, " ")}`,
    `Threshold: ${filters.threshold}`,
    `Strategic Focus: ${filters.focus.replace(/_/g, " ")}`,
  ];

  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.setTextColor(51, 65, 85); // slate-700
  const colWidth = contentWidth / 4;
  filterItems.forEach((text, i) => {
    doc.text(text, margin + 4 + i * colWidth, y + 8.5);
  });

  y += 18;

  // ==========================================
  // Helper: Section Headings
  // ==========================================
  const renderSectionHeader = (title: string) => {
    checkPageBreak(12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(15, 23, 42);
    doc.text(title, margin, y + 5);

    doc.setDrawColor(203, 213, 225);
    doc.setLineWidth(0.4);
    doc.line(margin, y + 7, pageWidth - margin, y + 7);
    y += 11;
  };

  // ==========================================
  // 3. EXECUTIVE DECISION-SUPPORT SUMMARY
  // ==========================================
  if (report.summary) {
    renderSectionHeader("1. Executive Priority Summary");

    const summaryRows = [
      { label: "Main Risk Theme", val: report.summary.theme },
      { label: "Highest-Priority Action", val: report.summary.topIntervention },
      { label: "Dominant Risk Signal", val: report.summary.keySignal },
      { label: "Operational Next Step", val: report.summary.nextStep },
    ];

    summaryRows.forEach((row) => {
      const labelText = `${row.label}: `;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      const labelWidth = doc.getTextWidth(labelText);

      const splitVal = doc.splitTextToSize(row.val, contentWidth - labelWidth - 6);
      const blockHeight = Math.max(splitVal.length * 4.5, 6);

      checkPageBreak(blockHeight + 3);

      doc.setFillColor(241, 245, 249);
      doc.rect(margin, y, contentWidth, blockHeight + 2, "F");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(30, 41, 59);
      doc.text(labelText, margin + 3, y + 4.5);

      doc.setFont("helvetica", "normal");
      doc.setTextColor(71, 85, 105);
      doc.text(splitVal, margin + 3 + labelWidth, y + 4.5);

      y += blockHeight + 3.5;
    });

    y += 4;
  }

  // ==========================================
  // 4. SYNTHESIZED RISK SIGNALS
  // ==========================================
  if (report.signals && report.signals.length > 0) {
    renderSectionHeader("2. Synthesized Risk Signals");

    report.signals.forEach((sig) => {
      const splitNote = doc.splitTextToSize(sig.note, contentWidth - 8);
      const boxHeight = 11 + splitNote.length * 4;

      checkPageBreak(boxHeight + 3);

      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(226, 232, 240);
      doc.setLineWidth(0.3);
      doc.rect(margin, y, contentWidth, boxHeight, "FD");

      // Priority pill
      const color = PRIORITY_COLORS[sig.level] || [100, 100, 100];
      doc.setFillColor(color[0], color[1], color[2]);
      doc.rect(margin + 3, y + 3, 16, 4.5, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(6.5);
      doc.setTextColor(255, 255, 255);
      doc.text(sig.level.toUpperCase(), margin + 11, y + 6.2, { align: "center" });

      // Signal Label & Value
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(15, 23, 42);
      doc.text(sig.label, margin + 22, y + 6.5);

      doc.setFont("helvetica", "bold");
      doc.setTextColor(color[0], color[1], color[2]);
      doc.text(sig.value, pageWidth - margin - 4, y + 6.5, { align: "right" });

      // Note
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(100, 116, 139);
      doc.text(splitNote, margin + 4, y + 12);

      y += boxHeight + 3;
    });

    y += 4;
  }

  // ==========================================
  // 5. RANKED PRIORITY INTERVENTIONS
  // ==========================================
  if (report.interventions && report.interventions.length > 0) {
    renderSectionHeader("3. Priority Infrastructure Interventions");

    report.interventions.forEach((item, index) => {
      const splitRationale = doc.splitTextToSize(`Rationale: ${item.rationale}`, contentWidth - 16);
      const boxHeight = 14 + splitRationale.length * 4;

      checkPageBreak(boxHeight + 3);

      doc.setFillColor(248, 250, 252);
      doc.setDrawColor(226, 232, 240);
      doc.rect(margin, y, contentWidth, boxHeight, "FD");

      // Number badge
      doc.setFillColor(15, 23, 42);
      doc.rect(margin + 3, y + 3, 6, 6, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.5);
      doc.setTextColor(255, 255, 255);
      doc.text(String(index + 1), margin + 6, y + 7.2, { align: "center" });

      // Intervention title
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(15, 23, 42);
      doc.text(item.intervention, margin + 12, y + 7.2);

      // Level badge
      const color = PRIORITY_COLORS[item.level] || [100, 100, 100];
      doc.setFillColor(color[0], color[1], color[2]);
      doc.rect(pageWidth - margin - 22, y + 3.5, 18, 4.5, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(6.5);
      doc.setTextColor(255, 255, 255);
      doc.text(item.level.toUpperCase(), pageWidth - margin - 13, y + 6.7, {
        align: "center",
      });

      // Location & Signal line
      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.5);
      doc.setTextColor(71, 85, 105);
      doc.text(`Location: ${item.location}  |  Signal: ${item.signal}`, margin + 12, y + 12);

      // Rationale
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(100, 116, 139);
      doc.text(splitRationale, margin + 12, y + 16.5);

      y += boxHeight + 3;
    });

    y += 4;
  }

  // ==========================================
  // 6. SUPPORTING EVIDENCE
  // ==========================================
  if (report.evidence && report.evidence.length > 0) {
    renderSectionHeader("4. Supporting Empirical Evidence");

    report.evidence.forEach((ev) => {
      const splitRelation = doc.splitTextToSize(ev.relation, contentWidth - 8);
      const boxHeight = 10 + splitRelation.length * 3.8;

      checkPageBreak(boxHeight + 2);

      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(226, 232, 240);
      doc.rect(margin, y, contentWidth, boxHeight, "FD");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(8);
      doc.setTextColor(15, 23, 42);
      doc.text(ev.signal, margin + 3, y + 5.5);

      doc.setTextColor(30, 41, 59);
      doc.text(
        `Value: ${ev.value} (Strength: ${ev.strength}/100)`,
        pageWidth - margin - 3,
        y + 5.5,
        { align: "right" },
      );

      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(100, 116, 139);
      doc.text(splitRelation, margin + 3, y + 10);

      y += boxHeight + 2.5;
    });

    y += 4;
  }

  // ==========================================
  // 7. ACTIONABLE RECOMMENDATIONS
  // ==========================================
  if (report.recommendations && report.recommendations.length > 0) {
    renderSectionHeader("5. Policy & Infrastructure Recommendations");

    report.recommendations.forEach((rec) => {
      const splitWhy = doc.splitTextToSize(`Why it matters: ${rec.why}`, contentWidth - 8);
      const splitObj = doc.splitTextToSize(`Safety objective: ${rec.objective}`, contentWidth - 8);
      const boxHeight = 11 + (splitWhy.length + splitObj.length) * 4;

      checkPageBreak(boxHeight + 3);

      doc.setFillColor(248, 250, 252);
      doc.setDrawColor(226, 232, 240);
      doc.rect(margin, y, contentWidth, boxHeight, "FD");

      // Title & Level
      doc.setFont("helvetica", "bold");
      doc.setFontSize(8.5);
      doc.setTextColor(15, 23, 42);
      doc.text(rec.title, margin + 3, y + 6);

      const color = PRIORITY_COLORS[rec.level] || [100, 100, 100];
      doc.setFillColor(color[0], color[1], color[2]);
      doc.rect(pageWidth - margin - 22, y + 2.5, 18, 4.5, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(6.5);
      doc.setTextColor(255, 255, 255);
      doc.text(rec.level.toUpperCase(), pageWidth - margin - 13, y + 5.7, {
        align: "center",
      });

      let subY = y + 11;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.5);
      doc.setTextColor(71, 85, 105);
      doc.text(splitWhy, margin + 3, subY);

      subY += splitWhy.length * 4;
      doc.setTextColor(15, 23, 42);
      doc.text(splitObj, margin + 3, subY);

      y += boxHeight + 3;
    });

    y += 4;
  }

  // ==========================================
  // 8. IMPLEMENTATION PRIORITIES MATRIX
  // ==========================================
  if (report.priorities && report.priorities.length > 0) {
    renderSectionHeader("6. Implementation Priorities Matrix");

    report.priorities.forEach((row) => {
      checkPageBreak(8);

      doc.setFillColor(255, 255, 255);
      doc.setDrawColor(226, 232, 240);
      doc.rect(margin, y, contentWidth, 7, "FD");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.5);
      doc.setTextColor(15, 23, 42);
      doc.text(row.intervention, margin + 3, y + 4.8);

      const badgesText = `Priority: ${row.priority.toUpperCase()}  |  Impact: ${row.impact.toUpperCase()}  |  Effort: ${row.effort.toUpperCase()}`;
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(71, 85, 105);
      doc.text(badgesText, pageWidth - margin - 3, y + 4.8, { align: "right" });

      y += 8.5;
    });

    y += 4;
  }

  // ==========================================
  // 9. MODEL PROVENANCE & GROUNDING METADATA
  // ==========================================
  if (report.provenance) {
    renderSectionHeader("7. Model Provenance & Grounding Verification");

    checkPageBreak(22);

    doc.setFillColor(241, 245, 249);
    doc.setDrawColor(203, 213, 225);
    doc.rect(margin, y, contentWidth, 18, "FD");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(7.5);
    doc.setTextColor(30, 41, 59);
    doc.text("Grounded AI Decision Support Architecture:", margin + 3, y + 5);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(71, 85, 105);
    doc.text(`• Student A Severity Model: ${report.provenance.student_a_model}`, margin + 5, y + 9);
    doc.text(
      `• Student B Hotspot Clustering: ${report.provenance.student_b_hotspots}`,
      margin + 5,
      y + 13,
    );
    doc.text(
      `• Student C GNN Segment Risk: ${report.provenance.student_c_gnn}`,
      margin + 5,
      y + 17,
    );

    const groundedLabel = report.provenance.grounded
      ? "GROUNDED IN EMPIRICAL MODELS (STRICT)"
      : "UNVERIFIED";
    doc.setFont("helvetica", "bold");
    doc.setTextColor(16, 185, 129); // green-500
    doc.text(groundedLabel, pageWidth - margin - 4, y + 11, { align: "right" });

    y += 22;
  }

  // Final pass to draw headers and footers on all pages
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    drawHeaderFooter();
  }

  // Download PDF
  const filename = `ai-infrastructure-report-${filters.region}-${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(filename);
}
