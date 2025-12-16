import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ConfigForm = ({ onInit }) => {
  const [config, setConfig] = useState({
    n_dreps: 100,
    n_delegators: 2000,
    epochs: 10,
    shift_x: 0.05,
    seed: 421,
    targets: [], // Array of {id: "d1", shift: 0.1}
    opinion_dist: "uniform",
    stake_dist: "uniform",
    delegation_model: "probabilistic",
    custom_logic: ""
  });
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [newTargetId, setNewTargetId] = useState("");
  const [newTargetShift, setNewTargetShift] = useState(0.1);

  useEffect(() => {
    // Fetch default config
    axios.get('http://localhost:8000/config')
      .then(res => {
        // We keep our local targets state separate from default config for now
        // unless default config has targets (which it doesn't currently)
        setConfig(prev => ({
            ...prev,
            ...res.data,
            targets: [] 
        }));
      })
      .catch(err => console.error("Failed to fetch config", err));
  }, []);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }));
  };

  const addTarget = () => {
    if (newTargetId) {
        setConfig(prev => ({
            ...prev,
            targets: [...prev.targets, { id: newTargetId, shift: parseFloat(newTargetShift) }]
        }));
        setNewTargetId("");
        setNewTargetShift(0.1); // Reset shift to default or clear
    }
  };

  const removeTarget = (index) => {
      setConfig(prev => ({
          ...prev,
          targets: prev.targets.filter((_, i) => i !== index)
      }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
        ...config,
        target_drep_id: config.target_drep_id || null,
        target_drep_shift: config.target_drep_shift || null
    };
    
    axios.post('http://localhost:8000/init', payload)
      .then(res => {
        onInit(res.data, payload);
      })
      .catch(err => console.error("Failed to init simulation", err));
  };

  const InputGroup = ({ label, name, type = "number", step }) => (
    <div className="mb-3">
      <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">{label}</label>
      <input 
        type={type} 
        step={step}
        name={name} 
        value={config[name]} 
        onChange={handleChange} 
        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border bg-gray-50" 
      />
    </div>
  );

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-6">
        <h3 className="text-sm font-bold text-gray-900 mb-3">Core Parameters</h3>
        <InputGroup label="N DReps" name="n_dreps" />
        <InputGroup label="N Delegators" name="n_delegators" />
        <InputGroup label="Epochs" name="epochs" />
        <InputGroup label="Global Shift (X)" name="shift_x" step="0.01" />
      </div>

      {/* Multi-Target Configuration */}
      <div className="bg-indigo-50 p-3 rounded-md border border-indigo-100 mb-4">
        <label className="block text-sm font-medium text-indigo-900 mb-2">Targeted DRep Shifts</label>
        
        <div className="flex space-x-2 mb-2">
            <input
                type="text"
                placeholder="DRep ID (e.g. d1)"
                value={newTargetId}
                onChange={(e) => setNewTargetId(e.target.value)}
                className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-1 px-2"
            />
            <input
                type="number"
                step="0.01"
                placeholder="Shift"
                value={newTargetShift}
                onChange={(e) => setNewTargetShift(e.target.value)}
                className="w-20 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-1 px-2"
            />
            <button
                type="button"
                onClick={addTarget}
                className="bg-indigo-600 text-white px-3 py-1 rounded-md text-sm hover:bg-indigo-700"
            >
                Add
            </button>
        </div>

        {/* Target List */}
        <div className="space-y-1 max-h-32 overflow-y-auto">
            {config.targets.map((t, idx) => (
                <div key={idx} className="flex justify-between items-center bg-white p-2 rounded border border-gray-200 text-sm">
                    <span><span className="font-bold">{t.id}</span>: {t.shift > 0 ? '+' : ''}{t.shift}</span>
                    <button 
                        type="button" 
                        onClick={() => removeTarget(idx)}
                        className="text-red-500 hover:text-red-700"
                    >
                        &times;
                    </button>
                </div>
            ))}
            {config.targets.length === 0 && (
                <p className="text-xs text-gray-500 italic">No specific targets defined.</p>
            )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center"
        >
          {showAdvanced ? 'Hide Advanced Parameters' : 'Show Advanced Parameters'}
          <svg className={`w-4 h-4 ml-1 transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {showAdvanced && (
        <div className="space-y-4 pt-4 border-t border-gray-200">
                <InputGroup label="Seed" name="seed" />
                <div className="mt-4">
                    <h4 className="text-xs font-bold text-gray-700 mb-2">Distributions</h4>
                    <div className="mb-3">
                        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Opinion Distribution</label>
                        <select name="opinion_dist" value={config.opinion_dist} onChange={handleChange} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border bg-gray-50">
                            <option value="uniform">Uniform</option>
                            <option value="beta">Beta (2, 2)</option>
                        </select>
                    </div>
                    <div className="mb-3">
                        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Stake Distribution</label>
                        <select name="stake_dist" value={config.stake_dist} onChange={handleChange} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border bg-gray-50">
                            <option value="uniform">Uniform</option>
                            <option value="beta">Beta (2, 5)</option>
                        </select>
                    </div>
                    <div className="mb-3">
                        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Delegation Model</label>
                        <select name="delegation_model" value={config.delegation_model} onChange={handleChange} className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3 border bg-gray-50">
                            <option value="probabilistic">Probabilistic (Default)</option>
                            <option value="responsive">Responsive (Rational)</option>
                            <option value="frozen">Frozen (Static)</option>
                        </select>
                    </div>
                </div>


                
                <div className="mt-4">
                    <h4 className="text-xs font-bold text-gray-700 mb-2">Custom Logic (Python)</h4>
                    <p className="text-xs text-gray-500 mb-2">
                        Overrides shift settings. Available variables: <code>dreps</code>, <code>delegators</code>, <code>epoch</code>, <code>rng</code>.
                    </p>
                    <textarea
                        name="custom_logic"
                        value={config.custom_logic || ""}
                        onChange={handleChange}
                        rows={6}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-xs font-mono p-2 border bg-gray-50"
                        placeholder={`# Example: Move all DReps to center\nfor d in dreps:\n    if d.opinion < 0.5: d.opinion += 0.01\n    else: d.opinion -= 0.01`}
                    />
                </div>
            </div>
        )}


      <button 
        type="submit" 
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
      >
        Initialize World
      </button>
    </form>
  );
};

export default ConfigForm;
