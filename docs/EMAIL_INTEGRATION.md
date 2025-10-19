# Email Integration Guide

## How Company Email Connects to SuperTickets.AI

Your company's email system integrates with the AI agent through **Gmail API**. Here's how it works:

## 🔧 **Setup Process**

### 1. **Google Cloud Console Setup**
```bash
# 1. Go to Google Cloud Console (console.cloud.google.com)
# 2. Create a new project or select existing one
# 3. Enable Gmail API
# 4. Create OAuth 2.0 credentials
# 5. Download credentials.json file
```

### 2. **Place Credentials**
```bash
# Put the downloaded file here:
./credentials/gmail_credentials.json
```

### 3. **Environment Configuration**
```bash
# In your .env file:
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json
```

## 📧 **How Email Integration Works**

### **Incoming Emails (Customer → AI)**
1. **Email Monitoring**: AI agent monitors your company inbox
2. **Auto-Processing**: New emails are automatically analyzed
3. **KB Search**: AI searches knowledge base for solutions
4. **Smart Response**: Either auto-replies or creates ticket

### **Outgoing Emails (AI → Customer)**
1. **Auto-Responses**: AI sends solutions from knowledge base
2. **Ticket Confirmations**: Sends ticket creation confirmations
3. **Follow-ups**: Scheduled follow-up emails
4. **Threading**: Maintains email conversation threads

## 🔄 **Email Flow Example**

```
Customer Email → Gmail API → AI Analysis → Knowledge Base Search
                                    ↓
                            Solution Found?
                                    ↓
                    YES: Auto-Reply    NO: Create Ticket
                                           ↓
                                    Send Confirmation
```

## 🛠 **Technical Implementation**

### **Email Monitoring Service**
```python
# This runs continuously to check for new emails
async def monitor_emails():
    gmail_client = GmailClient()
    
    # Get unread emails
    messages = await gmail_client.get_messages(
        query="is:unread label:inbox",
        max_results=50
    )
    
    for message in messages:
        # Process each email with AI
        await process_customer_email(message)
```

### **AI Email Processing**
```python
async def process_customer_email(email_message):
    # 1. Extract issue from email
    issue_text = email_message['body']
    customer_email = extract_sender_email(email_message['sender'])
    
    # 2. Search knowledge base
    kb_results = await search_knowledge_base(issue_text)
    
    # 3. Decide action
    if kb_results and kb_results[0]['similarity'] > 0.85:
        # Send auto-response
        await send_solution_email(customer_email, kb_results[0])
    else:
        # Create ticket
        ticket = await create_support_ticket(email_message)
        await send_ticket_confirmation(customer_email, ticket)
```

## 📋 **Required Permissions**

Your Gmail API needs these scopes:
- `gmail.send` - Send emails as your company
- `gmail.readonly` - Read incoming emails
- `gmail.modify` - Mark emails as read, add labels

## 🔐 **Security & Authentication**

### **OAuth 2.0 Flow**
1. **First Run**: Opens browser for company admin to authorize
2. **Token Storage**: Saves refresh token for future use
3. **Auto-Refresh**: Automatically renews expired tokens
4. **Secure Storage**: Tokens stored in `./credentials/gmail_token.json`

### **Company Email Account**
- Use your **company's Gmail/Google Workspace account**
- The AI will send emails **from your company domain**
- Customers see replies from `support@yourcompany.com`

## 📊 **Email Analytics**

The dashboard tracks:
- **Emails Processed**: Total incoming emails handled
- **Auto-Responses**: Solutions sent automatically
- **Tickets Created**: Issues that needed human attention
- **Response Time**: How quickly AI responds

## 🚀 **Getting Started**

### **Step 1: Enable Gmail API**
```bash
# 1. Go to console.cloud.google.com
# 2. APIs & Services → Library
# 3. Search "Gmail API" → Enable
```

### **Step 2: Create Credentials**
```bash
# 1. APIs & Services → Credentials
# 2. Create Credentials → OAuth 2.0 Client ID
# 3. Application Type: Desktop Application
# 4. Download JSON file
```

### **Step 3: First Authorization**
```bash
# Run the service - it will open browser for authorization
docker-compose up -d

# Check logs for authorization URL
docker logs supertickets-ai-mcp
```

### **Step 4: Test Integration**
```bash
# Send test email to your company address
# Check dashboard for processing activity
# Verify auto-response or ticket creation
```

## 🔧 **Troubleshooting**

### **Common Issues**

**"Credentials not found"**
```bash
# Ensure file exists and path is correct
ls -la ./credentials/gmail_credentials.json
```

**"Authentication failed"**
```bash
# Delete token file and re-authorize
rm ./credentials/gmail_token.json
docker-compose restart supertickets-ai
```

**"Permission denied"**
```bash
# Check OAuth scopes in Google Cloud Console
# Ensure Gmail API is enabled
```

## 📞 **Support**

If you need help with email integration:
1. Check the logs: `docker logs supertickets-ai-mcp`
2. Verify credentials file exists and is valid JSON
3. Ensure Gmail API is enabled in Google Cloud Console
4. Test with a simple email first

Your company email will be fully integrated with the AI agent, providing seamless customer support automation!