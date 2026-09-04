import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import TraceView from './components/TraceView';
import EntitiesView from './components/EntitiesView';
import ReportView from './components/ReportView';
import CyberBackground3D from './components/CyberBackground3D';
import { checkApiHealth } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [targetAddress, setTargetAddress] = useState('0x71C7656EC7ab88b098defB751B7401B5f6d8976F');
  const [apiLive, setApiLive] = useState(false);
  const [lastTraceResponse, setLastTraceResponse] = useState(null);
  const [lastTraceIsLive, setLastTraceIsLive] = useState(false);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    const res = await checkApiHealth();
    setApiLive(res.isLive);
  };

  const handleSelectCase = (address) => {
    setTargetAddress(address);
    setCurrentTab('trace');
  };

  const handleQuickSearch = (address) => {
    setTargetAddress(address);
    setCurrentTab('trace');
  };

  const handleTraceComplete = useCallback((traceResponse, isLive) => {
    setLastTraceResponse(traceResponse);
    setLastTraceIsLive(isLive);
  }, []);

  return (
    <div className="relative min-h-screen text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200 overflow-x-hidden">

      {/* Realtime 3D Interactive WebGL Cyberspace Background Canvas */}
      <CyberBackground3D />

      {/* Top Navbar Header */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        apiLive={apiLive}
        onQuickSearch={handleQuickSearch}
      />

      {/* Main Forensic Content Area */}
      <main className="relative z-10 flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {currentTab === 'dashboard' && (
          <DashboardView
            onSelectCase={handleSelectCase}
            lastTraceResponse={lastTraceResponse}
            apiLive={lastTraceIsLive}
          />
        )}

        {currentTab === 'trace' && (
          <TraceView
            targetAddress={targetAddress}
            onAddressChange={(addr) => setTargetAddress(addr)}
            onTraceComplete={handleTraceComplete}
          />
        )}

        {currentTab === 'entities' && (
          <EntitiesView onSelectEntity={handleSelectCase} />
        )}

        {currentTab === 'report' && (
          <ReportView targetAddress={targetAddress} />
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 glass-panel border-t border-slate-800/80 py-4 px-6 mt-12 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Crypto Attribution Engine v2.0 &bull; 3D Cyberspace Forensics Framework</span>
          <span className="font-mono text-[11px] text-cyan-400">SAHYOG Portal Integration Support</span>
        </div>
      </footer>

    </div>
  );
}