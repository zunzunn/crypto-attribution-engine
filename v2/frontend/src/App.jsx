import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/shell/Sidebar';
import TopBar from './components/shell/TopBar';
import Toast from './components/common/Toast';
import DashboardView from './components/dashboard/DashboardView';
import NewInvestigationView from './components/investigation/NewInvestigationView';
import InvestigationWorkspace from './components/investigation/InvestigationWorkspace';
import InvestigationHistoryView from './components/history/InvestigationHistoryView';
import EntitiesView from './components/EntitiesView';
import ReportPreviewView from './components/reports/ReportPreviewView';
import SystemAboutView from './components/system/SystemAboutView';
import CyberBackground3D from './components/CyberBackground3D';
import { checkApiHealth, fetchAddressTrace } from './services/api';
import {
  getStoredHistory,
  saveInvestigation,
  removeInvestigation,
  clearAllInvestigations
} from './services/historyStorage';
import { isValidEthAddress, shortenAddress, generateCaseId } from './utils/formatters';

const DEFAULT_TARGET = '0x71C7656EC7ab88b098defB751B7401B5f6d8976F';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [targetAddress, setTargetAddress] = useState(DEFAULT_TARGET);
  const [activeCase, setActiveCase] = useState(null);
  const [lastTraceResponse, setLastTraceResponse] = useState(null);
  const [lastTraceIsLive, setLastTraceIsLive] = useState(false);
  const [isExecutingTrace, setIsExecutingTrace] = useState(false);

  // Connectivity
  const [apiLive, setApiLive] = useState(false);
  const [apiLatency, setApiLatency] = useState(null);

  // Case History & Toasts
  const [history, setHistory] = useState(() => getStoredHistory());
  const [toasts, setToasts] = useState([]);

  // Initialize active case from history if present
  useEffect(() => {
    const stored = getStoredHistory();
    if (stored.length > 0 && !activeCase) {
      const latest = stored[0];
      setActiveCase(latest);
      setTargetAddress(latest.target_address);
      if (latest.trace_response) {
        setLastTraceResponse(latest.trace_response);
        setLastTraceIsLive(Boolean(latest.is_live));
      }
    }
  }, [activeCase]);

  // Toast helper
  const notify = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now().toString(36) + Math.random().toString(36).substr(2, 4);
    setToasts((prev) => [...prev, { id, message, type, duration }]);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const checkHealth = useCallback(async () => {
    const res = await checkApiHealth();
    setApiLive(res.isLive);
    setApiLatency(res.latency);
  }, []);

  // Health check on boot
  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // Run a forensic trace
  const executeTrace = useCallback(async (addr, hops = 2, useEtherscan = false) => {
    if (!addr) return;
    setIsExecutingTrace(true);
    setCurrentTab('new'); // Show progress stepper during execution

    try {
      const res = await fetchAddressTrace(addr, hops, useEtherscan);
      if (res.data) {
        const caseId = generateCaseId(addr);
        setLastTraceResponse(res.data);
        setLastTraceIsLive(Boolean(res.isLive));
        setTargetAddress(addr);

        const savedCase = saveInvestigation({
          targetAddress: addr,
          traceResponse: res.data,
          isLive: Boolean(res.isLive),
          maxHops: hops,
          caseId
        });

        if (savedCase) {
          setActiveCase(savedCase);
          setHistory(getStoredHistory());
        }

        notify(`Forensic investigation completed for ${shortenAddress(addr, 6, 4)}`, 'success');
        // Transition to workspace once trace is ready
        setTimeout(() => {
          setIsExecutingTrace(false);
          setCurrentTab('workspace');
        }, 500);
      }
    } catch (err) {
      setIsExecutingTrace(false);
      notify(`Investigation failed: ${err.message}`, 'error', 5000);
    }
  }, [notify]);

  // Handle case selection / restoring
  const handleSelectCase = useCallback((itemOrAddress) => {
    if (typeof itemOrAddress === 'string') {
      const addr = itemOrAddress;
      setTargetAddress(addr);
      // Check if case already in history
      const foundCase = history.find(
        (c) => c.target_address.toLowerCase() === addr.toLowerCase()
      );
      if (foundCase && foundCase.trace_response) {
        setActiveCase(foundCase);
        setLastTraceResponse(foundCase.trace_response);
        setLastTraceIsLive(Boolean(foundCase.is_live));
        setCurrentTab('workspace');
      } else {
        executeTrace(addr, 2, false);
      }
    } else if (itemOrAddress && typeof itemOrAddress === 'object') {
      const c = itemOrAddress;
      setActiveCase(c);
      setTargetAddress(c.target_address);
      if (c.trace_response) {
        setLastTraceResponse(c.trace_response);
        setLastTraceIsLive(Boolean(c.is_live));
        setCurrentTab('workspace');
      } else {
        executeTrace(c.target_address, c.max_hops || 2, c.is_live || false);
      }
    }
  }, [history, executeTrace]);

  // Global search handler
  const handleQuickSearch = useCallback((query) => {
    const clean = query.trim();
    if (!clean) return;

    // 1. Check if matches a Case ID
    const foundCase = history.find(
      (c) => (c.case_id || '').toLowerCase() === clean.toLowerCase()
    );
    if (foundCase) {
      handleSelectCase(foundCase);
      notify(`Loaded case ${foundCase.case_id}`, 'info');
      return;
    }

    // 2. Check if valid Ethereum Address
    if (isValidEthAddress(clean)) {
      handleSelectCase(clean);
      return;
    }

    // 3. Fallback: fuzzy search target addresses
    const fuzzyCase = history.find(
      (c) => (c.target_address || '').toLowerCase().includes(clean.toLowerCase())
    );
    if (fuzzyCase) {
      handleSelectCase(fuzzyCase);
      notify(`Matched case ${fuzzyCase.case_id}`, 'info');
      return;
    }

    notify('No matching case or valid Ethereum address format found.', 'warning');
  }, [history, handleSelectCase, notify]);

  // Delete single case
  const handleDeleteCase = useCallback((caseId) => {
    const updated = removeInvestigation(caseId);
    setHistory(updated);
    if (activeCase?.case_id === caseId) {
      setActiveCase(updated[0] || null);
      if (updated[0]?.trace_response) {
        setLastTraceResponse(updated[0].trace_response);
        setLastTraceIsLive(Boolean(updated[0].is_live));
      } else {
        setLastTraceResponse(null);
      }
    }
    notify(`Deleted case ${caseId}`, 'info');
  }, [activeCase, notify]);

  // Clear all history
  const handleClearAllHistory = useCallback(() => {
    clearAllInvestigations();
    setHistory([]);
    setActiveCase(null);
    setLastTraceResponse(null);
    notify('Cleared all investigation history', 'info');
  }, [notify]);

  return (
    <div className="relative min-h-screen text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200 overflow-x-hidden bg-[#060912]">
      {/* Restrained 3D WebGL Background Particles (Low opacity, non-intrusive) */}
      <div className="fixed inset-0 pointer-events-none opacity-25 z-0">
        <CyberBackground3D />
      </div>

      {/* 1. Collapsible Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        apiLive={apiLive}
        apiLatency={apiLatency}
        activeCase={activeCase}
        onNewInvestigation={() => setCurrentTab('new')}
      />

      {/* 2. Top Bar */}
      <TopBar
        activeCase={activeCase}
        isLive={lastTraceIsLive}
        onSearch={handleQuickSearch}
        onNewInvestigation={() => setCurrentTab('new')}
        collapsed={sidebarCollapsed}
      />

      {/* 3. Main Forensic Workspace Viewport */}
      <main
        className={`relative z-10 flex-1 transition-all duration-300 p-4 sm:p-6 pb-16 max-w-7xl w-full mx-auto ${
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        {currentTab === 'dashboard' && (
          <DashboardView
            lastTraceResponse={lastTraceResponse}
            apiLive={apiLive}
            apiLatency={apiLatency}
            history={history}
            onSelectCase={handleSelectCase}
            onNewInvestigation={() => setCurrentTab('new')}
            onDeleteCase={handleDeleteCase}
          />
        )}

        {currentTab === 'new' && (
          <NewInvestigationView
            onStartInvestigation={(addr, hops, useEtherscan) =>
              executeTrace(addr, hops, useEtherscan)
            }
            isExecuting={isExecutingTrace}
          />
        )}

        {currentTab === 'workspace' && (
          <InvestigationWorkspace
            traceData={lastTraceResponse}
            isLive={lastTraceIsLive}
            targetAddress={targetAddress}
            caseId={activeCase?.case_id}
            onAddressChange={(addr) => executeTrace(addr, 2, lastTraceIsLive)}
            onReTrace={() => executeTrace(targetAddress, lastTraceResponse?.max_hops || 2, lastTraceIsLive)}
            onExportReport={() => setCurrentTab('reports')}
            onNewInvestigation={() => setCurrentTab('new')}
          />
        )}

        {currentTab === 'history' && (
          <InvestigationHistoryView
            history={history}
            onOpenCase={handleSelectCase}
            onDeleteCase={handleDeleteCase}
            onClearAllHistory={handleClearAllHistory}
            onNewInvestigation={() => setCurrentTab('new')}
          />
        )}

        {currentTab === 'entities' && (
          <EntitiesView onSelectEntity={handleSelectCase} />
        )}

        {currentTab === 'reports' && (
          <ReportPreviewView
            targetAddress={targetAddress}
            lastTraceResponse={lastTraceResponse}
            caseId={activeCase?.case_id || 'CASE-2026-LIVE'}
            onNotify={notify}
          />
        )}

        {currentTab === 'system' && (
          <SystemAboutView
            apiLive={apiLive}
            apiLatency={apiLatency}
            onCheckHealth={checkHealth}
          />
        )}
      </main>

      {/* Floating Notifications Toast Container */}
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}