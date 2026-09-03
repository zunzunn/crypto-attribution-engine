import React, { useState, useEffect } from 'react';
import { FileText, Download, Copy, Check, Shield, AlertTriangle } from 'lucide-react';
import { fetchInvestigationReport } from '../services/api';
import { MOCK_TRACE_DATA } from '../services/mockData';

export default function ReportView({ targetAddress }) {
  const [address, setAddress] = useState(targetAddress || '0x71C7656EC7ab88b098defB751B7401B5f6d8976F');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadReport(address);
  }, [address]);

  const loadReport = async (addr) => {
    setLoading(true);
    try {
      const res = await fetchInvestigationReport(addr, MOCK_TRACE_DATA.trace_results, MOCK_TRACE_DATA.patterns);
      if (res.data) {
        setReportData(res.data);
      }
    } catch (err) {
      console.error("Failed to generate report", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (reportData?.markdown_report) {
      navigator.clipboard.writeText(reportData.markdown_report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!reportData?.markdown_report) return;
    const blob = new Blob([reportData.markdown_report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Forensic_Report_${address.substring(0, 10)}.md`;
    a.click();
  };

  const handleDownloadJson = () => {
    if (!reportData?.json_report) return;
    const blob = new Blob([JSON.stringify(reportData.json_report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Forensic_Report_${address.substring(0, 10)}.json`;
    a.click();
  };

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            Forensic Investigation Report Exporter
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Generate official evidence summaries formatted for SAHYOG portal filing and court proceedings.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 font-medium flex items-center gap-1.5 transition"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied' : 'Copy Markdown'}
          </button>
          <button
            onClick={handleDownloadMarkdown}
            className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-xs text-cyan-300 font-bold flex items-center gap-1.5 transition shadow-sm"
          >
            <Download className="w-4 h-4" /> Export .MD
          </button>
          <button
            onClick={handleDownloadJson}
            className="px-3 py-1.5 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-xs text-blue-300 font-bold flex items-center gap-1.5 transition shadow-sm"
          >
            <Download className="w-4 h-4" /> Export .JSON
          </button>
        </div>
      </div>

      {/* Markdown Preview Area */}
      <div className="glass-panel rounded-xl border border-slate-800 p-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <span className="text-xs font-mono text-cyan-400 uppercase font-bold">Report Preview</span>
          <span className="text-xs text-slate-500">Standard Forensic Template v2</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">Generating report preview...</div>
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-xs text-slate-200 bg-slate-950 p-5 rounded-lg border border-slate-800/80 leading-relaxed overflow-x-auto">
            {reportData?.markdown_report || "No report generated."}
          </pre>
        )}
      </div>

    </div>
  );
}
