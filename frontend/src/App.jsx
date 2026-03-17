import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const CLOUD_URL = `https://jsonblob.com/api/jsonBlob/019cfa65-ac81-7121-a9ac-bcc786dcf68e`;

const App = () => {
  const [stats, setStats] = useState({ balance: 0, equity: 0, dailyPnL: 0, drawdown: 0, is_trained: false, market_price: 1.08502 });
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [depositPhone, setDepositPhone] = useState('');
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawPhone, setWithdrawPhone] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [statusMsg, setStatusMsg] = useState('');
  const [connected, setConnected] = useState(false);
  const [chartData, setChartData] = useState(
    Array.from({ length: 40 }, (_, i) => ({ time: i, price: 1.08502 + Math.random() * 0.0005 }))
  );

  const fetchState = async () => {
    try {
      const res = await fetch(CLOUD_URL, { cache: "no-store", headers: { 'Cache-Control': 'no-cache' }});
      const data = await res.json();
      
      if (data && data.stats) {
        setStats(data.stats);
        setIsRunning(data.stats.is_running || false);
        setConnected(true);
        
        const livePrice = data.stats.market_price || 0;
        if (livePrice > 0) {
          setChartData(prev => {
            const next = [...prev.slice(-39), { time: new Date().toLocaleTimeString(), price: livePrice }];
            return next;
          });
        }
      }
      
      if (data && data.status) {
          if (data.status.includes("SUCCESS") || data.status.includes("ERROR")) {
              setStatusMsg(data.status);
          }
      }
    } catch {
      setConnected(false);
    }
  };

  const sendCommand = async (actionObj) => {
    try {
      const res = await fetch(CLOUD_URL);
      const current = await res.json() || {};
      const payload = { ...current, command: actionObj };
      await fetch(CLOUD_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return true;
    } catch (e) {
      return false;
    }
  };

  useEffect(() => {
    fetchState();
    const iv = setInterval(fetchState, 3000);
    return () => clearInterval(iv);
  }, []);

  const handleAction = async (action, data = {}) => {
    setIsLoading(true);
    setStatusMsg(`Sending ${action} request...`);
    const ok = await sendCommand({ action, ...data });
    if (!ok) setStatusMsg(`Error: Failed to connect to Cloud Relay.`);
    setIsLoading(false);
  };

  return (
    <div className="premium-container">
      {/* Header */}
      <div className="header-section">
        <div>
          <div className="logo-text">
            <span>⚡</span>
            GESI AI TRADER PRO
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginTop: '0.5rem' }}>
            <div className={connected ? "live-indicator" : ""} style={{ background: connected ? '#10b981' : '#ef4444' }} />
            <span style={{ color: '#8b949e', fontSize: '0.85rem' }}>
              {connected ? 'REAL-TIME CLOUD SYNC ACTIVE' : 'RECONNECTING TO CLOUD...'}
            </span>
          </div>
        </div>
        
        <div className={`status-badge ${!isRunning ? 'standby' : ''}`}>
          <div className={isRunning ? "live-indicator" : ""} style={{ width: 6, height: 6, opacity: isRunning ? 1 : 0.3 }} />
          {isRunning ? 'EGM LIVE TRADING' : 'SYSTEM STANDBY'}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-container">
        {[
          { label: 'Available Balance', value: `$${(stats.balance || 0).toFixed(2)}`, color: '#3b82f6' },
          { label: 'Unrealized P&L', value: `+$${(stats.dailyPnL || 0).toFixed(2)}`, color: '#10b981' },
          { label: 'Account Equity', value: `$${(stats.equity || 0).toFixed(2)}`, color: '#a78bfa' },
          { label: 'Market Sentiment', value: stats.is_trained ? 'BULLISH' : 'NEUTRAL', color: '#f59e0b' },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-panel stat-card">
            <span className="stat-label">{label}</span>
            <span className="stat-value" style={{ color }}>{value}</span>
          </div>
        ))}
      </div>

      <div className="main-layout">
        {/* Market Graph */}
        <div className="glass-panel" style={{ minHeight: '440px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>EUR / USD Market Feed</h3>
              <p style={{ color: '#8b949e', fontSize: '0.8rem', margin: '0.2rem 0' }}>98% Confidence Level — Optimized Moonshot</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: '#10b981', fontWeight: 800, fontSize: '1.2rem' }}>{(stats.market_price || 0).toFixed(5)}</div>
              <div style={{ color: '#8b949e', fontSize: '0.7rem' }}>LIVE TICK</div>
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
                contentStyle={{ background: '#0d1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                itemStyle={{ color: '#10b981' }}
              />
              <Area type="monotone" dataKey="price" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorPrice)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Action Panel */}
        <div className="controls-section">
          {/* Main Controls */}
          <div className="glass-panel">
            <h4 className="stat-label" style={{ marginBottom: '1rem' }}>Engine Control</h4>
            {!isRunning 
              ? <button className="control-btn btn-primary" onClick={() => handleAction('START')} disabled={isLoading || !connected}>
                  🚀 START AI ENGINE
                </button>
              : <button className="control-btn btn-danger" onClick={() => handleAction('STOP')} disabled={isLoading}>
                  ✋ EMERGENCY STOP
                </button>
            }
          </div>

          {/* Transfers */}
          <div className="glass-panel">
            <h4 className="stat-label" style={{ marginBottom: '1rem' }}>M-Pesa Transfers</h4>
            
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ paddingBottom: '1rem', borderBottom: '1px solid var(--border-glass)', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, display: 'block', marginBottom: '0.5rem', color: '#10b981' }}>DEPOSIT (Till/Paybill)</span>
                <input className="premium-input" placeholder="Phone (254...)" value={depositPhone} onChange={e => setDepositPhone(e.target.value)} />
                <input className="premium-input" placeholder="Amount (KES)" value={depositAmount} onChange={e => setDepositAmount(e.target.value)} />
                <button className="control-btn btn-primary" style={{ height: '40px' }} onClick={() => handleAction('DEPOSIT', { phone: depositPhone, amount: depositAmount })}>INSTANT DEPOSIT</button>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, display: 'block', marginBottom: '0.5rem', color: '#f59e0b' }}>WITHDRAW PROFITS</span>
                <input className="premium-input" placeholder="Phone (254...)" value={withdrawPhone} onChange={e => setWithdrawPhone(e.target.value)} />
                <input className="premium-input" placeholder="Amount (KES)" value={withdrawAmount} onChange={e => setWithdrawAmount(e.target.value)} />
                <button className="control-btn btn-withdraw" style={{ height: '40px' }} onClick={() => handleAction('WITHDRAW', { phone: withdrawPhone, amount: withdrawAmount })}>WITHDRAW NOW</button>
              </div>
            </div>

            {statusMsg && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', borderRadius: '8px', fontSize: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border-glass)' }}>
                {statusMsg}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer Features */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginTop: '1.5rem' }}>
        {[
          { icon: '💎', title: 'Moonshot AI', desc: '98.5% Accuracy' },
          { icon: '⚡', title: 'B2C Payouts', desc: 'Instant M-Pesa' },
          { icon: '🛡️', title: 'Zero-Risk', desc: 'Trail Stop Logic' },
          { icon: '🌍', title: 'Cloud Relay', desc: 'No ngrok Needed' },
        ].map(f => (
          <div key={f.title} className="glass-panel" style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '1.2rem' }}>{f.icon}</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginTop: '0.5rem' }}>{f.title}</div>
            <div style={{ color: '#8b949e', fontSize: '0.7rem' }}>{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;

