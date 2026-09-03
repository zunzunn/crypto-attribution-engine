import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import TraceView from './components/TraceView';
import EntitiesView from './components/EntitiesView';
import ReportView from './components/ReportView';
import { checkApiHealth } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [targetAddress, setTargetAddress] = useState('0x71C7656EC7ab88b098defB751B7401B5f6d8976F');
  const [apiLive, setApiLive] = useState(false);

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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      
      {/* Top Navbar */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        apiLive={apiLive}
        onQuickSearch={handleQuickSearch}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {currentTab === 'dashboard' && (
          <DashboardView onSelectCase={handleSelectCase} />
        )}

        {currentTab === 'trace' && (
          <TraceView
            targetAddress={targetAddress}
            onAddressChange={(addr) => setTargetAddress(addr)}
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
      <footer className="glass-panel border-t border-slate-900 py-4 px-6 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Crypto Attribution Engine v2.0 &bull; Blockchain Cybercrime Forensic Framework</span>
          <span className="font-mono text-[11px] text-slate-600">SAHYOG Portal Integration Support</span>
        </div>
      </footer>

    </div>
  );
}
