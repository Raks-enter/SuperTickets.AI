import React, { useState, useEffect } from 'react';
import './EmailInbox.css';

const EmailInbox = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [filter, setFilter] = useState('unread');
  const [error, setError] = useState('');

  const fetchEmails = async (filterType = 'unread') => {
    setLoading(true);
    setError('');
    
    try {
      let endpoint = '';
      
      switch (filterType) {
        case 'unread':
          endpoint = '/mcp/unread_emails?max_results=50';
          break;
        case 'recent':
          endpoint = '/mcp/recent_emails?hours=24&max_results=100';
          break;
        case 'all':
          endpoint = '/mcp/read_emails';
          break;
        default:
          endpoint = '/mcp/unread_emails?max_results=50';
      }
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: filterType === 'all' ? 'POST' : 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        body: filterType === 'all' ? JSON.stringify({
          query: "label:inbox",
          max_results: 100,
          parse_content: true
        }) : undefined
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setEmails(data.messages || []);
      
    } catch (err) {
      console.error('Error fetching emails:', err);
      setError(`Failed to fetch emails: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      const response = await fetch(`http://localhost:8000/mcp/mark_as_read/${messageId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        // Update local state
        setEmails(emails.map(email => 
          email.id === messageId 
            ? { ...email, is_unread: false }
            : email
        ));
      }
    } catch (err) {
      console.error('Error marking email as read:', err);
    }
  };

  const addLabel = async (messageId, labelName) => {
    try {
      const response = await fetch(`http://localhost:8000/mcp/add_label/${messageId}?label_name=${labelName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        console.log(`Label "${labelName}" added to email ${messageId}`);
      }
    } catch (err) {
      console.error('Error adding label:', err);
    }
  };

  const parseEmail = async (messageId) => {
    try {
      const response = await fetch(`http://localhost:8000/mcp/parse_email/${messageId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const parseData = await response.json();
        
        // Update the email with parsed content
        setEmails(emails.map(email => 
          email.id === messageId 
            ? { ...email, parsed_content: parseData }
            : email
        ));
        
        return parseData;
      }
    } catch (err) {
      console.error('Error parsing email:', err);
    }
  };

  useEffect(() => {
    fetchEmails(filter);
  }, [filter]);

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#ff4444';
      case 'medium': return '#ffaa00';
      case 'low': return '#44aa44';
      default: return '#666666';
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      billing: '#e74c3c',
      technical: '#3498db',
      account: '#9b59b6',
      product: '#2ecc71',
      shipping: '#f39c12',
      cancellation: '#e67e22',
      general: '#95a5a6'
    };
    return colors[category] || colors.general;
  };

  return (
    <div className="email-inbox">
      <div className="inbox-header">
        <h2>📧 Email Inbox</h2>
        
        <div className="inbox-controls">
          <div className="filter-buttons">
            <button 
              className={filter === 'unread' ? 'active' : ''}
              onClick={() => setFilter('unread')}
            >
              Unread ({emails.filter(e => e.is_unread).length})
            </button>
            <button 
              className={filter === 'recent' ? 'active' : ''}
              onClick={() => setFilter('recent')}
            >
              Recent (24h)
            </button>
            <button 
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              All Emails
            </button>
          </div>
          
          <button 
            className="refresh-btn"
            onClick={() => fetchEmails(filter)}
            disabled={loading}
          >
            {loading ? '🔄' : '↻'} Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <div className="inbox-content">
        <div className="email-list">
          {loading ? (
            <div className="loading">Loading emails...</div>
          ) : emails.length === 0 ? (
            <div className="no-emails">
              📭 No emails found for the selected filter
            </div>
          ) : (
            emails.map(email => (
              <div 
                key={email.id}
                className={`email-item ${email.is_unread ? 'unread' : 'read'} ${selectedEmail?.id === email.id ? 'selected' : ''}`}
                onClick={() => setSelectedEmail(email)}
              >
                <div className="email-header">
                  <div className="sender">
                    <strong>{email.sender}</strong>
                    {email.is_unread && <span className="unread-indicator">●</span>}
                  </div>
                  <div className="date">{formatDate(email.date)}</div>
                </div>
                
                <div className="subject">{email.subject}</div>
                <div className="snippet">{email.snippet}</div>
                
                {email.parsed_content && (
                  <div className="parsed-info">
                    <span 
                      className="priority-badge"
                      style={{ backgroundColor: getPriorityColor(email.parsed_content.priority_level) }}
                    >
                      {email.parsed_content.priority_level}
                    </span>
                    <span 
                      className="category-badge"
                      style={{ backgroundColor: getCategoryColor(email.parsed_content.issue_category) }}
                    >
                      {email.parsed_content.issue_category}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {selectedEmail && (
          <div className="email-detail">
            <div className="detail-header">
              <h3>{selectedEmail.subject}</h3>
              <div className="email-actions">
                {selectedEmail.is_unread && (
                  <button 
                    className="action-btn"
                    onClick={() => markAsRead(selectedEmail.id)}
                  >
                    Mark as Read
                  </button>
                )}
                <button 
                  className="action-btn"
                  onClick={() => parseEmail(selectedEmail.id)}
                >
                  Parse Email
                </button>
                <button 
                  className="action-btn"
                  onClick={() => addLabel(selectedEmail.id, 'processed')}
                >
                  Add Label
                </button>
              </div>
            </div>
            
            <div className="email-meta">
              <p><strong>From:</strong> {selectedEmail.sender}</p>
              <p><strong>Date:</strong> {formatDate(selectedEmail.date)}</p>
              <p><strong>Thread ID:</strong> {selectedEmail.thread_id}</p>
            </div>
            
            <div className="email-body">
              <h4>Email Content:</h4>
              <pre>{selectedEmail.body}</pre>
            </div>
            
            {selectedEmail.parsed_content && (
              <div className="parsed-content">
                <h4>AI Analysis:</h4>
                
                <div className="analysis-section">
                  <h5>Customer Information:</h5>
                  <ul>
                    <li><strong>Name:</strong> {selectedEmail.parsed_content.customer_info?.name}</li>
                    <li><strong>Email:</strong> {selectedEmail.parsed_content.customer_info?.email}</li>
                    <li><strong>Company:</strong> {selectedEmail.parsed_content.customer_info?.company}</li>
                  </ul>
                </div>
                
                <div className="analysis-section">
                  <h5>Issue Analysis:</h5>
                  <p><strong>Summary:</strong> {selectedEmail.parsed_content.issue_summary}</p>
                  <p>
                    <strong>Category:</strong> 
                    <span 
                      className="category-badge inline"
                      style={{ backgroundColor: getCategoryColor(selectedEmail.parsed_content.issue_category) }}
                    >
                      {selectedEmail.parsed_content.issue_category}
                    </span>
                  </p>
                  <p>
                    <strong>Priority:</strong> 
                    <span 
                      className="priority-badge inline"
                      style={{ backgroundColor: getPriorityColor(selectedEmail.parsed_content.priority_level) }}
                    >
                      {selectedEmail.parsed_content.priority_level}
                    </span>
                  </p>
                </div>
                
                {selectedEmail.parsed_content.extracted_data && (
                  <div className="analysis-section">
                    <h5>Extracted Data:</h5>
                    {Object.entries(selectedEmail.parsed_content.extracted_data).map(([key, value]) => (
                      value && value.length > 0 && (
                        <p key={key}>
                          <strong>{key.replace('_', ' ').toUpperCase()}:</strong> {Array.isArray(value) ? value.join(', ') : value}
                        </p>
                      )
                    ))}
                  </div>
                )}
                
                {selectedEmail.parsed_content.suggested_actions && (
                  <div className="analysis-section">
                    <h5>Suggested Actions:</h5>
                    <ul>
                      {selectedEmail.parsed_content.suggested_actions.map((action, index) => (
                        <li key={index}>{action.replace('_', ' ').toUpperCase()}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailInbox;