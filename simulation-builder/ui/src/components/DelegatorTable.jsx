import React, { useState, useMemo } from 'react';
import axios from 'axios';
import { downloadCSV } from '../utils/download';

const DelegatorTable = ({ delegators, dreps = [], onUpdate, onExportFullData }) => {
  const drepMap = useMemo(() => {
    return new Map(dreps.map(d => [d.id, d]));
  }, [dreps]);

  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const handleEdit = (delegator) => {
    setEditingId(delegator.id);
    setEditForm(delegator);
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditForm(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };

  const handleSave = () => {
    axios.post('http://localhost:8000/update-delegator', editForm)
      .then(res => {
        onUpdate(editForm);
        setEditingId(null);
      })
      .catch(err => console.error("Failed to update delegator", err));
  };

  const handleExportCSV = () => {
    if (onExportFullData) {
        onExportFullData();
    } else {
        downloadCSV(delegators, 'delegator_registry_current.csv');
    }
  };



  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Pagination Logic
  const totalPages = Math.ceil(delegators.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentData = delegators.slice(startIndex, endIndex);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
        setCurrentPage(newPage);
    }
  };

  return (
    <div className="bg-white shadow-sm border border-gray-200 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
        <div>
            <h2 className="text-lg font-bold text-gray-900">Delegator Registry</h2>
            <p className="text-sm text-gray-500">Manage individual delegator parameters</p>
        </div>
        <div className="flex items-center space-x-2">
            <button 
                onClick={handleExportCSV}
                className="mr-2 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-md border border-indigo-200 transition-colors flex items-center"
            >
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Export CSV
            </button>
            <span className="text-xs text-gray-500">Rows per page:</span>
            <select 
                value={pageSize} 
                onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                }}
                className="text-xs border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
            </select>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Opinion</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stake</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stickiness (s)</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delegated To</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delegated To Opinion</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Responsive</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delta U</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">State</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentData.map(d => (
              <tr key={d.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{d.id}</td>
                
                {editingId === d.id ? (
                  <>
                    <td className="px-6 py-4 whitespace-nowrap">
                        <input type="number" step="0.01" name="opinion" value={editForm.opinion} onChange={handleChange} className="w-24 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-1 border" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                        <input type="number" step="0.01" name="stake" value={editForm.stake} onChange={handleChange} className="w-24 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-1 border" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                        <input type="number" step="0.01" name="s" value={editForm.s} onChange={handleChange} className="w-24 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-1 border" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">-</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">-</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">-</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">-</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">-</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button onClick={handleSave} className="text-green-600 hover:text-green-900 font-bold">Save</button>
                      <button onClick={handleCancel} className="text-gray-500 hover:text-gray-700">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            {d.opinion.toFixed(3)}
                        </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{d.stake.toFixed(3)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{d.s.toFixed(3)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">{d.current_drep_id || "-"}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {d.current_drep_id && drepMap.get(d.current_drep_id) ? (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-indigo-50 text-indigo-700">
                                {drepMap.get(d.current_drep_id).opinion.toFixed(3)}
                            </span>
                        ) : "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">{d.last_responsive_id || "-"}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{d.last_delta_u ? d.last_delta_u.toFixed(4) : "0.0000"}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${d.is_frozen ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                            {d.is_frozen ? 'Frozen' : 'Active'}
                        </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button onClick={() => handleEdit(d)} className="text-indigo-600 hover:text-indigo-900 transition-colors">Edit</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination Footer */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="text-xs text-gray-500">
            Showing <span className="font-medium">{startIndex + 1}</span> to <span className="font-medium">{Math.min(endIndex, delegators.length)}</span> of <span className="font-medium">{delegators.length}</span> results
        </div>
        <div className="flex items-center space-x-2">
            <button 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`px-3 py-1 rounded-md text-xs font-medium border ${currentPage === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
                Previous
            </button>
            <span className="text-xs text-gray-600">
                Page {currentPage} of {totalPages}
            </span>
            <button 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 rounded-md text-xs font-medium border ${currentPage === totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
            >
                Next
            </button>
        </div>
      </div>
    </div>
  );
};

export default DelegatorTable;
