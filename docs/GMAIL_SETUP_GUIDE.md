# Gmail API Setup Guide for SuperTickets.AI

This guide will walk you through connecting your company's Gmail account to SuperTickets.AI for automatic email processing and responses.

## 🎯 **What You'll Achieve**

After setup, your system will:
- **Read incoming emails** from your company Gmail
- **Parse and analyze** customer issues automatically  
- **Search your knowledge base** for solutions
- **Send automatic responses** or create tickets
- **Track all email interactions** in the dashboard

## 📋 **Prerequisites**

- Company Gmail or Google Workspace account
- Admin access to Google Cloud Console
- SuperTickets.AI backend running

## 🚀 **Step-by-Step Setup**

### **Step 1: Google Cloud Console Setup**

1. **Go to Google Cloud Console**
   ```
   https://console.cloud.google.com
   ```

2. **Create or Select Project**
   - Click "Select a project" → "New Project"
   - Name: `SuperTickets-AI-Email`
   - Click "Create"

3. **Enable Gmail API**
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Gmail API" → "Enable"

### **Step 2: Create OAuth Credentials**

1. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (for Google Workspace, choose "Internal")
   - Fill required fields:
     - App name: `SuperTickets.AI`
     - User support email: Your company email
     - Developer contact: Your company email
   - Click "Save and Continue"
   - Add scopes: Click "Add or Remove Scopes"
     - Add: `https://www.googleapis.com/auth/gmail.send`
     - Add: `https://www.googleapis.com/auth/gmail.readonly`
     - Add: `https://www.googleapis.com/auth/gmail.modify`
   - Click "Save and Continue"

2. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Desktop application"
   - Name: `SuperTickets-AI-Gmail`
   - Click "Create"

3. **Download Credentials**
   - Click the download button (⬇️) next to your new credential
   - Save the JSON file as `gmail_credentials.json`

### **Step 3: Install Credentials**

1. **Create Credentials Directory**
   ```bash
   mkdir -p credentials
   ```

2. **Place Credentials File**
   ```bash
   # Move your downloaded file to:
   ./credentials/gmail_credentials.json
   ```

3. **Set Environment Variables**
   ```bash
   # Add to your .env file:
   GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
   GMAIL_TOKEN_PATH=./credentials/gmail_token.json
   ```

### **Step 4: First Authorization**

1. **Start the Backend**
   ```bash
   docker-compose up -d
   ```

2. **Check Logs for Authorization URL**
   ```bash
   docker logs supertickets-ai-mcp
   ```
   
   Look for a message like:
   ```
   Please visit this URL to authorize this application:
   https://accounts.google.com/oauth2/auth?...
   ```

3. **Complete Authorization**
   - Copy the URL and open in your browser
   - Sign in with your **company Gmail account**
   - Grant all requested permissions
   - You'll see "The authentication flow has completed"

4. **Verify Token Creation**
   ```bash
   ls -la ./credentials/
   # Should show both files:
   # gmail_credentials.json
   # gmail_token.json
   ```

### **Step 5: Test Integration**

1. **Check Gmail Status**
   ```bash
   curl http://localhost:8000/mcp/check-gmail-status
   ```
   
   Should return:
   ```json
   {
     "connected": true,
     "email_address": "support@yourcompany.com",
     "stats": {...}
   }
   ```

2. **Test Reading Emails**
   ```bash
   curl -X GET "http://localhost:8000/mcp/unread_emails?max_results=5"
   ```

3. **Test Sending Email**
   ```bash
   curl -X POST http://localhost:8000/mcp/send_email \
     -H "Content-Type: application/json" \
     -d '{
       "to": "test@yourcompany.com",
       "subject": "Test from SuperTickets.AI",
       "body": "Integration test successful!"
     }'
   ```

## 📧 **How Email Processing Works**

### **Incoming Email Flow**
```
Customer Email → Gmail API → AI Analysis → Knowledge Base Search
                                    ↓
                            Solution Found?
                                    ↓
                    YES: Auto-Reply    NO: Create Ticket
                                           ↓
                                    Send Confirmation
```

### **Email Parsing Features**
The AI automatically extracts:
- **Customer Information**: Name, email, company
- **Issue Category**: Technical, billing, account, etc.
- **Priority Level**: High, medium, low
- **Key Data**: Order numbers, phone numbers, error messages
- **Suggested Actions**: KB search, escalation, etc.

## 🔧 **Available API Endpoints**

