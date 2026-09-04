import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  Printer
} from 'lucide-react';
import { fetchInvestigationReport } from '../../services/api';
import { shortenAddress, formatTimestamp } from '../../utils/formatters';
import RiskBadge from '../common/RiskBadge';
import EntityBadge from '../common/EntityBadge';

export default function ReportPreviewView({
  targetAddress,
  lastTraceResponse,
  caseId = 'CASE-2026-001',
  onNotify
}) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [previewMode, setPreviewMode] = useState('dossier'); // 'dossier' | 'markdown' | 'json'

  const activeTarget = targetAddress || lastTraceResponse?.target_address || '0x71C7656EC7ab88b098defB751B7401B5f6d8976F';

  const loadReport = useCallback(async () => {
    setLoading(true);
    try {
      const traceResults = lastTraceResponse?.trace_results || {};
      const patterns = lastTraceResponse?.patterns || {};
      const res = await fetchInvestigationReport(activeTarget, traceResults, patterns, caseId);
      if (res.data) {
        setReportData(res.data);
      }
    } catch (err) {
      console.error('Failed to generate report', err);
    } finally {
      setLoading(false);
    }
  }, [activeTarget, lastTraceResponse, caseId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleCopyMarkdown = () => {
    if (reportData?.markdown_report) {
      navigator.clipboard.writeText(reportData.markdown_report);
      setCopied(true);
      if (onNotify) onNotify('Markdown report copied to clipboard', 'success');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!reportData?.markdown_report) return;
    const blob = new Blob([reportData.markdown_report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Forensic_Dossier_${caseId}_${activeTarget.substring(0, 8)}.md`;
    a.click();
    if (onNotify) onNotify('Exported Markdown dossier file', 'success');
  };

  const handleDownloadJson = () => {
    if (!reportData?.json_report) return;
    const blob = new Blob([JSON.stringify(reportData.json_report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Forensic_Dossier_${caseId}_${activeTarget.substring(0, 8)}.json`;
    a.click();
    if (onNotify) onNotify('Exported JSON forensic dataset file', 'success');
  };

  const handlePrintPdf = () => {
    window.print();
  };

  const jsonRep = reportData?.json_report || {};
  const caseMeta = jsonRep.case_metadata || {};
  const summary = jsonRep.investigation_summary || lastTraceResponse?.report_summary || {};
  const attributedEntities = jsonRep.attributed_entities || lastTraceResponse?.trace_results?.discovered_addresses?.filter(n => n.entity !== 'Unknown') || [];
  const patternsDetected = lastTraceResponse?.patterns || {};
  const overallRisk = lastTraceResponse?.trace_results?.overall_risk || {};

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="cyber-panel p-5 sm:p-6 rounded-2xl border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 no-print">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">
                Forensic Investigation Dossier
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Official court-ready forensic report with evidentiary provenance and behavioral findings
              </p>
            </div>
          </div>
        </div>

        {/* View Switcher & Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto justify-end">
          {/* Preview Format Switcher */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setPreviewMode('dossier')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'dossier'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Dossier
            </button>
            <button
              onClick={() => setPreviewMode('markdown')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'markdown'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Markdown
            </button>
            <button
              onClick={() => setPreviewMode('json')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'json'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              JSON
            </button>
          </div>

          {/* Export Actions */}
          <button
            onClick={handleCopyMarkdown}
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs text-slate-300 font-medium flex items-center gap-1.5 transition"
            title="Copy Markdown"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleDownloadMarkdown}
            className="px-3 py-1.5 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-xs text-cyan-300 font-bold flex items-center gap-1.5 transition shadow-sm"
            title="Download .MD file"
          >
            <Download className="w-3.5 h-3.5" />
            <span>.MD</span>
          </button>

          <button
            onClick={handleDownloadJson}
            className="px-3 py-1.5 rounded-lg bg-blue-500/15 hover:bg-blue-500/25 border border-blue-500/30 text-xs text-blue-300 font-bold flex items-center gap-1.5 transition shadow-sm"
            title="Download .JSON file"
          >
            <Download className="w-3.5 h-3.5" />
            <span>.JSON</span>
          </button>

          <button
            onClick={handlePrintPdf}
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-xs text-white font-bold flex items-center gap-1.5 transition shadow-md shadow-cyan-950/40"
            title="Print or Save as PDF"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* Main Dossier Content */}
      {loading ? (
        <div className="cyber-panel p-16 rounded-2xl border border-slate-800 text-center font-mono text-xs text-slate-400">
          Generating official investigation dossier...
        </div>
      ) : previewMode === 'markdown' ? (
        /* Markdown Raw View */
        <div className="cyber-panel rounded-2xl border border-slate-800 p-6">
          <pre className="whitespace-pre-wrap font-mono text-xs text-slate-200 bg-slate-950 p-6 rounded-xl border border-slate-800/80 leading-relaxed overflow-x-auto">
            {reportData?.markdown_report || 'No markdown report available.'}
          </pre>
        </div>
      ) : previewMode === 'json' ? (
        /* JSON Raw View */
        <div className="cyber-panel rounded-2xl border border-slate-800 p-6">
          <pre className="whitespace-pre-wrap font-mono text-xs text-cyan-300 bg-slate-950 p-6 rounded-xl border border-slate-800/80 leading-relaxed overflow-x-auto">
            {JSON.stringify(reportData?.json_report || {}, null, 2)}
          </pre>
        </div>
      ) : (
        /* Professional Law-Enforcement Forensic Dossier View */
        <div className="cyber-panel rounded-2xl border border-slate-800/90 p-6 sm:p-10 space-y-8 font-sans shadow-2xl relative">
          {/* Classification Banner */}
          <div className="text-center border-b border-slate-800 pb-4">
            <span className="text-[11px] font-mono tracking-widest uppercase font-bold text-cyan-400 px-3 py-1 rounded bg-cyan-950/80 border border-cyan-800/60 inline-block">
              CONFIDENTIAL // LAW ENFORCEMENT SENSITIVE // BLOCKCHAIN FORENSICS
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mt-3 tracking-tight">
              Cryptocurrency Forensic Attribution Report
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Crypto Attribution Engine Autonomous Forensics Framework &bull; SAHYOG Portal Compatible
            </p>
          </div>

          {/* 1. Case Information & Metadata */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-cyan-400 border-b border-slate-800 pb-1.5">
              1. Case Information & Target Metadata
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block">Case Identifier</span>
                <span className="font-bold text-white mt-1 block">{caseMeta.case_id || caseId}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block">Generation Timestamp</span>
                <span className="font-semibold text-slate-300 mt-1 block">
                  {formatTimestamp(caseMeta.generated_at || new Date().toISOString())}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block">Target Blockchain</span>
                <span className="font-bold text-white mt-1 block">{caseMeta.network || 'Ethereum Mainnet'}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-500 uppercase block">Assigned Analyst</span>
                <span className="font-bold text-cyan-300 mt-1 block">INV-7409 (Lead Forensics)</span>
              </div>
            </div>
          </div>

          {/* 2. Executive Summary */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-cyan-400 border-b border-slate-800 pb-1.5">
              2. Executive Forensic Summary
            </h3>
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs text-slate-300 leading-relaxed">
              <p>
                An automated forensic trace was executed for target address{' '}
                <span className="font-mono text-cyan-300 font-bold">{activeTarget}</span> traversing up to{' '}
                <span className="font-mono text-white font-bold">{summary.maximum_hop_distance || lastTraceResponse?.max_hops || 2} hops</span> in transaction depth.
              </p>
              <p>
                The investigative engine traversed <span className="font-mono text-white font-bold">{summary.total_addresses_traced || lastTraceResponse?.trace_results?.discovered_addresses?.length || 1} distinct addresses</span>, identifying <span className="font-mono text-white font-bold">{summary.attributed_entities_count || attributedEntities.length} verified entities</span>. Highest composite risk evaluated: <span className="font-mono text-red-400 font-bold">{summary.highest_risk_level || overallRisk.risk_level || 'Low'} ({summary.highest_risk_score || overallRisk.score || 0}/100)</span>.
              </p>
            </div>
          </div>

          {/* 3. Target Wallet Risk Assessment */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-cyan-400 border-b border-slate-800 pb-1.5">
              3. Target Wallet Profile & Threat Scoring
            </h3>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 font-mono text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block">Target Wallet Address</span>
                  <span className="text-sm font-bold text-white select-all">{activeTarget}</span>
                </div>
                <RiskBadge
                  level={overallRisk.risk_level || summary.highest_risk_level || 'Low'}
                  score={overallRisk.score || summary.highest_risk_score || 0}
                  size="lg"
                />
              </div>

              {overallRisk.reasons && overallRisk.reasons.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Risk Factor Attribution Signals:</span>
                  <ul className="list-disc list-inside text-slate-300 space-y-1 font-sans text-xs">
                    {overallRisk.reasons.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* 4. Attributed Entities Registry Findings */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-cyan-400 border-b border-slate-800 pb-1.5">
              4. Address Attribution Registry Findings
            </h3>
            {attributedEntities.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-500 font-mono text-center">
                No attributed entities detected within the current trace radius.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs font-mono text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px]">
                    <tr>
                      <th className="px-3 py-2.5">Entity Label</th>
                      <th className="px-3 py-2.5">Type</th>
                      <th className="px-3 py-2.5">Address</th>
                      <th className="px-3 py-2.5">Confidence</th>
                      <th className="px-3 py-2.5">Evidence Provenance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80 bg-slate-950/60">
                    {attributedEntities.map((ent, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40 transition">
                        <td className="px-3 py-2.5 font-bold text-white">{ent.entity}</td>
                        <td className="px-3 py-2.5">
                          <EntityBadge type={ent.entity_type} size="xs" />
                        </td>
                        <td className="px-3 py-2.5 text-cyan-300">
                          {shortenAddress(ent.address, 8, 6)}
                        </td>
                        <td className="px-3 py-2.5 font-bold text-cyan-400">
                          {Math.round((ent.confidence || 0) * 100)}%
                        </td>
                        <td className="px-3 py-2.5 text-slate-400 text-[11px] truncate max-w-xs font-sans" title={ent.evidence}>
                          {ent.evidence || 'Registry match'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 5. Behavioral Findings */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider font-bold text-cyan-400 border-b border-slate-800 pb-1.5">
              5. Behavioral Obfuscation Findings
            </h3>
            <div className="space-y-2 text-xs">
              {(patternsDetected.fan_out_events || []).map((evt, idx) => (
                <div key={`fo-${idx}`} className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 text-slate-300 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300 font-mono text-[11px]">FAN-OUT STRUCTURING DETECTED</span>
                    <span className="text-[10px] font-mono uppercase text-amber-400">High Risk Pattern</span>
                  </div>
                  <p className="font-sans text-xs text-slate-300">{evt.description}</p>
                </div>
              ))}

              {(patternsDetected.rapid_hopping_events || []).map((evt, idx) => (
                <div key={`rh-${idx}`} className="p-3 rounded-xl bg-red-950/20 border border-red-500/30 text-slate-300 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-red-300 font-mono text-[11px]">RAPID WALLET HOPPING DETECTED</span>
                    <span className="text-[10px] font-mono uppercase text-red-400">{evt.time_delta_seconds}s Interval</span>
                  </div>
                  <p className="font-sans text-xs text-slate-300">{evt.description}</p>
                </div>
              ))}

              {(patternsDetected.layering_events || []).map((evt, idx) => (
                <div key={`ly-${idx}`} className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/30 text-slate-300 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-purple-300 font-mono text-[11px]">MULTI-HOP LAYERING DETECTED</span>
                    <span className="text-[10px] font-mono uppercase text-purple-400">{evt.max_hop_depth}+ Hops</span>
                  </div>
                  <p className="font-sans text-xs text-slate-300">{evt.description}</p>
                </div>
              ))}

              {!patternsDetected.summary?.total_patterns_detected && (
                <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-xs text-slate-500 font-mono text-center">
                  No automated obfuscation anomalies triggered.
                </div>
              )}
            </div>
          </div>

          {/* 6. Legal & Evidentiary Disclaimer */}
          <div className="space-y-2 pt-4 border-t border-slate-800 text-[11px] text-slate-400 font-mono">
            <span className="font-bold uppercase text-slate-300 block">Forensic Disclaimer & Chain of Custody</span>
            <p className="leading-relaxed">
              This intelligence dossier is generated algorithmically through graph traversal, public blockchain ledgers, and curated open-source threat intelligence registries. Attribution scores represent probabilistic evidentiary assessments for law enforcement guidance and investigative prioritization.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
