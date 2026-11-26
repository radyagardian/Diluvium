import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Waves,
  LogOut,
  RefreshCw,
  ShieldAlert,
  Send,
  Terminal,
  Lock,
  Activity,
} from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const SIAGA_STYLES = {
  'Siaga 1': 'border-red-500/50 bg-red-500/15 text-red-400',
  'Siaga 2': 'border-orange-500/50 bg-orange-500/15 text-orange-400',
  'Siaga 3': 'border-amber-500/50 bg-amber-500/15 text-amber-400',
  'Siaga 4': 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
};

function buildHydroPath(values, minVal, maxVal, width = 520, height = 160, pad = 14) {
  if (!values || values.length === 0) return '';
  const range = Math.max(maxVal - minVal, 1);
  const stepX = values.length > 1 ? (width - pad * 2) / (values.length - 1) : 0;

  return values
    .map((val, idx) => {
      const x = pad + idx * stepX;
      const norm = Math.min(Math.max((val - minVal) / range, 0), 1);
      const y = height - pad - norm * (height - pad * 2);
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

export default function AdminDashboard() {
  const [token, setToken] = useState(() => localStorage.getItem('supabase_token') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  const [telemetry, setTelemetry] = useState(null);
  const [selectedArea, setSelectedArea] = useState('auto');
  const [actionLoading, setActionLoading] = useState(false);
  const [logs, setLogs] = useState([
    { time: new Date().toLocaleTimeString(), text: 'Console ready. Waiting for telemetry...', isError: false },
  ]);

  const appendLog = useCallback((text, isError = false) => {
    setLogs((prev) => [
      { time: new Date().toLocaleTimeString(), text, isError },
      ...prev.slice(0, 14),
    ]);
  }, []);

  const handleLogout = useCallback(
    (reason) => {
      localStorage.removeItem('supabase_token');
      setToken('');
      setTelemetry(null);
      if (reason) appendLog(reason, true);
    },
    [appendLog]
  );

  const fetchTelemetry = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/admin/telemetry?area_id=${encodeURIComponent(selectedArea)}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (res.status === 401) {
        handleLogout('Session expired or unauthorized. Please sign in again.');
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      setTelemetry(data);
    } catch (err) {
      appendLog(`Telemetry poll failed: ${err.message}`, true);
    }
  }, [token, selectedArea, handleLogout, appendLog]);

  useEffect(() => {
    if (!token) return;
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(interval);
  }, [token, fetchTelemetry]);

  async function handleLogin(e) {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        setAuthError('Invalid administrator credentials.');
        return;
      }

      const data = await res.json();
      localStorage.setItem('supabase_token', data.access_token);
      setToken(data.access_token);
      setPassword('');
      appendLog('Administrator authenticated via Supabase Auth.');
    } catch {
      setAuthError('Cannot reach backend API. Verify server is running.');
    } finally {
      setAuthLoading(false);
    }
  }

  async function triggerTestAlert() {
    setActionLoading(true);
    appendLog('Dispatching diagnostic test alert (BMKG refresh + calculation)...');
    try {
      const res = await fetch(`${API_BASE}/api/admin/test-alert`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        handleLogout('Session expired. Please sign in again.');
        return;
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Action blocked');
      appendLog(data.message);
      fetchTelemetry();
    } catch (err) {
      appendLog(`Diagnostic failed: ${err.message}`, true);
    } finally {
      setActionLoading(false);
    }
  }

  async function triggerFallbackToggle() {
    const isActive = telemetry?.fallback_active;
    const confirmed = window.confirm(
      isActive
        ? 'Restore Gemini AI Orchestrator as the active pipeline?'
        : 'WARNING: Switch pipeline directly to the hardcoded Non-AI Fallback script?'
    );
    if (!confirmed) return;

    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/override`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        handleLogout('Session expired. Please sign in again.');
        return;
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Override blocked');
      appendLog(data.message, data.fallback_active);
      fetchTelemetry();
    } catch (err) {
      appendLog(`Override failed: ${err.message}`, true);
    } finally {
      setActionLoading(false);
    }
  }

  // Unauthenticated View — Restricted Login Screen
  if (!token) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#09090b] px-6 text-zinc-100">
        <div className="w-full max-w-sm rounded-2xl border border-white/10 bg-[#0c0c0f] p-8">
          <div className="flex items-center gap-2.5">
            <Lock className="h-4 w-4 text-sky-400" />
            <span className="text-xs font-medium uppercase tracking-widest text-zinc-500">
              Restricted Access
            </span>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-white">
            Diluvium Admin
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Sign in with your Supabase administrator account.
          </p>

          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-400">Admin Email</label>
              <input
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@diluvium.local"
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-[#09090b] px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400">Password</label>
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-[#09090b] px-3.5 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:border-sky-400 focus:outline-none"
              />
            </div>

            {authError && (
              <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                {authError}
              </p>
            )}

            <button
              type="submit"
              disabled={authLoading}
              className="w-full cursor-pointer rounded-lg bg-sky-400 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-sky-300 disabled:opacity-50"
            >
              {authLoading ? 'Authenticating...' : 'Authorize Session'}
            </button>
          </form>

          <div className="mt-6 border-t border-white/10 pt-4 text-center">
            <Link to="/" className="text-xs text-zinc-500 transition hover:text-zinc-200">
              ← Return to Diluvium
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Compute SVG Donut & Hydrograph metrics
  const tokensUsed = telemetry?.tokens_used ?? 0;
  const tokensLimit = telemetry?.tokens_limit ?? 15000;
  const tokenPct = Math.min((tokensUsed / Math.max(tokensLimit, 1)) * 100, 100);
  const donutRadius = 42;
  const donutCircumference = 2 * Math.PI * donutRadius;
  const donutOffset = donutCircumference * (1 - tokenPct / 100);

  const manggaraiPath = buildHydroPath(telemetry?.hydro_manggarai, 500, 950);
  const katulampaPath = buildHydroPath(telemetry?.hydro_katulampa, 0, 250);
  const siagaBadgeClass =
    SIAGA_STYLES[telemetry?.current_siaga] || 'border-white/15 bg-white/5 text-zinc-300';

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 antialiased">
      {/* Top Bar */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#09090b]/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2 text-white">
              <Waves className="h-5 w-5 text-sky-400" />
              <span className="font-semibold tracking-tight">Diluvium</span>
            </Link>
            <span className="text-zinc-700">/</span>
            <span className="text-sm text-zinc-400">Admin Console</span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Live Kelurahan Switcher */}
            <select
              value={selectedArea}
              onChange={(e) => setSelectedArea(e.target.value)}
              className="rounded-lg border border-white/15 bg-[#0c0c0f] px-3 py-1.5 text-xs text-zinc-200 focus:border-sky-400 focus:outline-none"
            >
              <option value="auto">Auto: Highest Risk</option>
              {(telemetry?.available_areas || []).map((area) => (
                <option key={area.adm4_code} value={area.adm4_code}>
                  {area.label}
                </option>
              ))}
            </select>

            <span
              className={`rounded-full border px-3 py-1 font-mono text-xs font-semibold ${siagaBadgeClass}`}
            >
              {telemetry?.current_siaga || 'Loading...'}
            </span>

            <button
              onClick={fetchTelemetry}
              title="Refresh Now"
              className="cursor-pointer rounded-lg border border-white/10 p-1.5 text-zinc-400 transition hover:border-white/25 hover:text-white"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            <button
              onClick={() => handleLogout()}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-zinc-300 transition hover:border-white/30 hover:text-white"
            >
              <LogOut className="h-3.5 w-3.5" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        {/* Row 1: Primary Telemetry KPIs */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-5">
            <p className="text-xs uppercase tracking-wider text-zinc-500">AI Orchestrator</p>
            <p
              className={`mt-2 text-base font-semibold ${
                telemetry?.fallback_active ? 'text-red-400' : 'text-white'
              }`}
            >
              {telemetry?.gemini_status || 'Connecting...'}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {telemetry?.fallback_active ? 'Circuit breaker engaged' : 'FastMCP synchronized'}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-5">
            <p className="text-xs uppercase tracking-wider text-zinc-500">BMKG Ingestion</p>
            <p className="mt-2 text-base font-semibold text-white">
              {telemetry?.monitored_locations ?? '—'} Kelurahan
            </p>
            <p className="mt-1 truncate text-xs text-zinc-500">
              {telemetry?.api_bmkg_status || 'Polling...'}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-5">
            <p className="text-xs uppercase tracking-wider text-zinc-500">Peak Rainfall</p>
            <p className="mt-2 font-mono text-2xl font-semibold text-sky-400">
              {telemetry ? `${telemetry.peak_rainfall_mm} mm/3h` : '—'}
            </p>
            <p className="mt-1 truncate text-xs text-zinc-500">
              {telemetry?.highest_risk_area || '—'}
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-5">
            <p className="text-xs uppercase tracking-wider text-zinc-500">Runoff Forecast</p>
            <p className="mt-2 font-mono text-2xl font-semibold text-white">
              {telemetry?.estimated_arrival_eta || '—'}
            </p>
            <p className="mt-1 font-mono text-xs text-zinc-500">
              {telemetry
                ? `Depth ${telemetry.predicted_depth_cm} cm • Radius ${telemetry.inundation_radius_km}`
                : 'Calculating...'}
            </p>
          </div>
        </section>

        {/* Row 2: Gate Saturation, Hydrograph, and Token Donut */}
        <section className="grid gap-6 lg:grid-cols-12">
          {/* Gate Threshold Saturation */}
          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6 lg:col-span-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                Gate Saturation
              </h2>
              <span className="font-mono text-xs text-zinc-400">
                Avg {telemetry?.avg_gate_saturation ?? 0}%
              </span>
            </div>

            <div className="mt-6 space-y-5">
              {[
                {
                  name: 'Manggarai',
                  cm: telemetry?.water_level_manggarai ?? 0,
                  max: 850,
                  pct: telemetry?.manggarai_pct ?? 0,
                  bar: 'bg-sky-400',
                },
                {
                  name: 'Depok',
                  cm: telemetry?.water_level_depok ?? 0,
                  max: 350,
                  pct: telemetry?.depok_pct ?? 0,
                  bar: 'bg-indigo-400',
                },
                {
                  name: 'Katulampa',
                  cm: telemetry?.water_level_katulampa ?? 0,
                  max: 200,
                  pct: telemetry?.katulampa_pct ?? 0,
                  bar: 'bg-emerald-400',
                },
              ].map((gate) => (
                <div key={gate.name}>
                  <div className="flex items-baseline justify-between text-xs">
                    <span className="font-medium text-zinc-200">{gate.name}</span>
                    <span className="font-mono text-zinc-400">
                      {gate.cm} / {gate.max} cm ({gate.pct}%)
                    </span>
                  </div>
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${gate.bar}`}
                      style={{ width: `${gate.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 6-Point Rolling Hydrograph */}
          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6 lg:col-span-5">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-500">
                <Activity className="h-3.5 w-3.5 text-sky-400" />
                Live Hydrological Trend
              </h2>
              <div className="flex items-center gap-4 text-[11px] text-zinc-400">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-sky-400" />
                  Manggarai
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-pink-400" />
                  Katulampa
                </span>
              </div>
            </div>

            <div className="mt-5">
              <svg viewBox="0 0 520 160" className="h-40 w-full overflow-visible">
                {[30, 80, 130].map((y) => (
                  <line
                    key={y}
                    x1="14"
                    x2="506"
                    y1={y}
                    y2={y}
                    stroke="rgba(255,255,255,0.06)"
                    strokeDasharray="4 4"
                  />
                ))}
                {manggaraiPath && (
                  <path
                    d={manggaraiPath}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}
                {katulampaPath && (
                  <path
                    d={katulampaPath}
                    fill="none"
                    stroke="#f472b6"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}
              </svg>

              <div className="mt-2 flex justify-between px-2 font-mono text-[10px] text-zinc-500">
                {(telemetry?.hydro_labels || []).map((lbl, idx) => (
                  <span key={`${lbl}-${idx}`}>{lbl}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Gemini Token Quota Donut */}
          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6 lg:col-span-3">
            <h2 className="text-xs font-medium uppercase tracking-widest text-zinc-500">
              Gemini Token Quota
            </h2>

            <div className="mt-4 flex flex-col items-center">
              <div className="relative flex h-28 w-28 items-center justify-center">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r={donutRadius}
                    fill="none"
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r={donutRadius}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={donutCircumference}
                    strokeDashoffset={donutOffset}
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute text-center">
                  <div className="font-mono text-base font-semibold text-white">
                    {tokensUsed.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-zinc-500">/ {tokensLimit.toLocaleString()}</div>
                </div>
              </div>

              <div className="mt-4 w-full space-y-1.5 border-t border-white/10 pt-3 font-mono text-xs text-zinc-400">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Ingestion</span>
                  <span>{telemetry?.tokens_ingestion ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Calculation</span>
                  <span>{telemetry?.tokens_calculation ?? 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Verification</span>
                  <span>{telemetry?.tokens_verification ?? 0}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Row 3: Manual Controls & Audit Terminal */}
        <section className="grid gap-6 lg:grid-cols-12">
          <div className="flex flex-col justify-between rounded-2xl border border-white/10 bg-[#0c0c0f] p-6 lg:col-span-5">
            <div>
              <h2 className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                Manual Overrides &amp; Diagnostics
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-zinc-400">
                All actions require a verified Supabase Bearer token and are logged below.
              </p>
            </div>

            <div className="mt-6 flex flex-col gap-3">
              <button
                onClick={triggerTestAlert}
                disabled={actionLoading}
                className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm font-medium text-white transition hover:border-sky-400/60 hover:bg-sky-400/10 disabled:opacity-50"
              >
                <Send className="h-4 w-4 text-sky-400" />
                Run Diagnostic Dispatch (Telegram / Discord)
              </button>

              <button
                onClick={triggerFallbackToggle}
                disabled={actionLoading}
                className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium transition disabled:opacity-50 ${
                  telemetry?.fallback_active
                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                    : 'border-red-500/40 bg-red-500/10 text-red-300 hover:bg-red-500/20'
                }`}
              >
                <ShieldAlert className="h-4 w-4" />
                {telemetry?.fallback_active
                  ? 'Restore Gemini AI Orchestrator'
                  : 'Engage Emergency Non-AI Fallback'}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6 lg:col-span-7">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-zinc-500">
              <Terminal className="h-3.5 w-3.5 text-zinc-400" />
              System Audit Log
            </div>

            <div className="mt-4 h-40 overflow-y-auto rounded-xl border border-white/10 bg-[#070709] p-4 font-mono text-xs leading-relaxed">
              {logs.map((entry, idx) => (
                <div key={idx} className="mb-1.5">
                  <span className="text-zinc-600">[{entry.time}]</span>{' '}
                  <span className={entry.isError ? 'text-red-400' : 'text-emerald-400'}>&gt;</span>{' '}
                  <span className={entry.isError ? 'text-red-300' : 'text-zinc-300'}>
                    {entry.text}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}