### **Reading Emails**
```bash
# Get unread emails
GET /mcp/unread_emails?max_results=50

# Get recent emails (last 24 hours)
GET /mcp/recent_emails?hours=24&max_results=100

# Search emails with custom query
POST /mcp/read_emails
{
  "query": "is:unread label:inbox",
  "max_results": 50,
  "parse_content": true
}
```

### **Email Management**
```bash
# Parse specific email
POST /mcp/parse_email/{message_id}

# Mark email as read
POST /mcp/mark_as_read/{message_id}

# Add label to email
POST /mcp/add_label/{message_id}?label_name=processed
```

### **Sending Emails**
```bash
# Send email
POST /mcp/send_email
{
  "to": "customer@example.com",
  "subject": "Re: Your Support Request",
  "body": "Thank you for contacting us...",
  "thread_id": "optional_gmail_thread_id"
}
```

## 🎛️ **Frontend Dashboard**

The web dashboard provides:

### **Email Inbox Tab**
- View unread, recent, and all emails
- Real-time email parsing and analysis
- Priority and category indicators
- Mark as read, add labels
- Detailed AI analysis view

### **Email Monitor Tab**
- Gmail connection status
- Email processing statistics
- Recent email activity
- Integration health monitoring

## 🔐 **Security & Permissions**

### **Required Gmail Scopes**
- `gmail.send` - Send emails as your company
- `gmail.readonly` - Read incoming emails  
- `gmail.modify` - Mark emails as read, add labels

### **Token Management**
- **Refresh tokens** are stored securely in `./credentials/gmail_token.json`
- **Automatic renewal** when tokens expire
- **No password storage** - uses OAuth 2.0 flow

### **Company Email Account**
- Use your **company's official Gmail/Google Workspace account**
- AI will send emails **from your company domain**
- Customers see replies from `support@yourcompany.com`

## 🚨 **Troubleshooting**

### **"Credentials not found"**
```bash
# Check file exists and has correct permissions
ls -la ./credentials/gmail_credentials.json
chmod 600 ./credentials/gmail_credentials.json
```

### **"Authentication failed"**
```bash
# Delete token and re-authorize
rm ./credentials/gmail_token.json
docker-compose restart supertickets-ai
# Follow authorization URL in logs
```

### **"Permission denied"**
- Verify Gmail API is enabled in Google Cloud Console
- Check OAuth consent screen is configured
- Ensure all required scopes are added

### **"Quota exceeded"**
- Gmail API has daily limits
- For high volume, request quota increase in Google Cloud Console
- Consider implementing rate limiting

### **"Invalid grant"**
```bash
# Token may be expired, refresh authorization
rm ./credentials/gmail_token.json
docker-compose restart supertickets-ai
```

## 📊 **Monitoring & Analytics**

### **Dashboard Metrics**
- **Emails Processed**: Total incoming emails handled
- **Auto-Responses**: Solutions sent automatically  
- **Tickets Created**: Issues requiring human attention
- **Response Time**: Average AI response time
- **Success Rate**: Percentage of issues resolved automatically

### **Email Labels**
The system automatically adds Gmail labels:
- `supertickets-processed` - Email has been analyzed
- `supertickets-responded` - Auto-response sent
- `supertickets-ticket-created` - Support ticket created
- `supertickets-high-priority` - High priority issue

## 🔄 **Maintenance**

### **Regular Tasks**
- Monitor Gmail API quota usage
- Review auto-response accuracy
- Update knowledge base content
- Check token expiration (auto-renewed)

### **Backup**
```bash
# Backup credentials (encrypted storage recommended)
cp ./credentials/gmail_credentials.json ./backups/
cp ./credentials/gmail_token.json ./backups/
```

## 📞 **Support**

If you encounter issues:

1. **Check the logs**:
   ```bash
   docker logs supertickets-ai-mcp
   ```

2. **Verify credentials**:
   ```bash
   cat ./credentials/gmail_credentials.json | jq .
   ```

3. **Test connection**:
   ```bash
   curl http://localhost:8000/mcp/check-gmail-status
   ```

4. **Common solutions**:
   - Restart the service: `docker-compose restart`
   - Re-authorize: Delete token file and restart
   - Check Google Cloud Console for API limits

Your company email is now fully integrated with SuperTickets.AI! 🎉

The AI will automatically process incoming customer emails, provide instant solutions from your knowledge base, and create tickets for complex issues that need human attention.