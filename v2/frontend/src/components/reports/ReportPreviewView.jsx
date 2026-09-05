import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Download, Copy, Check, Printer } from 'lucide-react';
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
  const [previewMode, setPreviewMode] = useState('professional'); // 'professional' | 'markdown' | 'json'

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
    <div className="space-y-4">
      {/* Top Controls Header - minimal */}
      <div className="bg-slate-950/80 border-b border-slate-800/30 p-4 sm:p-6 rounded-t-lg mb-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 no-print">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded bg-slate-800 text-slate-400">
              <FileText className="w-3.5 h-3.5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100 tracking-tight">
                Forensic Investigation Dossier
              </h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Official forensic report with evidentiary provenance and behavioral findings
              </p>
            </div>
          </div>
        </div>

        {/* View Switcher & Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 sm:w-auto justify-end">
          {/* Preview Format Switcher */}
          <div className="flex items-center gap-1 bg-slate-900 rounded-lg p-1">
            <button
              onClick={() => setPreviewMode('professional')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'professional'
                  ? 'text-slate-300 border-b-2 border-cyan-500'
                  : 'text-slate-500'
              }`}
            >
              Professional
            </button>
            <button
              onClick={() => setPreviewMode('markdown')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'markdown'
                  ? 'text-slate-300 border-b-2 border-cyan-500'
                  : 'text-slate-500'
              }`}
            >
              Markdown
            </button>
            <button
              onClick={() => setPreviewMode('json')}
              className={`px-2.5 py-1 rounded font-semibold transition ${
                previewMode === 'json'
                  ? 'text-slate-300 border-b-2 border-cyan-500'
                  : 'text-slate-500'
              }`}
            >
              JSON
            </button>
          </div>

          {/* Export Actions */}
          <div className="flex flex-col sm:flex-row gap-1">
            <button
              onClick={handleCopyMarkdown}
              className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/30 text-xs text-slate-300 font-medium flex items-center gap-1.5 transition"
              title="Copy Markdown"
            >
              {copied ? <Check className="w-2.5 h-2.5 text-emerald-400" /> : <Copy className="w-2.5 h-2.5" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handleDownloadMarkdown}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/30 text-xs text-cyan-300 font-bold flex items-center gap-1.5 transition shadow-sm"
              title="Download .MD file"
            >
              <Download className="w-2.5 h-2.5" />
              <span>.MD</span>
            </button>

            <button
              onClick={handleDownloadJson}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/30 text-xs text-blue-300 font-bold flex items-center gap-1.5 transition shadow-sm"
              title="Download .JSON file"
            >
              <Download className="w-2.5 h-2.5" />
              <span>.JSON</span>
            </button>

            <button
              onClick={handlePrintPdf}
              className="px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800/90 border border-slate-700/30 text-xs text-slate-300 font-bold flex items-center gap-1.5 transition shadow-sm"
              title="Print or Save as PDF"
            >
              <Printer className="w-2.5 h-2.5" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="bg-slate-900 rounded-lg p-6 sm:p-8 text-slate-500 text-[11px] font-mono text-center">
          Generating official investigation dossier...
        </div>
      ) : previewMode === 'markdown' ? (
        /* Markdown Raw View - clean */
        <div className="bg-slate-900 rounded-lg p-6 sm:p-8">
          <pre className="whitespace-pre-wrap font-mono text-[10px] text-slate-300 bg-slate-950 p-4 rounded-xl border border-slate-800/30 leading-relaxed overflow-x-auto">
            {reportData?.markdown_report || 'No markdown report available.'}
          </pre>
        </div>
      ) : previewMode === 'json' ? (
        /* JSON Raw View - clean */
        <div className="bg-slate-900 rounded-lg p-6 sm:p-8">
          <pre className="whitespace-pre-wrap font-mono text-[10px] text-cyan-300 bg-slate-950 p-4 rounded-xl border border-slate-800/30 leading-relaxed overflow-x-auto">
            {JSON.stringify(reportData?.json_report || {}, null, 2)}
          </pre>
        </div>
      ) : (
        /* Professional Forensic Report */
        <div className="bg-slate-900 rounded-2xl overflow-hidden border border-slate-700/30">
          {/* Classification Banner */}
          <div className="border-b border-slate-700/30 px-6 py-2.5 bg-slate-950">
            <span className="text-[9px] font-mono uppercase tracking-wider text-slate-400 block">CONFIDENTIAL</span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-100 mt-1 tracking-tight">
              Cryptocurrency Forensic Attribution Report
            </h1>
            <p className="text-xs text-slate-500 font-mono mt-1">
              Crypto Attribution Engine · SAHYOG Portal Compatible
            </p>
          </div>

          {/* 1. Case Information */}
          <div className="px-6 py-3 sm:p-4 border-b border-slate-700/30">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 font-mono text-xs">
              <div className="p-2 rounded bg-slate-850 border border-slate-700">
                <span className="text-[8px] text-slate-500 uppercase block">Case ID</span>
                <span className="font-semibold text-slate-300 block">{caseMeta.case_id || caseId}</span>
              </div>
              <div className="p-2 rounded bg-slate-850 border border-slate-700">
                <span className="text-[8px] text-slate-500 uppercase block">Generated</span>
                <span className="font-semibold text-slate-300 block">{formatTimestamp(caseMeta.generated_at || new Date().toISOString())}</span>
              </div>
              <div className="p-2 rounded bg-slate-850 border border-slate-700">
                <span className="text-[8px] text-slate-500 uppercase block">Target</span>
                <span className="font-bold text-cyan-300 select-all block">{activeTarget}</span>
              </div>
              <div className="p-2 rounded bg-slate-850 border border-slate-700">
                <span className="text-[8px] text-slate-500 uppercase block">Network</span>
                <span className="text-slate-300 block">{caseMeta.network || 'Ethereum Mainnet'}</span>
              </div>
            </div>
          </div>

          {/* 2. Executive Summary */}
          <div className="px-6 py-3 sm:p-4 border-b border-slate-700/30">
            <h3 className="text-[9px] font-medium uppercase tracking-wider font-semibold text-slate-400 border-b border-slate-700/50 pb-1.5">
              2. Executive Summary
            </h3>
            <div className="pt-2 space-y-2 text-sm">
              <p>
                An automated forensic trace was executed for target address{' '}
                <span className="font-mono text-cyan-300 font-bold">{activeTarget}</span> traversing up to{' '}
                <span className="font-mono text-slate-300 font-bold">{summary.maximum_hop_distance || lastTraceResponse?.max_hops || 2} hops</span> in transaction depth.
              </p>
              <p>
                The investigative engine traversed <span className="font-mono text-slate-300 font-bold">{summary.total_addresses_traced || lastTraceResponse?.trace_results?.discovered_addresses?.length || 1} distinct addresses</span>, identifying <span className="font-mono text-slate-300 font-bold">{summary.attributed_entities_count || attributedEntities.length} verified entities</span>. Highest composite risk evaluated: <span className="font-mono text-rose-400 font-bold">{summary.highest_risk_level || overallRisk.risk_level || 'Low'} ({summary.highest_risk_score || overallRisk.score || 0}/100)</span>.
              </p>
            </div>
          </div>

          {/* 3. Target Wallet Risk Assessment */}
          <div className="px-6 py-3 sm:p-4 border-b border-slate-700/30">
            <h3 className="text-[9px] font-medium uppercase tracking-wider font-semibold text-slate-400 border-b border-slate-700/50 pb-1.5">
              3. Target Wallet Profile & Threat Scoring
            </h3>
            <div className="pt-2 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/30 pb-3">
                <div>
                  <span className="text-[8px] text-slate-500 uppercase block">Target Wallet Address</span>
                  <span className="text-sm font-bold text-slate-300 select-all">{activeTarget}</span>
                </div>
                <RiskBadge
                  level={overallRisk.risk_level || summary.highest_risk_level || 'Low'}
                  score={overallRisk.score || summary.highest_risk_score || 0}
                  size="lg"
                />
              </div>

              {overallRisk.reasons && overallRisk.reasons.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[8px] uppercase font-bold text-slate-400">Risk Factor Attribution Signals:</span>
                  <ul className="list-disc list-inside text-slate-400 space-y-0.5 font-sans text-xs">
                    {overallRisk.reasons.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* 4. Attributed Entities */}
          <div className="px-6 py-3 sm:p-4 border-b border-slate-700/30">
            <h3 className="text-[9px] font-medium uppercase tracking-wider font-semibold text-slate-400 border-b border-slate-700/50 pb-1.5">
              4. Address Attribution Registry Findings
            </h3>
            {attributedEntities.length === 0 ? (
              <div className="p-3 sm:p-4 rounded bg-slate-850 text-sm text-slate-500 font-mono text-center">
                No attributed entities detected within the current trace radius.
              </div>
            ) : (
              <div className="overflow-x-auto rounded bg-slate-850">
                <table className="w-full text-left text-[9px] font-mono text-slate-400">
                  <thead className="bg-slate-950/60 border-b border-slate-700/30 uppercase text-[8px] tracking-wider">
                    <tr>
                      <th className="px-2.5 py-2">Entity</th>
                      <th className="px-2.5 py-2">Type</th>
                      <th className="px-2.5 py-2">Address</th>
                      <th className="px-2.5 py-2">Confidence</th>
                      <th className="px-2.5 py-2">Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/30 bg-slate-950/50">
                    {attributedEntities.map((ent, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/40 transition">
                        <td className="px-2.5 py-2 font-bold text-slate-200">{ent.entity}</td>
                        <td className="px-2.5 py-2">
                          <EntityBadge type={ent.entity_type} size="xs" />
                        </td>
                        <td className="px-2.5 py-2 text-cyan-300">{shortenAddress(ent.address, 8, 6)}</td>
                        <td className="px-2.5 py-2 font-bold text-cyan-300">{Math.round((ent.confidence || 0) * 100)}%</td>
                        <td className="px-2.5 py-2 text-slate-400 text-[9px] truncate max-w-xs" title={ent.evidence}>{ent.evidence || 'Registry match'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 5. Behavioral Findings */}
          <div className="px-6 py-3 sm:p-4 border-b border-slate-700/30">
            <h3 className="text-[9px] font-medium uppercase tracking-wider font-semibold text-slate-400 border-b border-slate-700/50 pb-1.5">
              5. Behavioral Obfuscation Findings
            </h3>
            <div className="space-y-2 text-xs">
              {(patternsDetected.fan_out_events || []).map((evt, idx) => (
                <div key={`fo-${idx}`} className="p-2 rounded bg-slate-850 border border-amber-500/20 mb-1.5">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-bold text-amber-300 font-mono text-[9px]">FAN-OUT STRUCTURING DETECTED</span>
                    <span className="text-[8px] font-mono uppercase text-amber-400">High Risk Pattern</span>
                  </div>
                  <p className="font-sans text-[9px] text-slate-400">{evt.description}</p>
                </div>
              ))}

              {(patternsDetected.rapid_hopping_events || []).map((evt, idx) => (
                <div key={`rh-${idx}`} className="p-2 rounded bg-slate-850 border border-rose-500/20 mb-1.5">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-bold text-rose-300 font-mono text-[9px]">RAPID WALLET HOPPING DETECTED</span>
                    <span className="text-[8px] font-mono uppercase text-rose-400">{evt.time_delta_seconds}s Interval</span>
                  </div>
                  <p className="font-sans text-[9px] text-slate-400">{evt.description}</p>
                </div>
              ))}

              {(patternsDetected.layering_events || []).map((evt, idx) => (
                <div key={`ly-${idx}`} className="p-2 rounded bg-slate-850 border border-cyan-500/20 mb-1.5">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-bold text-cyan-300 font-mono text-[9px]">MULTI-HOP LAYERING DETECTED</span>
                    <span className="text-[8px] font-mono uppercase text-cyan-400">{evt.max_hop_depth || 3}+ Hops</span>
                  </div>
                  <p className="font-sans text-[9px] text-slate-400">{evt.description}</p>
                </div>
              ))}

              {!patternsDetected.summary?.total_patterns_detected && (
                <div className="p-2 sm:p-4 rounded bg-slate-850 text-sm text-slate-500 font-mono text-center">
                  No automated obfuscation anomalies triggered.
                </div>
              )}
            </div>
          </div>

          {/* 6. Legal & Evidentiary Disclaimer */}
          <div className="px-6 py-3 sm:p-4 border-t border-slate-700/30">
            <span className="text-[9px] font-bold uppercase text-slate-300 block">Forensic Disclaimer & Chain of Custody</span>
            <p className="text-[9px] leading-relaxed">
              This intelligence dossier is generated algorithmically through graph traversal, public blockchain ledgers, and curated open-source threat intelligence registries. Attribution scores represent probabilistic evidentiary assessments for investigative guidance and prioritization.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}