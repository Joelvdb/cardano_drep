import React, { useState, useMemo, useEffect } from 'react';
import axios from 'axios';
import ConfigForm from './components/ConfigForm';
import DelegatorTable from './components/DelegatorTable';
import SimulationChart from './components/SimulationChart';
import DelegationMap from './components/DelegationMap';
import { downloadText, downloadCSV } from './utils/download';

function App() {
  const [initData, setInitData] = useState(null);
  const [config, setConfig] = useState(null);
  const [simulationResults, setSimulationResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [proposalRange, setProposalRange] = useState({ min: 0, max: 0.5 });

  // Playback Loop
  useEffect(() => {
    let interval;
    if (isPlaying && simulationResults) {
      interval = setInterval(() => {
        setCurrentEpoch(prev => {
          const maxEpoch = config.epochs;
          if (prev >= maxEpoch) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 800); // 800ms per epoch
    }
    return () => clearInterval(interval);
  }, [isPlaying, simulationResults, config]);

  const handleInit = (data, usedConfig) => {
    setInitData(data);
    setConfig(usedConfig);
    setSimulationResults(null);
    setCurrentEpoch(0);
    setIsPlaying(false);
  };

  const handleDelegatorUpdate = (updatedDelegator) => {
    setInitData(prev => ({
      ...prev,
      delegators: prev.delegators.map(d => d.id === updatedDelegator.id ? updatedDelegator : d)
    }));
  };

  const handleRunSimulation = () => {
    if (!config) return;
    setLoading(true);
    axios.post('http://localhost:8000/run', config)
      .then(res => {
        setSimulationResults(res.data);
        setLoading(false);
        setCurrentEpoch(0);
        setIsPlaying(true); // Auto-play on run
      })
      .catch(err => {
        console.error("Simulation failed", err);
        setLoading(false);
      });
  };

  const handleExportConfig = () => {
    if (!config) return;
    const textContent = Object.entries(config)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');
    downloadText(textContent, 'simulation_parameters.txt');
  };

  const handleExportFullData = () => {
    if (!simulationResults || !simulationResults.delegators_history) return;

    // Create a lookup for DRep opinions: epoch -> drep_id -> opinion
    const drepOpinions = {};
    if (simulationResults.dreps_history) {
        simulationResults.dreps_history.forEach(d => {
            if (!drepOpinions[d.epoch]) drepOpinions[d.epoch] = {};
            drepOpinions[d.epoch][d.drep_id] = d.opinion;
        });
    }

    // Enrich delegator history
    const enrichedHistory = simulationResults.delegators_history.map(d => ({
        ...d,
        delegated_to_opinion: (d.current_drep_id && drepOpinions[d.epoch] && drepOpinions[d.epoch][d.current_drep_id] !== undefined) 
            ? drepOpinions[d.epoch][d.current_drep_id] 
            : ""
    }));

    downloadCSV(enrichedHistory, 'delegator_history_all_epochs.csv');
  };

  // Determine current data to display based on currentEpoch
  // Epoch 0 = Initial State
  // Epoch 1..N = Simulation History [epoch-1]
  const currentDelegators = useMemo(() => {
    if (currentEpoch === 0 || !simulationResults) {
        return initData ? initData.delegators : [];
    }
    
    // History is 0-indexed, so Epoch 1 corresponds to history[0]
    const historyIndex = currentEpoch - 1;
    if (simulationResults.delegators_history) {
        const history = simulationResults.delegators_history.filter(d => d.epoch === historyIndex);
        if (history.length > 0) {
            return history.map(h => ({ ...h, id: h.delegator_id }));
        }
    }
    return initData ? initData.delegators : [];
  }, [initData, simulationResults, currentEpoch]);

  const currentDreps = useMemo(() => {
    if (currentEpoch === 0 || !simulationResults) {
        return initData ? initData.dreps : [];
    }

    const historyIndex = currentEpoch - 1;
    if (simulationResults.dreps_history) {
        const history = simulationResults.dreps_history.filter(d => d.epoch === historyIndex);
        if (history.length > 0) {
            return history.map(h => ({ ...h, id: h.drep_id }));
        }
    }
    return initData ? initData.dreps : [];
  }, [initData, simulationResults, currentEpoch]);

  return (
    <div className="flex h-screen bg-gray-100 font-sans text-gray-900">
      {/* Sidebar */}
      <aside className="w-80 bg-white border-r border-gray-200 flex flex-col shadow-sm z-10">
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-2xl font-bold text-indigo-600 tracking-tight">DRep Sim</h1>
          <p className="text-xs text-gray-500 mt-1">Governance Simulation Builder</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <ConfigForm onInit={handleInit} />
          
          {initData && (
            <div className="mt-6 p-4 bg-indigo-50 rounded-xl border border-indigo-100">
              <h3 className="font-semibold text-indigo-900 mb-2 flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Simulation Ready
              </h3>
              <div className="text-xs text-indigo-700 space-y-1 mb-4">
                <p>DReps: <span className="font-mono font-bold">{initData.dreps.length}</span></p>
                <p>Delegators: <span className="font-mono font-bold">{initData.delegators.length}</span></p>
              </div>
              <button 
                onClick={handleRunSimulation}
                disabled={loading}
                className={`w-full py-2.5 px-4 rounded-lg text-white font-medium shadow-sm transition-all
                  ${loading 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-md active:transform active:scale-95'
                  }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Running...
                  </span>
                ) : 'Run Simulation'}
              </button>
              
              <button
                onClick={handleExportConfig}
                className="w-full mt-2 py-2 px-4 rounded-lg text-indigo-700 bg-indigo-100 hover:bg-indigo-200 font-medium text-sm transition-colors flex items-center justify-center"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Export Config
              </button>

              {/* Proposal Analysis Controls */}
              <div className="mt-6 pt-4 border-t border-indigo-200">
                  <h3 className="font-semibold text-indigo-900 mb-2 text-sm">Proposal Analysis</h3>
                  <div className="space-y-3">
                      <div>
                          <div className="flex justify-between items-center mb-1">
                              <label className="text-xs font-medium text-indigo-700">Min Opinion</label>
                              <input
                                  type="number"
                                  min="0"
                                  max="1"
                                  step="0.01"
                                  value={proposalRange.min}
                                  onChange={(e) => {
                                      const val = Math.max(0, Math.min(1, parseFloat(e.target.value)));
                                      setProposalRange(prev => ({ ...prev, min: Math.min(val, prev.max) }));
                                  }}
                                  className="w-16 text-xs border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 p-1"
                              />
                          </div>
                          <input 
                              type="range" 
                              min="0" 
                              max="1" 
                              step="0.01"
                              value={proposalRange.min} 
                              onChange={(e) => {
                                  const val = parseFloat(e.target.value);
                                  setProposalRange(prev => ({ ...prev, min: Math.min(val, prev.max) }));
                              }}
                              className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                          />
                      </div>
                      <div>
                          <div className="flex justify-between items-center mb-1">
                              <label className="text-xs font-medium text-indigo-700">Max Opinion</label>
                              <input
                                  type="number"
                                  min="0"
                                  max="1"
                                  step="0.01"
                                  value={proposalRange.max}
                                  onChange={(e) => {
                                      const val = Math.max(0, Math.min(1, parseFloat(e.target.value)));
                                      setProposalRange(prev => ({ ...prev, max: Math.max(val, prev.min) }));
                                  }}
                                  className="w-16 text-xs border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 p-1"
                              />
                          </div>
                          <input 
                              type="range" 
                              min="0" 
                              max="1" 
                              step="0.01"
                              value={proposalRange.max} 
                              onChange={(e) => {
                                  const val = parseFloat(e.target.value);
                                  setProposalRange(prev => ({ ...prev, max: Math.max(val, prev.min) }));
                              }}
                              className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                          />
                      </div>
                  </div>
              </div>

              {/* Playback Controls */}
              {simulationResults && (
                <div className="mt-6 pt-4 border-t border-indigo-200">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-indigo-900">
                            {currentEpoch === 0 ? "Initial State" : `Epoch ${currentEpoch - 1}`} / {config.epochs - 1}
                        </span>
                        <button 
                            onClick={() => setIsPlaying(!isPlaying)}
                            className="p-1 rounded-full hover:bg-indigo-200 text-indigo-700 transition-colors"
                        >
                            {isPlaying ? (
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                            ) : (
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                            )}
                        </button>
                    </div>
                    <input 
                        type="range" 
                        min="0" 
                        max={config.epochs} 
                        value={currentEpoch} 
                        onChange={(e) => {
                            setCurrentEpoch(parseInt(e.target.value));
                            setIsPlaying(false);
                        }}
                        className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                </div>
              )}


            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-100 text-xs text-center text-gray-400">
          v1.0.0 • Ada DRep
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto space-y-8">
          
          {!simulationResults && !initData && (
            <div className="flex flex-col items-center justify-center h-96 text-gray-400 border-2 border-dashed border-gray-300 rounded-2xl">
              <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              <p className="text-lg font-medium">Configure and Initialize to start</p>
            </div>
          )}

          {simulationResults && (
            <section className="animate-fade-in-up">
              <SimulationChart results={simulationResults} proposalRange={proposalRange} />
            </section>
          )}

          {initData && (
            <section className="animate-fade-in-up delay-100 space-y-8">
              <DelegationMap 
                dreps={currentDreps} 
                delegators={currentDelegators} 
                currentEpoch={currentEpoch === 0 ? -1 : currentEpoch - 1}
              />
              
              <DelegatorTable 
                delegators={currentDelegators} 
                dreps={currentDreps}
                onUpdate={handleDelegatorUpdate} 
                onExportFullData={handleExportFullData}
              />
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
