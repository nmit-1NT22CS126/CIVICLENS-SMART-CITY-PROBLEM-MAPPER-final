// src/utils/reportStorage.js
const STORAGE_KEY = "civiclens_reports_v1";

export function loadReports() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error("Failed to parse reports:", e);
    return [];
  }
}

export function saveReports(reports) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
  } catch (e) {
    console.error("Failed to save reports:", e);
  }
}

export function addReport(report) {
  const reports = loadReports();
  reports.unshift(report); // newest first
  saveReports(reports);
}
