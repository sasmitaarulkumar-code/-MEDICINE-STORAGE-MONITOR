import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, ShieldCheck, Thermometer, Droplets, Sun, 
  DoorClosed, DoorOpen, Zap, AlertTriangle, Play, RefreshCw, 
  FileText, CheckCircle2, Sliders 
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function App() {
  const [units, setUnits] = useState([]);
  const [activeUnitId, setActiveUnitId] = useState(1);
  const [activeUnit, setActiveUnit] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [affectedReport, setAffectedReport] = useState(null);
  const [showAffectedModal, setShowAffectedModal] = useState(false);
  const [demoActive, setDemoActive] = useState(false);

  useEffect(() => {
    fetchUnits();
    fetchAlerts();
    const interval = setInterval(() => {
      fetchUnits();
      fetchAlerts();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeUnitId) {
      fetchHistory(activeUnitId);
      fetchAffected(activeUnitId);
    }
  }, [activeUnitId]);

  const fetchUnits = async () => {
    try {
      const res = await fetch('/api/v1/storage-units');
      if (res.ok) {
        const data = await res.json();
        setUnits(data);
        const current = data.find(u => u.id === activeUnitId) || data[0];
        setActiveUnit(current);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch('/api/v1/alerts/active');
      if (res.ok) setAlerts(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchHistory = async (id) => {
    try {
      const res = await fetch(`/api/v1/telemetry/history/${id}?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.map(d => ({
          time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          temperature: d.temperature,
          humidity: d.humidity
        })));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAffected = async (id) => {
    try {
      const res = await fetch(`/api/v1/inventory/affected/${id}`);
      if (res.ok) setAffectedReport(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const triggerDemo = async (scenarioId) => {
    try {
      setDemoActive(true);
      await fetch('/api/v1/demo/trigger-scenario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId, unit_code: activeUnit ? activeUnit.unit_code : "UNIT-A-FRIDGE" })
      });
      fetchUnits();
      fetchAlerts();
      fetchHistory(activeUnitId);
      fetchAffected(activeUnitId);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white font-bold shadow-md">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight">MED<span className="text-emerald-600">GUARD</span></h1>
            <p className="text-[11px] text-slate-500 font-medium">Intelligent Medicine Storage Monitoring Platform</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span>
            Live IoT Connected
          </span>
          <button 
            onClick={() => setShowAffectedModal(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100 transition"
          >
            Affected Inventory ({affectedReport?.affected_batches_count || 0})
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Storage Tabs */}
        <div className="flex items-center space-x-3">
          {units.map(u => (
            <button
              key={u.id}
              onClick={() => { setActiveUnitId(u.id); setActiveUnit(u); }}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 border ${
                activeUnitId === u.id 
                  ? 'bg-slate-900 text-white border-slate-900' 
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <span>{u.name}</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-black bg-emerald-100 text-emerald-800">
                {u.status}
              </span>
            </button>
          ))}
        </div>

        {/* Metric Cards */}
        {activeUnit && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 flex items-center justify-between">
                <span>Temperature</span>
                <Thermometer className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="mt-2 text-3xl font-black">
                {activeUnit.latest_temperature !== null ? `${activeUnit.latest_temperature}°C` : '--'}
              </div>
              <div className="text-[11px] text-slate-500 mt-1 font-medium">
                Limit: {activeUnit.default_min_temp}°C – {activeUnit.default_max_temp}°C
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 flex items-center justify-between">
                <span>Humidity</span>
                <Droplets className="w-4 h-4 text-blue-500" />
              </div>
              <div className="mt-2 text-3xl font-black">
                {activeUnit.latest_humidity !== null ? `${activeUnit.latest_humidity}%` : '--'}
              </div>
              <div className="text-[11px] text-slate-500 mt-1 font-medium">
                Max Allowed: {activeUnit.default_max_humidity}%
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 flex items-center justify-between">
                <span>Door State</span>
                {activeUnit.door_open_state ? <DoorOpen className="w-4 h-4 text-rose-500" /> : <DoorClosed className="w-4 h-4 text-slate-400" />}
              </div>
              <div className={`mt-2 text-2xl font-black ${activeUnit.door_open_state ? 'text-rose-600 animate-pulse' : 'text-emerald-600'}`}>
                {activeUnit.door_open_state ? 'OPEN' : 'CLOSED'}
              </div>
              <div className="text-[11px] text-slate-500 mt-1 font-medium">
                Light: {activeUnit.latest_light_lux || 0} Lux
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 flex items-center justify-between">
                <span>Operational Risk</span>
                <ShieldAlert className="w-4 h-4 text-amber-500" />
              </div>
              <div className="mt-2 flex items-baseline space-x-2">
                <span className="text-3xl font-black text-slate-900">{Math.round(activeUnit.current_risk_score)}</span>
                <span className="text-xs font-bold text-slate-400">/100</span>
                <span className="text-xs font-black uppercase ml-auto px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  {activeUnit.status}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Charts and Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-4">Temperature Stream (°C)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <XAxis dataKey="time" />
                  <YAxis domain={['auto', 'auto']} />
                  <Tooltip />
                  <Line type="monotone" dataKey="temperature" stroke="#10b981" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 flex items-center justify-between">
              <span>Active Alerts</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-black bg-rose-100 text-rose-800">
                {alerts.length}
              </span>
            </h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">No active alerts detected.</div>
              ) : (
                alerts.map(a => (
                  <div key={a.id} className="p-3 rounded-xl border border-rose-100 bg-rose-50 text-xs space-y-1">
                    <div className="flex justify-between font-black text-rose-800">
                      <span>{a.alert_level}</span>
                      <span>{a.alert_type}</span>
                    </div>
                    <div className="text-slate-800 font-medium">{a.description}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 3-Minute Hackathon Demo Controller */}
        <div className="bg-slate-900 text-white p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <Play className="w-5 h-5 text-amber-400" />
            <h3 className="font-black text-sm uppercase tracking-wider text-amber-400">Hackathon 3-Minute Demo Controller</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <button onClick={() => triggerDemo(1)} className="p-3 rounded-xl bg-slate-800 hover:bg-emerald-600 transition text-left text-xs font-bold">
              1. Normal Baseline
            </button>
            <button onClick={() => triggerDemo(2)} className="p-3 rounded-xl bg-slate-800 hover:bg-amber-600 transition text-left text-xs font-bold">
              2. Trend Warning
            </button>
            <button onClick={() => triggerDemo(3)} className="p-3 rounded-xl bg-slate-800 hover:bg-rose-600 transition text-left text-xs font-bold">
              3. Excursion (>10°C)
            </button>
            <button onClick={() => triggerDemo(4)} className="p-3 rounded-xl bg-slate-800 hover:bg-amber-600 transition text-left text-xs font-bold">
              4. Door Ajar
            </button>
            <button onClick={() => triggerDemo(5)} className="p-3 rounded-xl bg-slate-800 hover:bg-rose-600 transition text-left text-xs font-bold">
              5. Power Failure
            </button>
            <button onClick={() => triggerDemo(6)} className="p-3 rounded-xl bg-slate-800 hover:bg-emerald-600 transition text-left text-xs font-bold">
              6. Recovery
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
