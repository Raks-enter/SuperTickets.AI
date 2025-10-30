import React, { useState, useEffect } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://18.117.190.231:8000';

function EmailAutomation() {
  const [automationStatus, setAutomationStatus] = useState(null);
  const [automationStats, setAutomationStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAutomationStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/mcp/email-automation-status`);
      if (response.ok) {
        const data = await response.json();
        setAutomationStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch automation status:', error);
    }
  };

  const fetchAutomationStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/mcp/email-automation-stats`);
      if (response.ok) {
        const data = await response.json();
        setAutomationStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch automation stats:', error);
    }
  };



  useEffect(() => {
    fetchAutomationStatus();
    fetchAutomationStats();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAutomationStatus();
      fetchAutomationStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="panel">
      <div className="automation-header">
        <h2>🤖 Email Automation Dashboard</h2>
        <div className="connection-status">
          <div className={`status-dot ${automationStatus?.gmail_connected ? 'connected' : 'disconnected'}`}></div>
          <span>Gmail: {automationStatus?.gmail_connected ? 'Connected' : 'Not Connected'}</span>
        </div>
      </div>

      {/* AI System Info */}
      <div className="automation-info">
        <h3>🤖 AWS Bedrock AI Email Processing</h3>
        <div className="info-grid">
          <div className="info-item">
            <strong>AI Model:</strong> Claude 3 Sonnet (AWS Bedrock)
          </div>
          <div className="info-item">
            <strong>Gmail Integration:</strong> {automationStatus?.gmail_connected ? '✅ Connected' : '❌ Not Connected'}
          </div>
          <div className="info-item">
            <strong>Processing Mode:</strong> Real AI (Not Rule-Based)
          </div>
          <div className="info-item">
            <strong>Auto-Start:</strong> Enabled with Backend
          </div>
        </div>
      </div>

      {/* AI Capabilities */}
      <div className="ai-capabilities">
        <h3>🧠 AI Capabilities</h3>
        <div className="capabilities-grid">
          <div className="capability-item">
            <span className="capability-icon">📧</span>
            <strong>Intelligent Email Analysis</strong>
            <p>Advanced understanding of customer intent and context</p>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🎯</span>
            <strong>Smart Categorization</strong>
            <p>Accurate classification beyond simple keyword matching</p>
          </div>
          <div className="capability-item">
            <span className="capability-icon">💬</span>
            <strong>Contextual Responses</strong>
            <p>Human-like responses tailored to each situation</p>
          </div>
          <div className="capability-item">
            <span className="capability-icon">🔍</span>
            <strong>AI Knowledge Search</strong>
            <p>Intelligent search and solution matching</p>
          </div>
        </div>
      </div>

      {/* Current Status */}
      {automationStatus && (
        <div className="automation-status">
          <h3>Current Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <strong>Running:</strong> {automationStatus.is_running ? 'Yes' : 'No'}
            </div>
            <div className="status-item">
              <strong>Processed Emails:</strong> {automationStatus.processed_count}
            </div>
            <div className="status-item">
              <strong>Check Interval:</strong> {automationStatus.check_interval}s
            </div>
            <div className="status-item">
              <strong>Last Check:</strong> {
                automationStatus.last_check 
                  ? new Date(automationStatus.last_check).toLocaleTimeString()
                  : 'Never'
              }
            </div>
          </div>
        </div>
      )}

      {/* Statistics */}
      {automationStats && (
        <div className="automation-stats">
          <h3>Automation Statistics (Last 24 Hours)</h3>
          
          <div className="stats-overview">
            <div className="stat-card queries">
              <div className="stat-number">{automationStats.total_processed}</div>
              <div className="stat-label">Email Queries</div>
              <div className="stat-trend">Total processed</div>
            </div>
            <div className="stat-card solutions">
              <div className="stat-number">{automationStats.automated_responses}</div>
              <div className="stat-label">Solutions Sent</div>
              <div className="stat-trend">Auto-resolved</div>
            </div>
            <div className="stat-card categories">
              <div className="stat-number">{Object.keys(automationStats.categories || {}).length}</div>
              <div className="stat-label">Categories</div>
              <div className="stat-trend">Classified</div>
            </div>
            <div className="stat-card tickets">
              <div className="stat-number">{automationStats.tickets_created}</div>
              <div className="stat-label">Tickets Created</div>
              <div className="stat-trend">Human needed</div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="breakdown-section">
            <div className="breakdown-item">
              <h4>Categories</h4>
              <div className="breakdown-list">
                {Object.entries(automationStats.categories || {}).map(([category, count]) => (
                  <div key={category} className="breakdown-row">
                    <span className="category-name">{category}</span>
                    <span className="category-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="breakdown-item">
              <h4>Priorities</h4>
              <div className="breakdown-list">
                {Object.entries(automationStats.priorities || {}).map(([priority, count]) => (
                  <div key={priority} className="breakdown-row">
                    <span className={`priority-name ${priority}`}>{priority}</span>
                    <span className="priority-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="breakdown-item">
              <h4>Sentiments</h4>
              <div className="breakdown-list">
                {Object.entries(automationStats.sentiments || {}).map(([sentiment, count]) => (
                  <div key={sentiment} className="breakdown-row">
                    <span className={`sentiment-name ${sentiment}`}>{sentiment}</span>
                    <span className="sentiment-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* How It Works */}
      <div className="automation-flow">
        <h3>🔄 How Email Automation Works</h3>
        <div className="flow-steps">
          <div className="flow-step">
            <div className="step-number">1</div>
            <div className="step-content">
              <strong>Monitor Inbox</strong>
              <p>Continuously checks Gmail for new unread emails</p>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="step-number">2</div>
            <div className="step-content">
              <strong>AI Analysis</strong>
              <p>Analyzes email content, categorizes, and determines priority</p>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="step-number">3</div>
            <div className="step-content">
              <strong>Knowledge Search</strong>
              <p>Searches knowledge base for relevant solutions</p>
            </div>
          </div>
          <div className="flow-arrow">→</div>
          <div className="flow-step">
            <div className="step-number">4</div>
            <div className="step-content">
              <strong>Smart Response</strong>
              <p>Generates and sends appropriate response or creates ticket</p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Features */}
      <div className="ai-features">
        <h3>🧠 AI Features</h3>
        <div className="features-grid">
          <div className="feature-item">
            <strong>Smart Categorization</strong>
            <p>Automatically categorizes emails: Technical, Billing, Account, General, Complaints, Feature Requests</p>
          </div>
          <div className="feature-item">
            <strong>Priority Detection</strong>
            <p>Identifies urgent issues and prioritizes responses accordingly</p>
          </div>
          <div className="feature-item">
            <strong>Sentiment Analysis</strong>
            <p>Detects customer sentiment and adjusts response tone</p>
          </div>
          <div className="feature-item">
            <strong>Solution Matching</strong>
            <p>Finds relevant solutions from knowledge base with high accuracy</p>
          </div>
          <div className="feature-item">
            <strong>Auto-Response</strong>
            <p>Generates contextual responses based on issue type and available solutions</p>
          </div>
          <div className="feature-item">
            <strong>Ticket Creation</strong>
            <p>Creates support tickets for complex issues requiring human attention</p>
          </div>
        </div>
      </div>

      <div className="refresh-info">
        <small>Auto-refreshes every 30 seconds • Last updated: {new Date().toLocaleTimeString()}</small>
        <button 
          onClick={() => {
            fetchAutomationStatus();
            fetchAutomationStats();
          }} 
          className="button small"
        >
          Refresh Now
        </button>
      </div>
    </div>
  );
}

export default EmailAutomation;