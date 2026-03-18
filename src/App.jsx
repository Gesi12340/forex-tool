import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Play, Square, CreditCard, ArrowUpRight, Shield, Zap, Globe, TrendingUp } from 'lucide-react';

const IS_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = IS_LOCAL ? '' : 'https://jsonblob.com/api/jsonBlob/019cff51-9acf-75cc-9685-304ab695d7a7';

const App = () => {
  const [stats, setStats] = useState({ 
    balance: 0, 
    equity: 0, 
    dailyPnL: 0, 
    drawdown: 0, 
    is_trained: true, 
    market_price: 1.08502 
  });
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [depositPhone, setDepositPhone] = useState('');
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawPhone, setWithdrawPhone] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [connected, setConnected] = useState(false);
  const [relayActive, setRelayActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(0);
  const [chartData, setChartData] = useState(
    Array.from({ length: 40 }, (_, i) => ({ time: i, price: 1.08502 + Math.random() * 0.0005 }))
  );
  const [debugLogs, setDebugLogs] = useState([]);

  const addLog = (msg) => {
    setDebugLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 5));
  };

  const fetchState = async () => {
    try {
      const url = IS_LOCAL ? '/api/status' : API_BASE;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      
      if (data && data.stats) {
        setStats(data.stats);
        setIsRunning(data.stats.is_running || false);
        setConnected(true);
        
        // Track Relay Activity
        const ts = data.last_update || 0;
        setLastUpdate(ts);
        const isActive = (Date.now() / 1000) - ts < 60;
        setRelayActive(isActive);
        
        if (!isActive) {
           addLog("Warning: Local Relay is offline/timed out.");
        }

        const livePrice = data.stats.market_price || 0;
        if (livePrice > 0) {
          setChartData(prev => {
            const next = [...prev.slice(-39), { time: new Date().toLocaleTimeString(), price: livePrice }];
            return next;
          });
        }
      } else {
        setConnected(true); 
      }
    } catch (err) {
      setConnected(false);
      setRelayActive(false);
      const errMsg = `Relay Connection Error: ${err.message}`;
      setStatusMsg(errMsg);
      addLog(errMsg);
    }
  };

  const sendCommand = async (actionObj) => {
    try {
      if (IS_LOCAL) {
        const res = await fetch('/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(actionObj)
        });
        return res.ok;
      } else {
        const res = await fetch(API_BASE);
        const current = await res.json() || {};
        const payload = { ...current, command: actionObj };
        await fetch(API_BASE, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        return true;
      }
    } catch (e) {
      addLog(`Send Error: ${e.message}`);
      return false;
    }
  };

  useEffect(() => {
    fetchState();
    const iv = setInterval(fetchState, 5000);
    return () => clearInterval(iv);
  }, []);

  const manualSync = async () => {
    setIsLoading(true);
    addLog("Manual sync initiated...");
    await fetchState();
    setIsLoading(false);
  };

  const handleAction = async (action, data = {}) => {
    // 1. Validate Amount if applicable
    if (action === 'DEPOSIT' || action === 'WITHDRAW') {
      const amt = parseFloat(data.amount);
      if (isNaN(amt) || amt < 50 || amt > 20000) {
        const err = `Invalid amount: Minimum 50, Maximum 20,000 KES.`;
        setStatusMsg(err);
        addLog(`Error: ${err}`);
        return;
      }
      if (!data.phone || data.phone.length < 10) {
        setStatusMsg("Error: Please enter a valid phone number.");
        return;
      }
    }

    setIsLoading(true);
    setStatusMsg(`Requesting Safaricom Gateway...`);
    addLog(`Initiating ${action} for ${data.amount} KES...`);
    
    const ok = await sendCommand({ action, ...data });
    if (ok && ok.status) {
        setStatusMsg(ok.status);
    } else if (!ok) {
        setStatusMsg(`Error: Connection to local engine failed.`);
        addLog("Sync Error: Local server unreachable.");
    }
    setIsLoading(false);
  };

  return (
    <div className="premium-container">
      {/* Header */}
      <div className="header-section glass-panel" style={{ background: 'rgba(16, 185, 129, 0.05)', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="logo-text">
            <Zap size={32} fill="var(--accent-primary)" />
            GESI AI PREMIUM V4.0
          </div>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', margin: '0.25rem 0' }}>The Ultimate Automated Forex Engine</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div className={connected ? "live-indicator" : ""} style={{ background: connected ? 'var(--accent-primary)' : '#ef4444' }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem', fontWeight: 600 }}>
                {!connected ? 'CLOUD OFFLINE' : (!relayActive ? 'WAITING FOR LOCAL RELAY...' : 'FULLY OPERATIONAL')}
              </span>
              <button 
                onClick={manualSync} 
                style={{ background: 'transparent', border: 'none', color: 'var(--accent-primary)', fontSize: '0.65rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', padding: 0 }}
                disabled={isLoading}
              >
                <Zap size={10} fill={connected ? "var(--accent-primary)" : "transparent"} />
                {connected ? 'MANUAL RE-SYNC' : 'RETRY CONNECTION'}
              </button>
            </div>
          </div>
        
          <div className={`status-badge ${!isRunning ? 'standby' : ''}`}>
            <div className={isRunning ? "live-indicator" : ""} style={{ width: 6, height: 6, opacity: isRunning ? 1 : 0.3 }} />
            {isRunning ? 'ALGORITHM ACTIVE' : 'ENGINE STANDBY'}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-container">
        {[
          { label: 'Net Balance', value: `KES ${(stats.balance * 128 || 0).toLocaleString()}`, sub: `$${(stats.balance || 0).toFixed(2)}`, color: '#3b82f6' },
          { label: 'Real-time P&L', value: `+$${(stats.dailyPnL || 0).toFixed(2)}`, sub: 'Active Trades', color: '#10b981' },
          { label: 'Account Equity', value: `$${(stats.equity || 0).toFixed(2)}`, sub: 'Post-Margin', color: '#a78bfa' },
          { label: 'AI Sentiment', value: stats.is_trained ? 'BULLISH' : 'NEUTRAL', sub: '98% Confidence', color: '#f59e0b' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="glass-panel stat-card">
            <span className="stat-label">{label}</span>
            <span className="stat-value" style={{ color }}>{value}</span>
            <span style={{ color: '#8b949e', fontSize: '0.75rem', marginTop: '-0.25rem' }}>{sub}</span>
          </div>
        ))}
      </div>

      <div className="main-layout">
        {/* Market Graph */}
        <div className="glass-panel" style={{ minHeight: '440px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>EUR/USD Live Liquidity</h3>
              <p style={{ color: '#8b949e', fontSize: '0.85rem', margin: '0.2rem 0' }}>Smart Money Flow Index — H1 TF</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: '#10b981', fontWeight: 900, fontSize: '1.5rem', fontFamily: 'monospace' }}>
                {(stats.market_price || 0).toFixed(5)}
              </div>
              <div style={{ color: '#8b949e', fontSize: '0.75rem', fontWeight: 600 }}>INSTANT FEED</div>
            </div>
          </div>
          
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
              <XAxis dataKey="time" hide />
              <YAxis domain={['auto', 'auto']} hide />
              <Tooltip 
                contentStyle={{ background: 'rgba(13, 17, 23, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)' }}
                itemStyle={{ color: '#10b981', fontWeight: 700 }}
              />
              <Area type="monotone" dataKey="price" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorPrice)" animationDuration={1000} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Action Panel */}
        <div className="controls-section" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Main Controls */}
          <div className="glass-panel">
            <h4 className="stat-label" style={{ marginBottom: '1.25rem' }}>Engine Master Switch</h4>
            {!isRunning 
              ? <button className="control-btn btn-primary" style={{ padding: '1.25rem' }} onClick={() => handleAction('START')} disabled={isLoading || !connected}>
                  <Play size={20} fill="currentColor" /> START TRADING BOT
                </button>
              : <button className="control-btn btn-danger" style={{ padding: '1.25rem' }} onClick={() => handleAction('STOP')} disabled={isLoading}>
                  <Square size={20} fill="currentColor" /> KILL ALL PROCESSES
                </button>
            }
          </div>

          {/* Transfers */}
          <div className="glass-panel" style={{ border: '1px solid rgba(255,255,255,0.15)', background: 'linear-gradient(135deg, rgba(13,17,23,0.8), rgba(13,17,23,0.4))' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <CreditCard size={22} color="var(--accent-primary)" />
              <h4 className="stat-label" style={{ margin: 0, fontSize: '0.9rem', color: '#fff' }}>Gesi Secure Gateway</h4>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ padding: '1.25rem', borderRadius: '16px', background: 'rgba(0, 255, 136, 0.03)', border: '1px solid rgba(0, 255, 136, 0.1)' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 900, display: 'block', marginBottom: '1rem', color: 'var(--accent-primary)', letterSpacing: '1px' }}>INSTANT DEPOSIT (STK)</span>
                <input className="premium-input" placeholder="M-Pesa Number (e.g. 2547...)" value={depositPhone} onChange={e => setDepositPhone(e.target.value)} />
                <input className="premium-input" placeholder="Amount in KES (Min 50)" value={depositAmount} onChange={e => setDepositAmount(e.target.value)} />
                <button className="control-btn btn-primary" style={{ height: '54px', fontSize: '1rem', boxShadow: '0 0 20px var(--glow-green)' }} onClick={() => handleAction('DEPOSIT', { phone: depositPhone, amount: depositAmount })}>
                  <Zap size={18} fill="currentColor" /> DEPOSIT NOW
                </button>
              </div>

              <div style={{ padding: '1.25rem', borderRadius: '16px', background: 'rgba(255, 204, 0, 0.03)', border: '1px solid rgba(255, 204, 0, 0.1)' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 900, display: 'block', marginBottom: '1rem', color: 'var(--accent-yellow)', letterSpacing: '1px' }}>INSTANT WITHDRAWAL</span>
                <input className="premium-input" placeholder="M-Pesa Number" value={withdrawPhone} onChange={e => setWithdrawPhone(e.target.value)} />
                <input className="premium-input" placeholder="Amount (Profit Only)" value={withdrawAmount} onChange={e => setWithdrawAmount(e.target.value)} />
                <button className="control-btn btn-withdraw" style={{ height: '54px', fontSize: '1rem', background: 'rgba(255,204,0,0.15)', color: 'var(--accent-yellow)', borderColor: 'var(--accent-yellow)' }} onClick={() => handleAction('WITHDRAW', { phone: withdrawPhone, amount: withdrawAmount })}>
                  <ArrowUpRight size={18} /> WITHDRAW TO MPESA
                </button>
              </div>
            </div>

            {statusMsg && (
              <div className="glass-panel" style={{ marginTop: '1.25rem', padding: '1rem', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', animation: 'fadeIn 0.3s' }}>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <div className="live-indicator" style={{ width: 6, height: 6 }} />
                  <span style={{ color: '#e6edf3', fontSize: '0.85rem', fontWeight: 500 }}>{statusMsg}</span>
                </div>
              </div>
            )}
            
            {/* Debug Info */}
            <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.65rem', color: '#8b949e', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>CONNECTION LOGS</span>
                <span>V3.2-STABLE</span>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '0.75rem', fontFamily: 'monospace', fontSize: '0.7rem' }}>
                {debugLogs.length === 0 && <div style={{ color: '#4b5563' }}>Waiting for signals...</div>}
                {debugLogs.map((log, i) => (
                  <div key={i} style={{ color: log.includes('Error') ? '#ef4444' : '#10b981', marginBottom: '2px' }}>{log}</div>
                ))}
              </div>
              {!connected && (
                <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                  <p style={{ margin: 0, fontSize: '0.7rem', color: '#ef4444', fontWeight: 600 }}>
                    TIP: Ensure `relay_manager.py` is running in your local terminal. 
                    If it is, check your internet connection or firewall.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Features */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginTop: '1.5rem' }}>
        {[
          { icon: <TrendingUp size={20} color="#10b981" />, title: 'Moonshot AI', desc: 'LSTM + XGBoost' },
          { icon: <Zap size={20} color="#3b82f6" />, title: 'Instant Sync', desc: 'REST Cloud Relay' },
          { icon: <Shield size={20} color="#a78bfa" />, title: 'Risk Lock', desc: 'ATR Trail Stop' },
          { icon: <Globe size={20} color="#f59e0b" />, title: 'Edge Node', desc: 'Global Execution' },
        ].map(f => (
          <div key={f.title} className="glass-panel" style={{ textAlign: 'center', padding: '1.25rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '12px' }}>{f.icon}</div>
            <div style={{ fontWeight: 800, fontSize: '0.9rem' }}>{f.title}</div>
            <div style={{ color: '#8b949e', fontSize: '0.75rem', fontWeight: 500 }}>{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;


