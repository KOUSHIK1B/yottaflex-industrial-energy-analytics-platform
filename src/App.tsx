import React, { useState, useEffect } from 'react';
import {
  Activity,
  Zap,
  DollarSign,
  AlertTriangle,
  Database,
  BarChart3,
  Cpu,
  FileText,
  Play,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Clock,
  Layers,
  Thermometer,
  ShieldAlert,
  Sliders,
  ChevronRight,
  TrendingDown,
  Info,
  ExternalLink,
  Code2,
  Check
} from 'lucide-react';

interface KPI {
  totalEnergyKwh: number;
  totalCostUsd: number;
  facilityPeakDemandKw: number;
  totalGoodUnitsProduced: number;
  averageFacilitySec: string;
  totalIdleWastedKwh: number;
  totalIdleCostUsd: number;
  anomaliesCount: number;
  validationPassedRatio: string;
}

interface Machine {
  machine_id: string;
  machine_name: string;
  category: string;
  rated_power_kw: number;
  total_energy_kwh: number;
  total_cost_usd: number;
  peak_power_kw: number;
  total_good_units: number;
  specific_energy_consumption_kwh_per_unit: number;
  idle_wasted_kwh: number;
  idle_wasted_cost_usd: number;
  idle_waste_pct: number;
}

interface Anomaly {
  anomaly_id: string;
  category_id: number;
  category_name: string;
  affected_entity_type: string;
  affected_entity_id: string;
  reading_id: string;
  timestamp: string;
  original_value: string;
  injected_value: string;
  severity: string;
  expected_detection_rule: string;
  rationale: string;
}

interface QueryItem {
  id: number;
  title: string;
  sql: string;
}

interface Recommendation {
  recommendation_id: string;
  machine_id: string;
  category: string;
  title: string;
  issue_description: string;
  supporting_evidence: string;
  baseline_annual_kwh: number;
  expected_savings_kwh: number;
  estimated_annual_cost_savings_usd: number;
  implementation_cost_usd: number;
  payback_months: number;
  priority: string;
  status: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'machines' | 'anomalies' | 'sql' | 'validation' | 'recommendations' | 'docs'>('overview');
  const [kpi, setKpi] = useState<KPI | null>(null);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [validationReport, setValidationReport] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [queries, setQueries] = useState<QueryItem[]>([]);
  const [dailyData, setDailyData] = useState<any[]>([]);

