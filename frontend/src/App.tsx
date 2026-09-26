import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Search, 
  BarChart3, 
  ShieldAlert, 
  LayoutDashboard, 
  FileText, 
  Activity, 
  Cpu,
  RefreshCcw,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = "http://localhost:8000";

interface ResearchReport {
  ticker: string;
  executive_summary: string;
  fundamental_analysis: string;
  technical_analysis: string;
  conclusion: string;
  total_latency_ms: number;
  total_cost_usd: number;
  created_at: string;
  risk_assessment: Array<{
    category: string;
    level: string;
    title: string;
    description: string;
  }>;
  data_snapshot: {
    metadata: { name: string; sector: string };
    price: { current_price: number; price_change_1d_pct: number };
  };
}

export default function App() {
  const [ticker, setTicker] = useState("NVDA");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`].slice(-10));
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!ticker) return;
    
    setLoading(true);
    setReport(null);
    setLogs(["Submitting research request to AnalystPro cluster..."]);
    
    try {
      const response = await fetch(`${API_BASE}/analyze`, {
          method: 'POST',
          headers: { 
              'Content-Type': 'application/json',
              'X-API-Key': 'analyst_pro_dev_key_2026'
          },
          body: JSON.stringify({ ticker })
      });
      
      if (!response.ok) throw new Error("Failed to initialize report generation");
      
      const initData = await response.json();
      const jobId = initData.job_id;
      setLogs(initData.logs);
      
      let completed = false;
      
      while (!completed) {
        await new Promise(r => setTimeout(r, 1500)); // Poll every 1.5 seconds
        
        const pollResponse = await fetch(`${API_BASE}/jobs/${jobId}`, {
            headers: { 'X-API-Key': 'analyst_pro_dev_key_2026' }
        });
        if (!pollResponse.ok) throw new Error("Failed to fetch research status updates");
        
        const jobData = await pollResponse.json();
        setLogs(jobData.logs);
        
        if (jobData.status === "completed") {
          setReport(jobData.result);
          completed = true;
        } else if (jobData.status === "failed") {
          throw new Error(jobData.error || "Execution failed in the agent cluster.");
        }
      }
    } catch (error) {
      setLogs(prev => [...prev, `[ERROR] ${error instanceof Error ? error.message : "Network failure"}`]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="logo">
          <Activity size={24} />
          <span>AnalystPro AI</span>
        </div>

        <nav className="nav-links">
          <a href="#" className="nav-item active">
            <LayoutDashboard size={20} /> Dashboard
          </a>
          <a href="#" className="nav-item">
            <FileText size={20} /> Research Library
          </a>
          <a href="#" className="nav-item">
            <BarChart3 size={20} /> Market Pulse
          </a>
          <a href="#" className="nav-item">
            <ShieldAlert size={20} /> Risk Monitoring
          </a>
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid var(--border-color)' }}>
          <div className="section-title">
            <Cpu size={14} /> Agent Cluster Logs
          </div>
          <div className="trace-container">
            {logs.map((log, i) => (
              <div key={i} className="log-entry" style={{ opacity: 1 - i * 0.1 }}>
                {log}
              </div>
            ))}
            {loading && <div className="log-entry pulse">Processing analyst consensus...</div>}
          </div>
        </div>
      </aside>

      <main className="content">
        <header className="header">
          <div className="title-section">
            <h1>Institutional Intelligence</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Advanced cross-agent equity research platform</p>
          </div>
          
          <form className="search-container" onSubmit={handleSearch}>
            <Search size={20} style={{ margin: '0 0.5rem', color: 'var(--text-secondary)' }} />
            <input 
              className="search-input" 
              placeholder="ENTER TICKER (e.g. MSFT, AAPL)..."
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
            />
            <button className="search-button" disabled={loading}>
              {loading ? <RefreshCcw className="pulse" size={18} /> : "GENERATE"}
            </button>
          </form>
        </header>

        <AnimatePresence mode="wait">
          {report ? (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="report-view"
            >
              <div className="repo-grid">
                <div className="card summary-card">
                  <div className="section-title"><TrendingUp size={16} /> Research Thesis</div>
                  <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>
                    {report.data_snapshot.metadata.name} ({report.ticker})
                  </h2>
                  <div className="prose" dangerouslySetInnerHTML={{ __html: report.executive_summary.replace(/\n/g, '<br/>') }} />
                </div>

                <div className="card">
                  <div className="section-title"><Activity size={16} /> Market Snapshot</div>
                  <div className="metric-grid">
                    <div className="metric-item">
                      <div className="label">Current Price</div>
                      <div className="value">${report.data_snapshot.price.current_price.toLocaleString()}</div>
                    </div>
                    <div className="metric-item">
                      <div className="label">1D Change</div>
                      <div className="value" style={{ color: report.data_snapshot.price.price_change_1d_pct >= 0 ? 'var(--accent-primary)' : 'var(--accent-danger)' }}>
                        {report.data_snapshot.price.price_change_1d_pct.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card prose">
                  <div className="section-title"><BarChart3 size={16} /> Fundamental Analysis</div>
                  <div dangerouslySetInnerHTML={{ __html: report.fundamental_analysis.replace(/\n/g, '<br/>') }} />
                </div>

                <div className="card prose">
                  <div className="section-title"><TrendingUp size={16} /> Technical Analysis</div>
                  <div dangerouslySetInnerHTML={{ __html: report.technical_analysis.replace(/\n/g, '<br/>') }} />
                </div>

                <div className="card" style={{ gridColumn: 'span 2' }}>
                  <div className="section-title"><ShieldAlert size={16} /> Risk Assessment Matrix</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                    {report.risk_assessment.map((risk, i) => (
                      <div key={i} style={{ padding: '1rem', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>{risk.category}</span>
                          <span style={{ 
                            fontSize: '0.65rem', 
                            padding: '2px 6px', 
                            borderRadius: '4px',
                            background: risk.level === 'HIGH' ? 'rgba(248, 81, 73, 0.1)' : 'rgba(139, 148, 158, 0.1)',
                            color: risk.level === 'HIGH' ? 'var(--accent-danger)' : 'var(--text-secondary)'
                          }}>{risk.level}</span>
                        </div>
                        <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{risk.title}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{risk.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <footer style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                Report Generated in {report.total_latency_ms / 1000}s | Cost: ${report.total_cost_usd} | {new Date(report.created_at).toLocaleString()}
              </footer>
            </motion.div>
          ) : !loading && (
            <div style={{ height: '60vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--border-color)', borderRadius: '24px' }}>
              <TrendingUp size={48} style={{ color: var(--border-color), marginBottom: '1rem' }} />
              <h3 style={{ color: 'var(--text-secondary)' }}>Ready for Research</h3>
              <p style={{ color: 'var(--text-muted)' }}>Enter a ticker above to begin institutional-grade analysis.</p>
            </div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
