import React, { useState, useEffect } from 'react';
import { Activity, Shield, TrendingUp, AlertOctagon, Play } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const App = () => {
  const [stats, setStats] = useState({
    balance: 0,
    equity: 0,
    dailyPnL: 0,
    drawdown: 0,
    is_trained: false
  });
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('trading_api_url') || '');

  const getBaseUrl = () => apiUrl || '';

  const fetchStats = async () => {
    try {
      const response = await fetch(`${getBaseUrl()}/api/stats`);
      const data = await response.json();
      setStats(data);
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleStartTrading = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${getBaseUrl()}/api/start`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'STARTED' || data.status === 'ALREADY_RUNNING') {
        setIsRunning(true);
      }
    } catch (e) {
      alert("Failed to start bot");
    }
    setIsLoading(false);
  };

  const handleStopTrading = async () => {
    try {
      await fetch(`${getBaseUrl()}/api/stop`, { method: 'POST' });
      setIsRunning(false);
      alert("CRITICAL: Bot Halted.");
    } catch (e) {
      alert("Failed to stop bot");
    }
  };

  const handleDeposit = async () => {
    const phone = prompt("Enter phone number (Format: 2547XXXXXXXX):", "254746957621");
    const amount = prompt("Enter amount to deposit (KES):", "1000");
    
    if (phone && amount) {
      setIsLoading(true);
      try {
        const response = await fetch(`${getBaseUrl()}/api/deposit/mpesa`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone, amount })
        });
        const data = await response.json();
        if (data.status === 'SUCCESS') {
          alert(`STK Push sent to ${phone}. Approve on your phone to credit your account (Pochi/Till mode).`);
        } else {
          alert(`Error: ${data.message}`);
        }
      } catch (e) {
        alert("Failed to initiate deposit");
      }
      setIsLoading(false);
    }
  };

  const mockChartData = Array.from({ length: 20 }, (_, i) => ({
    time: i,
    price: 1.0850 + Math.random() * 0.0050
  }));

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>AI TRADER PRO (KENYA)</h1>
          <p className="stat-label">{isRunning ? "System Operational • Live Feed" : "System Standby"}</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="glass-card" onClick={handleDeposit} disabled={isLoading} style={{ 
            color: '#10b981', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, border: '1px solid #10b981', opacity: isLoading ? 0.5 : 1
          }}>
            Deposit M-Pesa
          </button>
          <div className="glass-card" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color={isRunning ? "#10b981" : "#9ca3af"} />
            <span style={{ fontWeight: 600 }}>{isRunning ? "Active" : "Halted"}</span>
          </div>
        </div>
      </header>

      <div className="glass-card" style={{ margin: '1rem 2rem', padding: '1rem', background: 'rgba(255, 255, 255, 0.05)' }}>
        <p className="stat-label" style={{ marginBottom: '0.5rem' }}>Backend Connection (Tunnel URL)</p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <input 
            type="text" 
            placeholder="e.g. https://xyz.ngrok.io" 
            value={apiUrl}
            onChange={(e) => {
              setApiUrl(e.target.value);
              localStorage.setItem('trading_api_url', e.target.value);
            }}
            className="glass-card"
            style={{ flex: 1, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', padding: '0.5rem' }}
          />
          {!apiUrl && <span style={{ color: '#ef4444', fontSize: '0.8rem', alignSelf: 'center' }}>Enter tunnel URL to connect</span>}
        </div>
      </div>

      <div className="stats-grid">
        <div className="glass-card">
          <div className="stat-label">Total Balance</div>
          <div className="stat-value">${stats.balance.toLocaleString()}</div>
        </div>
        <div className="glass-card">
          <div className="stat-label">Daily P&L</div>
          <div className="stat-value profit-text">+${stats.dailyPnL}</div>
        </div>
        <div className="glass-card">
          <div className="stat-label">System State</div>
          <div className="stat-value" style={{ color: stats.is_trained ? '#3b82f6' : '#f59e0b', fontSize: '1.1rem' }}>
            {stats.is_trained ? "AI TRAINED" : "AI UNTRAINED"}
          </div>
        </div>
        <div className="glass-card">
          <div className="stat-label">Risk Level</div>
          <div className="stat-value" style={{ color: '#ef4444' }}>CAUTIOUS</div>
        </div>
      </div>

      <div className="main-content">
        <section className="chart-section glass-card">
          <h3 style={{ marginTop: 0 }}>Market Analysis: EUR/USD</h3>
          <div style={{ height: '300px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockChartData}>
                <XAxis dataKey="time" hide />
                <YAxis domain={['auto', 'auto']} hide />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                  itemStyle={{ color: '#f3f4f6' }}
                />
                <Line type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="controls-section">
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ marginTop: 0 }}>System Controls</h3>
            
            {!isRunning ? (
              <button className="btn-start" onClick={handleStartTrading} disabled={isLoading} style={{
                background: '#10b981', color: 'white', padding: '1rem', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
              }}>
                <Play size={20} fill="white" /> START TRADING
              </button>
            ) : (
              <button className="btn-stop" onClick={handleStopTrading} style={{
                background: '#ef4444', color: 'white', padding: '1rem', borderRadius: '12px', border: 'none', cursor: 'pointer', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
              }}>
                <AlertOctagon size={20} /> STOP ALL TRADING
              </button>
            )}
            
            <p className="stat-label" style={{ textAlign: 'center' }}>
              {stats.is_trained ? "System ready for high-probability signals." : "Awaiting model training for live signals."}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default App;
