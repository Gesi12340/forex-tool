import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const App = () => {
  const [stats, setStats] = useState({ balance: 0, equity: 0, dailyPnL: 0, drawdown: 0, is_trained: false });
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('trading_api_url') || '');
  const [depositPhone, setDepositPhone] = useState('');
  const [depositAmount, setDepositAmount] = useState('');
  const [depositStatus, setDepositStatus] = useState('');
  const [connected, setConnected] = useState(false);
  const [chartData, setChartData] = useState(
    Array.from({ length: 20 }, (_, i) => ({ time: i, price: 1.0850 + Math.random() * 0.005 }))
  );

  const getBase = () => apiUrl.trim();

  const fetchStats = async () => {
    if (!getBase()) return;
    try {
      const res = await fetch(`${getBase()}/api/stats`);
      const data = await res.json();
      setStats(data);
      setConnected(true);
      setChartData(prev => {
        const next = [...prev.slice(-19), { time: Date.now(), price: data.equity || data.balance || 1.085 }];
        return next;
      });
    } catch {
      setConnected(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const iv = setInterval(fetchStats, 5000);
    return () => clearInterval(iv);
  }, [apiUrl]);

  const handleStart = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${getBase()}/api/start`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'STARTED' || data.status === 'ALREADY_RUNNING') setIsRunning(true);
    } catch { alert('Failed to start — check your tunnel URL'); }
    setIsLoading(false);
  };

  const handleStop = async () => {
    try {
      await fetch(`${getBase()}/api/stop`, { method: 'POST' });
      setIsRunning(false);
    } catch { alert('Failed to stop'); }
  };

  const handleDeposit = async () => {
    if (!depositPhone || !depositAmount) { setDepositStatus('Please enter phone and amount'); return; }
    setIsLoading(true);
    setDepositStatus('Sending STK Push...');
    try {
      const res = await fetch(`${getBase()}/api/deposit/mpesa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: depositPhone, amount: depositAmount })
      });
      const data = await res.json();
      setDepositStatus(data.status === 'SUCCESS'
        ? `STK Push sent to ${depositPhone}! Check your phone.`
        : `Error: ${data.message}`);
    } catch {
      setDepositStatus('Failed — ensure your tunnel URL is connected');
    }
    setIsLoading(false);
  };

  const styles = {
    app: { minHeight: '100vh', background: 'linear-gradient(135deg,#0f0c29,#302b63,#24243e)', color: '#fff', fontFamily: 'Inter, sans-serif', padding: '1.5rem' },
    card: { background: 'rgba(255,255,255,0.07)', backdropFilter: 'blur(10px)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.12)', padding: '1.25rem' },
    title: { margin: 0, fontSize: '1.6rem', fontWeight: 900, background: 'linear-gradient(90deg,#10b981,#3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
    subtitle: { margin: '0.25rem 0 0', color: '#9ca3af', fontSize: '0.85rem' },
    grid4: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: '1rem', margin: '1.5rem 0' },
    statLabel: { color: '#9ca3af', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' },
    statValue: { fontSize: '1.5rem', fontWeight: 800, marginTop: '0.4rem' },
    btn: (color) => ({ background: color, color: '#fff', border: 'none', borderRadius: '12px', padding: '0.9rem 1.5rem', fontWeight: 800, fontSize: '1rem', cursor: 'pointer', width: '100%', marginBottom: '0.5rem' }),
    input: { width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', color: '#fff', padding: '0.75rem', fontSize: '0.95rem', boxSizing: 'border-box', marginBottom: '0.75rem' },
    connDot: (ok) => ({ width: 10, height: 10, borderRadius: '50%', background: ok ? '#10b981' : '#ef4444', display: 'inline-block', marginRight: '0.5rem' }),
    mainGrid: { display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginTop: '1.5rem' },
  };

  return (
    <div style={styles.app}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={styles.title}>AI TRADER PRO — KENYA</h1>
          <p style={styles.subtitle}>
            <span style={styles.connDot(connected)} />
            {connected ? 'Live Connection Active' : 'Not Connected — Enter Tunnel URL Below'}
          </p>
        </div>
        <div style={{ ...styles.card, padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: isRunning ? '#10b981' : '#6b7280', display: 'inline-block' }} />
          <span style={{ fontWeight: 700 }}>{isRunning ? 'BOT RUNNING' : 'STANDBY'}</span>
        </div>
      </div>

      {/* Tunnel URL */}
      <div style={{ ...styles.card, marginTop: '1.25rem' }}>
        <p style={{ ...styles.statLabel, marginBottom: '0.5rem' }}>Backend Tunnel URL (required to connect)</p>
        <input
          style={styles.input}
          type="text"
          placeholder="Paste your ngrok URL here — e.g. https://abc123.ngrok.io"
          value={apiUrl}
          onChange={(e) => { setApiUrl(e.target.value); localStorage.setItem('trading_api_url', e.target.value); }}
        />
        <p style={{ color: '#9ca3af', fontSize: '0.78rem', margin: 0 }}>
          Start your bot with <code>python backend/api.py</code>, then run <code>ngrok http 5000</code> and paste the link above.
        </p>
      </div>

      {/* Stats */}
      <div style={styles.grid4}>
        {[
          { label: 'Balance', value: `$${stats.balance.toLocaleString()}`, color: '#3b82f6' },
          { label: 'Daily P&L', value: `+$${stats.dailyPnL}`, color: '#10b981' },
          { label: 'Equity', value: `$${stats.equity.toLocaleString()}`, color: '#a78bfa' },
          { label: 'AI Status', value: stats.is_trained ? 'TRAINED' : 'MOCK MODE', color: stats.is_trained ? '#10b981' : '#f59e0b' },
        ].map(({ label, value, color }) => (
          <div key={label} style={styles.card}>
            <div style={styles.statLabel}>{label}</div>
            <div style={{ ...styles.statValue, color }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div style={styles.mainGrid}>
        {/* Chart */}
        <div style={styles.card}>
          <h3 style={{ margin: '0 0 1rem', fontWeight: 700 }}>Live Market Feed — EUR/USD</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <XAxis dataKey="time" hide />
              <YAxis domain={['auto', 'auto']} hide />
              <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Controls + Deposit */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Trading Controls */}
          <div style={styles.card}>
            <h3 style={{ margin: '0 0 1rem', fontWeight: 700 }}>Trading Controls</h3>
            {!isRunning
              ? <button style={styles.btn('#10b981')} onClick={handleStart} disabled={isLoading || !getBase()}>
                  {isLoading ? 'Starting...' : '▶ START AUTO-TRADING'}
                </button>
              : <button style={styles.btn('#ef4444')} onClick={handleStop}>
                  ⏹ STOP TRADING
                </button>
            }
            <p style={{ ...styles.statLabel, textAlign: 'center', marginTop: '0.5rem' }}>
              {isRunning ? 'Bot is live — scanning for Moonshot trades' : 'Bot is in standby mode'}
            </p>
          </div>

          {/* Deposit via M-Pesa */}
          <div style={styles.card}>
            <h3 style={{ margin: '0 0 1rem', fontWeight: 700, color: '#10b981' }}>Deposit via M-Pesa</h3>
            <input
              style={styles.input}
              type="tel"
              placeholder="Phone: 2547XXXXXXXX"
              value={depositPhone}
              onChange={e => setDepositPhone(e.target.value)}
            />
            <input
              style={styles.input}
              type="number"
              placeholder="Amount (KES) e.g. 500"
              value={depositAmount}
              onChange={e => setDepositAmount(e.target.value)}
            />
            <button style={styles.btn('#f59e0b')} onClick={handleDeposit} disabled={isLoading}>
              {isLoading ? 'Sending...' : 'DEPOSIT NOW (M-Pesa)'}
            </button>
            {depositStatus && (
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: depositStatus.startsWith('Error') ? '#ef4444' : '#10b981' }}>
                {depositStatus}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Strategy Info */}
      <div style={{ ...styles.card, marginTop: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1.5rem' }}>
        {[
          { icon: '🎯', title: 'Moonshot Detection', desc: 'ADX > 40 + RSI > 60 = Hyper-Growth Signal' },
          { icon: '🛡️', title: 'Zero-Loss Guard', desc: 'Auto-closes trades on EMA reversal' },
          { icon: '📈', title: '10x–100x Target', desc: 'Compounds position size as balance grows' },
          { icon: '💰', title: 'Auto-Compounding', desc: '500 KES → 1,000,000 KES goal' },
        ].map(({ icon, title, desc }) => (
          <div key={title} style={{ flex: '1 1 200px' }}>
            <div style={{ fontSize: '1.5rem' }}>{icon}</div>
            <div style={{ fontWeight: 700, marginTop: '0.25rem' }}>{title}</div>
            <div style={{ color: '#9ca3af', fontSize: '0.82rem', marginTop: '0.25rem' }}>{desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