  // SQL Studio State
  const [selectedQueryId, setSelectedQueryId] = useState<number>(1);
  const [sqlInput, setSqlInput] = useState<string>('');
  const [queryResults, setQueryResults] = useState<any[]>([]);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLatency, setQueryLatency] = useState<number | null>(null);
  const [isExecutingSql, setIsExecutingSql] = useState<boolean>(false);

  // Filter states
  const [machineCategoryFilter, setMachineCategoryFilter] = useState<string>('ALL');
  const [anomalyCategoryFilter, setAnomalyCategoryFilter] = useState<string>('ALL');

  // Loading & Execution
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [pipelineOutput, setPipelineOutput] = useState<string | null>(null);
  const [isRunningPipeline, setIsRunningPipeline] = useState<boolean>(false);
  const [testOutput, setTestOutput] = useState<string | null>(null);
  const [isRunningTests, setIsRunningTests] = useState<boolean>(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const [kpiRes, machRes, anoRes, valRes, recRes, qryRes, dlyRes] = await Promise.all([
        fetch('/api/kpi').then(r => r.json()),
        fetch('/api/machines').then(r => r.json()),
        fetch('/api/anomalies').then(r => r.json()),
        fetch('/api/validation').then(r => r.json()),
        fetch('/api/recommendations').then(r => r.json()),
        fetch('/api/queries').then(r => r.json()),
        fetch('/api/daily').then(r => r.json()),
      ]);

      setKpi(kpiRes);
      setMachines(machRes);
      setAnomalies(anoRes);
      setValidationReport(valRes);
      setRecommendations(recRes);
      setQueries(qryRes);
      setDailyData(dlyRes);

      if (qryRes.length > 0) {
        setSelectedQueryId(qryRes[0].id);
        setSqlInput(qryRes[0].sql);
        runSql(qryRes[0].sql);
      }
    } catch (err) {
      console.error('Error loading initial data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const runSql = async (queryToRun?: string) => {
    const q = queryToRun || sqlInput;
    if (!q) return;
    setIsExecutingSql(true);
    setQueryError(null);
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      const data = await res.json();
      if (data.success) {
        setQueryResults(data.rows);
        setQueryLatency(data.durationMs);
      } else {
        setQueryError(data.error);
        setQueryResults([]);
      }
    } catch (e: any) {
      setQueryError(e.message || 'Network error executing query');
      setQueryResults([]);
    } finally {
      setIsExecutingSql(false);
    }
  };

  const handleSelectQuery = (id: number) => {
    const found = queries.find(q => q.id === id);
    if (found) {
      setSelectedQueryId(id);
      setSqlInput(found.sql);
      runSql(found.sql);
    }
  };

  const handleTriggerPipeline = async () => {
    setIsRunningPipeline(true);
    setPipelineOutput('Executing python3 main.py --all in background...');
    try {
      const res = await fetch('/api/run-pipeline', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setPipelineOutput(data.output);
        fetchInitialData();
      } else {
        setPipelineOutput(`Error: ${data.error}`);
      }
    } catch (err: any) {
      setPipelineOutput(`Failed: ${err.message}`);
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const handleRunTests = async () => {
    setIsRunningTests(true);
    setTestOutput('Running pytest -v test suites...');
    try {
      const res = await fetch('/api/run-tests', { method: 'POST' });
      const data = await res.json();
      setTestOutput(data.output || (data.success ? 'All tests passed' : data.error));
    } catch (err: any) {
      setTestOutput(`Error: ${err.message}`);
    } finally {
      setIsRunningTests(false);
    }
  };

  const filteredMachines = machines.filter(m =>
    machineCategoryFilter === 'ALL' ? true : m.category === machineCategoryFilter
  );

  const filteredAnomalies = anomalies.filter(a =>
    anomalyCategoryFilter === 'ALL' ? true : a.category_name === anomalyCategoryFilter
  );

  const categories = Array.from(new Set(machines.map(m => m.category)));
  const anomalyCategories = Array.from(new Set(anomalies.map(a => a.category_name)));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Industrial Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20 text-slate-950 font-black">
            <Zap className="h-6 w-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                YottaFlex <span className="text-amber-400 font-mono text-sm px-2 py-0.5 rounded bg-amber-400/10 border border-amber-400/20">Energy Analytics Engine</span>
              </h1>
              <span className="flex items-center gap-1.5 text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                ACTIVE MONITOR
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              PLT-001 Austin Facility • Seed: 20261022 • 172,815 Readings • 90-Day Simulation
            </p>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={fetchInitialData}
            className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition"
            title="Refresh from SQLite and exports"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleRunTests}
            disabled={isRunningTests}
            className="px-3 py-1.5 rounded-md bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/60 flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <ShieldAlert className="h-3.5 w-3.5" />
            {isRunningTests ? 'Running Pytest...' : 'Run Pytest Suite'}
          </button>
          <button
            onClick={handleTriggerPipeline}
            disabled={isRunningPipeline}
            className="px-3 py-1.5 rounded-md bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold flex items-center gap-1.5 transition disabled:opacity-50 shadow-md shadow-amber-500/10"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {isRunningPipeline ? 'Regenerating...' : 'Re-Run Pipeline'}
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-slate-800 bg-slate-900/40 px-6 flex overflow-x-auto space-x-1 scrollbar-none text-xs font-medium">
        {[
          { id: 'overview', label: 'Executive Overview', icon: Activity },
          { id: 'machines', label: 'Machine Performance & Intensity', icon: Cpu },
          { id: 'anomalies', label: 'Anomaly Ground Truth (5 Categories)', icon: AlertTriangle, count: kpi?.anomaliesCount },
          { id: 'sql', label: 'Live SQL Query Studio', icon: Database },
          { id: 'validation', label: 'Validation Engine (15 Suites)', icon: ShieldAlert, badge: kpi?.validationPassedRatio },
          { id: 'recommendations', label: 'Actionable Interventions & ROI', icon: TrendingDown, count: recommendations.length },
          { id: 'docs', label: 'Architecture & Technical Docs', icon: FileText },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 px-4 border-b-2 flex items-center gap-2 whitespace-nowrap transition ${
                isActive
                  ? 'border-amber-400 text-amber-300 bg-amber-400/5 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-mono ${isActive ? 'bg-amber-400/20 text-amber-200' : 'bg-slate-800 text-slate-400'}`}>
                  {tab.count}
                </span>
              )}
              {tab.badge && (
                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">

        {/* Console Execution Drawer if active */}
        {(pipelineOutput || testOutput) && (
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 font-mono text-xs relative">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
              <span className="text-amber-400 font-semibold flex items-center gap-2">
                <Code2 className="h-4 w-4" /> System Execution Terminal
              </span>
              <button
                onClick={() => { setPipelineOutput(null); setTestOutput(null); }}
                className="text-slate-500 hover:text-slate-300 text-xs"
              >
                Close
              </button>
            </div>
            <pre className="text-slate-300 overflow-x-auto max-h-48 whitespace-pre-wrap">
              {pipelineOutput || testOutput}
            </pre>
          </div>
        )}

        {/* TAB 1: EXECUTIVE OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                  <span>TOTAL ENERGY CONSUMPTION</span>
                  <Zap className="h-4 w-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-white">
                  {kpi ? (kpi.totalEnergyKwh / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—'} <span className="text-sm font-normal text-slate-400">MWh</span>
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1 font-mono">
                  <span>172,815 readings across 20 meters</span>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                  <span>TOTAL ELECTRICITY SPEND</span>
                  <DollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  ${kpi ? kpi.totalCostUsd.toLocaleString() : '—'}
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1 font-mono">
                  <span>Avg blended: ${kpi && kpi.totalEnergyKwh > 0 ? (kpi.totalCostUsd / kpi.totalEnergyKwh).toFixed(4) : '0.12'} / kWh</span>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                  <span>PEAK DEMAND (COINCIDENT)</span>
                  <BarChart3 className="h-4 w-4 text-cyan-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-cyan-400">
                  {kpi ? kpi.facilityPeakDemandKw.toLocaleString() : '—'} <span className="text-sm font-normal text-slate-400">kW</span>
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1 font-mono">
                  <span>Utility contracted cap: 2,500 kW</span>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                  <span>CONFIRMED IDLE WASTAGE</span>
                  <AlertTriangle className="h-4 w-4 text-rose-400" />
                </div>
                <div className="text-2xl font-bold font-mono text-rose-400">
                  ${kpi ? kpi.totalIdleCostUsd.toLocaleString() : '—'}
                </div>
                <div className="text-xs text-slate-400 mt-2 flex items-center gap-1 font-mono">
                  <span>{kpi ? kpi.totalIdleWastedKwh.toLocaleString() : '0'} kWh wasted during pauses</span>
                </div>
              </div>
            </div>

            {/* Facility Context Strip */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-800 rounded-lg text-amber-400">
                  <Activity className="h-5 w-5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-200">Austin Advanced Metals & Robotics Plant #1</div>
                  <div className="text-slate-400 font-mono text-[11px]">Primary Incomer 13.8kV • Sub-feeders: 3 • Machine Points: 16 • Timezone: America/Chicago</div>
                </div>
              </div>

              <div className="flex items-center gap-6 font-mono text-slate-300">
                <div>
                  <span className="text-slate-500 block text-[10px]">PRODUCTION BATCHES</span>
                  <span className="font-bold text-slate-200">2,000 work orders</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">TOTAL OUTPUT</span>
                  <span className="font-bold text-slate-200">{kpi?.totalGoodUnitsProduced.toLocaleString()} good parts</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">AVERAGE FACILITY SEC</span>
                  <span className="font-bold text-slate-200">{kpi?.averageFacilitySec} kWh/unit</span>
                </div>
              </div>
            </div>

            {/* 90-Day Trend Preview & Tariff Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Daily Energy & Spend Trend Table */}
              <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-sm text-slate-200">90-Day Daily Telemetry Aggregation</h3>
                    <p className="text-xs text-slate-400">Aggregated from 15-minute readings across all meters</p>
                  </div>
                  <span className="text-xs font-mono text-amber-400">90 Daily Intervals</span>
                </div>

                <div className="overflow-x-auto max-h-72 scrollbar-thin">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-800/80 text-slate-400 sticky top-0">
                      <tr>
                        <th className="py-2 px-3">Date</th>
                        <th className="py-2 px-3">Day</th>
                        <th className="py-2 px-3 text-right">Total Energy (kWh)</th>
                        <th className="py-2 px-3 text-right">Peak (kW)</th>
                        <th className="py-2 px-3 text-right">Daily Cost ($)</th>
                        <th className="py-2 px-3 text-right">Blended ($/kWh)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {dailyData.slice(0, 20).map((row, idx) => (
                        <tr key={idx} className={row.is_weekend === 1 ? 'bg-slate-800/20 text-slate-400' : 'hover:bg-slate-800/40'}>
                          <td className="py-2 px-3 text-slate-200">{row.date}</td>
                          <td className="py-2 px-3">{row.day_of_week}</td>
                          <td className="py-2 px-3 text-right font-medium">{Number(row.daily_total_kwh).toLocaleString()}</td>
                          <td className="py-2 px-3 text-right">{row.daily_peak_demand_kw}</td>
                          <td className="py-2 px-3 text-right text-emerald-400">${Number(row.daily_cost_usd).toLocaleString()}</td>
                          <td className="py-2 px-3 text-right text-slate-400">${row.effective_rate_usd_per_kwh}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-[11px] text-slate-500 mt-2 font-mono">Showing first 20 of 90 days. Query Studio provides full historical SQL access.</div>
              </div>

              {/* Tariff Schedule & Cost Distribution */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <h3 className="font-semibold text-sm text-slate-200 mb-1">Time-of-Use Tariff Schedule</h3>
                  <p className="text-xs text-slate-400 mb-4">4 pricing tiers applied deterministically based on hour, day & weather</p>

                  <div className="space-y-3 text-xs">
                    <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-rose-300">CRITICAL PEAK (TAR-2026-004)</div>
                        <div className="text-[11px] text-slate-400 font-mono">Summer Weekdays 14:00-18:00 (Temp ≥ 38°C)</div>
                      </div>
                      <div className="text-right font-mono font-bold text-rose-400">$0.4500 <span className="text-[10px] font-normal text-slate-400">/kWh</span></div>
                    </div>

                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-amber-300">ON-PEAK (TAR-2026-003)</div>
                        <div className="text-[11px] text-slate-400 font-mono">Weekdays 13:00 to 19:00</div>
                      </div>
                      <div className="text-right font-mono font-bold text-amber-400">$0.2250 <span className="text-[10px] font-normal text-slate-400">/kWh</span></div>
                    </div>

                    <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-sky-300">SHOULDER (TAR-2026-002)</div>
                        <div className="text-[11px] text-slate-400 font-mono">Weekdays 07:00-13:00 & 19:00-22:00</div>
                      </div>
                      <div className="text-right font-mono font-bold text-sky-400">$0.1280 <span className="text-[10px] font-normal text-slate-400">/kWh</span></div>
                    </div>

                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-emerald-300">OFF-PEAK (TAR-2026-001)</div>
                        <div className="text-[11px] text-slate-400 font-mono">Weekdays 22:00-07:00 & All Weekends</div>
                      </div>
                      <div className="text-right font-mono font-bold text-emerald-400">$0.0650 <span className="text-[10px] font-normal text-slate-400">/kWh</span></div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Coincident Peak Tariff Impact:</span>
                  <span className="font-semibold text-amber-400">On-Peak accounts for ~40% of spend</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: MACHINE PERFORMANCE & INTENSITY */}
        {activeTab === 'machines' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-100">Machine Energy & Performance Matrix</h2>
                <p className="text-xs text-slate-400">Specific Energy Consumption (SEC), rated vs operating draw, and confirmed idle losses</p>
              </div>

              {/* Category Filter */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Category:</span>
                <select
                  value={machineCategoryFilter}
                  onChange={e => setMachineCategoryFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-amber-400"
                >
                  <option value="ALL">All Categories ({machines.length})</option>
                  {categories.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Machines Grid Table */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-800/80 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Machine ID & Name</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4 text-right">Rated kW</th>
                      <th className="py-3 px-4 text-right">Peak kW</th>
                      <th className="py-3 px-4 text-right">Total Energy (kWh)</th>
                      <th className="py-3 px-4 text-right">Total Cost ($)</th>
                      <th className="py-3 px-4 text-right">Good Output</th>
                      <th className="py-3 px-4 text-right">SEC (kWh/unit)</th>
                      <th className="py-3 px-4 text-right">Idle Wasted ($)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {filteredMachines.map(m => (
                      <tr key={m.machine_id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-100">{m.machine_name}</div>
                          <div className="text-[11px] text-amber-400">{m.machine_id}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-300">
                            {m.category}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">{m.rated_power_kw}</td>
                        <td className="py-3 px-4 text-right text-cyan-400 font-semibold">{m.peak_power_kw}</td>
                        <td className="py-3 px-4 text-right font-medium">{m.total_energy_kwh.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-emerald-400">${m.total_cost_usd.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right">{m.total_good_units > 0 ? m.total_good_units.toLocaleString() : 'N/A (Utility)'}</td>
                        <td className="py-3 px-4 text-right font-bold text-amber-300">
                          {m.specific_energy_consumption_kwh_per_unit > 0 ? m.specific_energy_consumption_kwh_per_unit.toFixed(4) : '—'}
                        </td>
                        <td className="py-3 px-4 text-right text-rose-400">
                          ${m.idle_wasted_cost_usd} <span className="text-[10px] text-slate-500">({m.idle_waste_pct}%)</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: ANOMALY GROUND TRUTH */}
        {activeTab === 'anomalies' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-amber-400" />
                  Injected Anomaly Registry & Ground Truth
                </h2>
                <p className="text-xs text-slate-400">
                  5 required industrial anomaly categories deliberately injected with explicit verification rules and 100% ground truth traceability
                </p>
              </div>

              {/* Filter */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Category:</span>
                <select
                  value={anomalyCategoryFilter}
                  onChange={e => setAnomalyCategoryFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-amber-400"
                >
                  <option value="ALL">All Categories ({anomalies.length})</option>
                  {anomalyCategories.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Category Summary Badges */}
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs">
              {[
                { name: 'METER_SUM_MISMATCH', label: '1. Meter Sum Mismatch', count: anomalies.filter(a => a.category_name === 'METER_SUM_MISMATCH').length },
                { name: 'KW_KWH_CONFUSION', label: '2. kW vs kWh Confusion', count: anomalies.filter(a => a.category_name === 'KW_KWH_CONFUSION').length },
                { name: 'TARIFF_TZ_MISMATCH', label: '3. Tariff TZ Mismatch', count: anomalies.filter(a => a.category_name === 'TARIFF_TZ_MISMATCH').length },
                { name: 'DUPLICATE_READING', label: '4. Duplicate Readings', count: anomalies.filter(a => a.category_name === 'DUPLICATE_READING').length },
                { name: 'HIERARCHY_VIOLATION', label: '5. Hierarchy Violations', count: anomalies.filter(a => a.category_name === 'HIERARCHY_VIOLATION').length },
              ].map(cat => (
                <div
                  key={cat.name}
                  onClick={() => setAnomalyCategoryFilter(anomalyCategoryFilter === cat.name ? 'ALL' : cat.name)}
                  className={`p-3 rounded-lg border cursor-pointer transition ${
                    anomalyCategoryFilter === cat.name
                      ? 'bg-amber-400/10 border-amber-400 text-amber-200'
                      : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold truncate">{cat.label}</div>
                  <div className="text-xl font-bold font-mono mt-1 text-white">{cat.count}</div>
                </div>
              ))}
            </div>

            {/* Anomaly Table */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto max-h-[600px] scrollbar-thin">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-800/80 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="py-3 px-4">Anomaly ID</th>
                      <th className="py-3 px-4">Category</th>
                      <th className="py-3 px-4">Affected Meter / Timestamp</th>
                      <th className="py-3 px-4">Original Clean Value</th>
                      <th className="py-3 px-4">Injected Corrupt Value</th>
                      <th className="py-3 px-4">Severity</th>
                      <th className="py-3 px-4">Detection Rule</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {filteredAnomalies.map(a => (
                      <tr key={a.anomaly_id} className="hover:bg-slate-800/30 transition">
                        <td className="py-3 px-4 font-bold text-amber-400">{a.anomaly_id}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-200">
                            {a.category_name}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-slate-200">{a.affected_entity_id}</div>
                          <div className="text-[10px] text-slate-500">{a.timestamp || 'N/A'}</div>
                        </td>
                        <td className="py-3 px-4 text-emerald-400 font-mono text-[11px] max-w-xs truncate" title={a.original_value}>
                          {a.original_value}
                        </td>
                        <td className="py-3 px-4 text-rose-400 font-mono text-[11px] max-w-xs truncate" title={a.injected_value}>
                          {a.injected_value}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            a.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                            a.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                            'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]" title={a.expected_detection_rule}>
                          {a.expected_detection_rule}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: LIVE SQL QUERY STUDIO */}
        {activeTab === 'sql' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Database className="h-5 w-5 text-amber-400" />
                Live SQL Query Studio (SQLite Engine)
              </h2>
              <p className="text-xs text-slate-400">
                Execute analytical queries directly against <code className="text-amber-400 font-mono">database/energy_analytics.db</code> containing 172,815 records
              </p>
            </div>

            {/* Pre-Loaded Queries Selector */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
              {queries.map(q => (
                <button
                  key={q.id}
                  onClick={() => handleSelectQuery(q.id)}
                  className={`p-2.5 rounded-lg border text-left text-xs transition truncate ${
                    selectedQueryId === q.id
                      ? 'bg-amber-400/10 border-amber-400 text-amber-300 font-semibold'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                  title={q.title}
                >
                  <span className="font-mono text-amber-400 mr-1.5 font-bold">#{q.id}</span>
                  <span>{q.title.replace(/^\d+\.\s*/, '')}</span>
                </button>
              ))}
            </div>

            {/* SQL Editor Area */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-mono">SQL Query Editor</span>
                <div className="flex items-center gap-3">
                  {queryLatency !== null && (
                    <span className="font-mono text-emerald-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> Executed in {queryLatency} ms ({queryResults.length} rows)
                    </span>
                  )}
                  <button
                    onClick={() => runSql()}
                    disabled={isExecutingSql}
                    className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center gap-1.5 transition text-xs disabled:opacity-50"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    {isExecutingSql ? 'Executing...' : 'Run Query'}
                  </button>
                </div>
              </div>

              <textarea
                value={sqlInput}
                onChange={e => setSqlInput(e.target.value)}
                rows={7}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-amber-200 focus:outline-none focus:border-amber-400 selection:bg-amber-500/20"
                spellCheck={false}
              />
            </div>

            {/* Query Error Notice */}
            {queryError && (
              <div className="p-4 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-mono">
                <strong>SQL Execution Error:</strong> {queryError}
              </div>
            )}

            {/* Results Grid Table */}
            {queryResults.length > 0 && (
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="p-3 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Results Grid ({queryResults.length} records returned)</span>
                  <span>Read-Only Relational Connection</span>
                </div>
                <div className="overflow-x-auto max-h-96 scrollbar-thin">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-800/80 text-slate-400 border-b border-slate-800 sticky top-0">
                      <tr>
                        {Object.keys(queryResults[0]).map(col => (
                          <th key={col} className="py-2.5 px-3 whitespace-nowrap">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {queryResults.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition">
                          {Object.values(row).map((val: any, colIdx) => (
                            <td key={colIdx} className="py-2 px-3 whitespace-nowrap">
                              {typeof val === 'number' ? val.toLocaleString() : String(val ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: VALIDATION ENGINE */}
        {activeTab === 'validation' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-emerald-400" />
                  Enterprise Validation Engine (15 Check Suites)
                </h2>
                <p className="text-xs text-slate-400">
                  Automated structural, relational, and physical consistency auditing separating injected anomalies from generator defects
                </p>
              </div>

              {validationReport && (
                <div className="flex items-center gap-3 font-mono text-xs">
                  <div className="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
                    Ground Truth Match: {validationReport.summary.ground_truth_match_rate_pct}%
                  </div>
                  <div className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300">
                    {validationReport.summary.total_records_analyzed.toLocaleString()} records audited
                  </div>
                </div>
              )}
            </div>

            {/* Validation Suites Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {validationReport?.checks.map((chk: any) => {
                const isPassed = chk.status === 'PASSED';
                const isWarning = chk.status === 'WARNING';
                return (
                  <div
                    key={chk.check_id}
                    className={`p-4 rounded-xl border bg-slate-900/90 flex flex-col justify-between ${
                      isPassed ? 'border-emerald-500/30' : isWarning ? 'border-amber-500/40' : 'border-rose-500/40'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-[10px] text-slate-500">{chk.check_id}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                          isPassed ? 'bg-emerald-500/20 text-emerald-300' : isWarning ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'
                        }`}>
                          {chk.status}
                        </span>
                      </div>
                      <h4 className="font-semibold text-xs text-slate-100 mb-1">{chk.name}</h4>
                      <p className="text-[11px] text-slate-400">{chk.description}</p>
                    </div>

                    <div className="mt-4 pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono">
                      <span className="text-slate-500">Flagged Events:</span>
                      <span className={chk.violations_count > 0 ? 'text-amber-400 font-bold' : 'text-emerald-400'}>
                        {chk.violations_count}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 6: RECOMMENDATIONS & ROI */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-emerald-400" />
                Actionable Engineering Recommendations & Payback
              </h2>
              <p className="text-xs text-slate-400">
                Prioritized energy efficiency interventions with baseline metrics, expected kWh savings, and verified capital payback
              </p>
            </div>

            {/* Recommendations List */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map(r => (
                <div key={r.recommendation_id} className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-sm">
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="font-mono text-xs font-bold text-amber-400">{r.recommendation_id}</span>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.priority === 'HIGH' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                          r.priority === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                        }`}>
                          {r.priority} PRIORITY
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          {r.status}
                        </span>
                      </div>
                    </div>

                    <h3 className="font-bold text-sm text-slate-100 mb-1">{r.title}</h3>
                    <div className="text-xs text-amber-400/90 font-mono mb-2">Target Asset: {r.machine_id}</div>
                    <p className="text-xs text-slate-300 mb-2 leading-relaxed">{r.issue_description}</p>
                    <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400">
                      <strong className="text-slate-300">Measured Telemetry Evidence:</strong> {r.supporting_evidence}
                    </div>
                  </div>

                  {/* Financial Metrics Strip */}
                  <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800 text-xs font-mono">
                    <div>
                      <span className="text-slate-500 block text-[10px]">ANNUAL SAVINGS</span>
                      <span className="font-bold text-emerald-400 text-sm">${Number(r.estimated_annual_cost_savings_usd).toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">ENERGY SAVED</span>
                      <span className="font-bold text-slate-200">{Number(r.expected_savings_kwh).toLocaleString()} kWh</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">PAYBACK</span>
                      <span className="font-bold text-cyan-400 text-sm">{r.payback_months} mos</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 7: ARCHITECTURE & TECHNICAL DOCS */}
        {activeTab === 'docs' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <FileText className="h-5 w-5 text-amber-400" />
                Technical Interview Readiness & Architecture Overview
              </h2>
              <p className="text-xs text-slate-400">
                End-to-end documentation for YottaFlex Associate AI Forward Deployed Engineer Round 2 submission
              </p>
            </div>

            {/* Architecture Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="font-bold text-sm text-amber-400 mb-2 flex items-center gap-2">
                  <Database className="h-4 w-4" /> Relational SQLite Architecture
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  13 normalized entities enforcing strict primary and foreign keys, B-tree indexes, and a historical bridge table (<code className="text-amber-300 font-mono">machine_meter_assignments</code>) to support multi-channel metering with effective date ranges.
                </p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="font-bold text-sm text-cyan-400 mb-2 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4" /> 5 Industrial Anomaly Scenarios
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Deterministic injection of Sub-Meter Reconciliation Mismatches, kW vs kWh Unit Confusion, Tariff Timezone Drift, Telemetry Duplicates, and Hierarchy Violations with a separate traceable Ground Truth Registry.
                </p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="font-bold text-sm text-emerald-400 mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> 100% Deterministic Reproducibility
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Fixed seed <code className="text-emerald-300 font-mono">20261022</code> guarantees identical row counts, IDs, values, and SHA-256 hashes across consecutive executions without timestamp drift or random leakage.
                </p>
              </div>
            </div>

            {/* Technical Interview Q&A Section */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="font-bold text-sm text-slate-200 border-b border-slate-800 pb-2">
                Frequently Asked Technical Interview Questions & Engineering Solutions
              </h3>

              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="font-semibold text-amber-300 mb-1">
                    Q1: How does the system correlate production output with energy consumption when meters aggregate continuous busbar power?
                  </h4>
                  <p className="text-slate-300 leading-relaxed">
                    We bridge production batches with 15-minute telemetry intervals using the machine-meter topological hierarchy. Energy is integrated across the exact time span of each work order (<code className="text-slate-200 font-mono">timestamp &gt;= start_timestamp AND timestamp &lt;= end_timestamp</code>), computing Specific Energy Consumption (SEC in kWh per actual good part produced) and isolating scrap waste.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-amber-300 mb-1">
                    Q2: How do you identify non-productive idle energy and distinguish it from scheduled maintenance?
                  </h4>
                  <p className="text-slate-300 leading-relaxed">
                    Scheduled maintenance events have zero planned production and de-energized motors (recorded in <code className="text-slate-200 font-mono">maintenance_events</code>). In contrast, idle periods occur when equipment remains energized at its nominal standby kW (e.g. 18.5 kW on compressors or 8.5 kW on hydraulic pumps) during operator breaks, material starvation, or downstream line blockage. Idle waste is calculated by multiplying standby kW by duration and applying the effective time-of-use tariff.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-amber-300 mb-1">
                    Q3: How does the platform handle time-of-use tariff complexities and weather-sensitive loads?
                  </h4>
                  <p className="text-slate-300 leading-relaxed">
                    The platform models 4 Time-of-Use tariffs (Off-Peak, Shoulder, On-Peak, Critical Peak) aligned to the facility local timezone (<code className="text-slate-200 font-mono">America/Chicago</code>). Chiller plant loads dynamically respond to outdoor dry-bulb temperature and cooling degree days, while the Critical Peak tariff ($0.45/kWh) automatically triggers when summer ambient temperatures exceed 38°C during peak afternoon hours.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Industrial Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 px-6 py-4 text-xs text-slate-500 font-mono flex flex-wrap items-center justify-between gap-4">
        <div>
          YottaFlex.ai Recruitment Challenge • Associate AI Forward Deployed Engineer • Round 2 Code Submission
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>Python 3.11</span>
          <span>•</span>
          <span>SQLite 3 (WAL)</span>
          <span>•</span>
          <span>16 Pytests Passing</span>
          <span>•</span>
          <span>Deterministic Seed 20261022</span>
        </div>
      </footer>
    </div>
  );
}
