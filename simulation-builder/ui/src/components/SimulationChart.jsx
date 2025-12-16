import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { downloadSVGAsPNG } from "../utils/download";

const SimulationChart = ({ results }) => {
  if (!results || !results.dreps_history) return null;

  const data = results;

  const chartData = useMemo(() => {
    const dataMap = {};
    data.dreps_history.forEach((entry) => {
      if (!dataMap[entry.epoch]) {
        dataMap[entry.epoch] = { epoch: entry.epoch };
      }
      dataMap[entry.epoch][entry.drep_id] = entry.opinion;
    });
    return Object.values(dataMap).sort((a, b) => a.epoch - b.epoch);
  }, [data]);

  const chartDataPower = useMemo(() => {
    const dataMap = {};
    data.dreps_history.forEach((entry) => {
      if (!dataMap[entry.epoch]) {
        dataMap[entry.epoch] = { epoch: entry.epoch };
      }
      dataMap[entry.epoch][entry.drep_id] = entry.w_prime;
    });
    return Object.values(dataMap).sort((a, b) => a.epoch - b.epoch);
  }, [data]);

  // Process data for Gini and Median
  const metricsData = useMemo(() => {
    if (!data || !data.dreps_history) return [];

    // Group by epoch
    const epochGroups = {};
    data.dreps_history.forEach((d) => {
      if (!epochGroups[d.epoch]) {
        epochGroups[d.epoch] = {
          epoch: d.epoch,
          gini: d.gini,
          median_power: d.median_power,
          weighted_median_opinion: d.weighted_median_opinion,
        };
      }
    });
    return Object.values(epochGroups).sort((a, b) => a.epoch - b.epoch);
  }, [data]);

  const utilityData = useMemo(() => {
    if (!data || !data.delegators_history || !data.dreps_history) return [];

    // 1. Create a lookup for DRep opinions: epoch -> drep_id -> opinion
    const drepOpinions = {};
    data.dreps_history.forEach((d) => {
      if (!drepOpinions[d.epoch]) drepOpinions[d.epoch] = {};
      drepOpinions[d.epoch][d.drep_id] = d.opinion;
    });

    // 2. Group delegators by epoch and calculate sum of utility
    const epochUtilities = {};
    data.delegators_history.forEach((d) => {
      if (!epochUtilities[d.epoch]) {
        epochUtilities[d.epoch] = { epoch: d.epoch, sum_utility: 0 };
      }
      
      const drepOpinion = drepOpinions[d.epoch]?.[d.current_drep_id];
      if (drepOpinion !== undefined) {
        const utility = 1 - Math.abs(d.opinion - drepOpinion);
        epochUtilities[d.epoch].sum_utility += utility;
      }
    });

    return Object.values(epochUtilities).sort((a, b) => a.epoch - b.epoch);
  }, [data]);

  const handleDownload = (id, filename) => {
    const container = document.getElementById(id);
    // Select the SVG by its role attribute as requested
    // This is a semantic selector that targets the chart specifically
    const svg = container?.querySelector('svg[role="application"]') || container?.querySelector(".recharts-surface");
    if (svg) {
      downloadSVGAsPNG(svg, filename);
    }
  };

  const DownloadButton = ({ onClick }) => (
    <button
      onClick={onClick}
      className="absolute top-2 right-2 p-1.5 bg-white/80 hover:bg-white text-gray-600 hover:text-indigo-600 rounded-lg shadow-sm border border-gray-200 opacity-0 group-hover:opacity-100 transition-all z-10"
      title="Download Chart as PNG"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
        />
      </svg>
    </button>
  );

  return (
    <div className="space-y-6">
      {/* Opinion Chart */}
      <div
        className="bg-white p-4 rounded-xl shadow-sm border border-gray-200"
      >
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          DRep Opinions Over Time
        </h3>
        <div id="chart-opinions" className="h-64 w-full relative group">
          <DownloadButton
            onClick={() => handleDownload("chart-opinions", "drep_opinions.png")}
          />
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis
                dataKey="epoch"
                stroke="#9CA3AF"
                label={{
                  value: "Epoch",
                  position: "insideBottom",
                  offset: -10,
                  fill: "#6B7280",
                  fontSize: 12,
                }}
              />
              <YAxis
                domain={[0, 1]}
                stroke="#9CA3AF"
                label={{
                  value: "Opinion [0-1]",
                  angle: -90,
                  position: "insideLeft",
                  style: { textAnchor: "middle" },
                  offset: 10,
                  fill: "#6B7280",
                  fontSize: 12,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#FFF",
                  borderRadius: "8px",
                  border: "1px solid #E5E7EB",
                }}
                itemStyle={{ fontSize: "12px" }}
              />
              <Legend />
              {Object.keys(chartData[0] || {})
                .filter((k) => k !== "epoch")
                .map((key, index) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={`hsl(${(index * 137.5) % 360}, 70%, 50%)`}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Gini Index Chart */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Gini Index (Inequality)
          </h3>
          <div id="chart-gini" className="h-48 w-full relative group">
            <DownloadButton
              onClick={() => handleDownload("chart-gini", "gini_index.png")}
            />
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={metricsData}
                margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="epoch"
                  stroke="#9CA3AF"
                  label={{
                    value: "Epoch",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#9CA3AF"
                  label={{
                    value: "Gini Coefficient",
                    angle: -90,
                    position: "insideLeft",
                    style: { textAnchor: "middle" },
                    offset: 10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="gini"
                  stroke="#EF4444"
                  strokeWidth={2}
                  dot={false}
                  name="Gini Index"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Median Power Chart */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Median DRep Power</h3>
          <div id="chart-median-power" className="h-48 w-full relative group">
            <DownloadButton
              onClick={() => handleDownload("chart-median-power", "median_power.png")}
            />
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={metricsData}
                margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="epoch"
                  stroke="#9CA3AF"
                  label={{
                    value: "Epoch",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <YAxis
                  stroke="#9CA3AF"
                  label={{
                    value: "Median Power",
                    angle: -90,
                    position: "insideLeft",
                    style: { textAnchor: "middle" },
                    offset: 10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="median_power"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={false}
                  name="Median Power"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Weighted Median Opinion Chart */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 md:col-span-2">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Weighted Median Opinion
          </h3>
          <div id="chart-weighted-median" className="h-48 w-full relative group">
            <DownloadButton
              onClick={() =>
                handleDownload("chart-weighted-median", "weighted_median_opinion.png")
              }
            />
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={metricsData}
                margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="epoch"
                  stroke="#9CA3AF"
                  label={{
                    value: "Epoch",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <YAxis
                  domain={[0, 1]}
                  stroke="#9CA3AF"
                  label={{
                    value: "Weighted Median Opinion",
                    angle: -90,
                    position: "insideLeft",
                    style: { textAnchor: "middle" },
                    offset: 10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="weighted_median_opinion"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={false}
                  name="Weighted Median Opinion"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Power Chart */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 md:col-span-2">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            DRep Power Over Time
          </h3>
          <div id="chart-power" className="h-64 w-full relative group">
            <DownloadButton
              onClick={() => handleDownload("chart-power", "drep_power.png")}
            />
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartDataPower}
                margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="epoch"
                  stroke="#9CA3AF"
                  label={{
                    value: "Epoch",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <YAxis
                  stroke="#9CA3AF"
                  label={{
                    value: "Power (w_prime)",
                    angle: -90,
                    position: "insideLeft",
                    style: { textAnchor: "middle" },
                    offset: 10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFF",
                    borderRadius: "8px",
                    border: "1px solid #E5E7EB",
                  }}
                  itemStyle={{ fontSize: "12px" }}
                />
                <Legend />
                {Object.keys(chartDataPower[0] || {})
                  .filter((k) => k !== "epoch")
                  .map((key, index) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      stroke={`hsl(${(index * 137.5) % 360}, 70%, 50%)`}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sum of Utility Chart */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 md:col-span-2">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Sum of Delegator Utility
          </h3>
          <div id="chart-utility" className="h-64 w-full relative group">
            <DownloadButton
              onClick={() => handleDownload("chart-utility", "sum_utility.png")}
            />
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={utilityData}
                margin={{ top: 10, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="epoch"
                  stroke="#9CA3AF"
                  label={{
                    value: "Epoch",
                    position: "insideBottom",
                    offset: -10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <YAxis
                  stroke="#9CA3AF"
                  label={{
                    value: "Sum of Utility",
                    angle: -90,
                    position: "insideLeft",
                    style: { textAnchor: "middle" },
                    offset: 10,
                    fill: "#6B7280",
                    fontSize: 12,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFF",
                    borderRadius: "8px",
                    border: "1px solid #E5E7EB",
                  }}
                  itemStyle={{ fontSize: "12px" }}
                />
                <Line
                  type="monotone"
                  dataKey="sum_utility"
                  stroke="#2563EB"
                  strokeWidth={2}
                  dot={false}
                  name="Sum Utility"
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(SimulationChart);
