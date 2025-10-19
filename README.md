# SuperTickets.AI

An AI-powered support triage system that automatically processes emails and call transcriptions, searches for known solutions, and either provides automated responses or creates support tickets.

## 🚀 Features

- **Email Processing**: Receives and analyzes support emails
- **Call Transcription Analysis**: Processes call transcriptions for issue identification
- **AI-Powered Triage**: Uses AWS Bedrock (GPT-4o-mini) for intelligent issue analysis
- **Knowledge Base Search**: Vector similarity search in Supabase for known solutions
- **Automated Responses**: Sends Gmail replies for resolved issues
- **Ticket Creation**: Raises tickets via SuperOps GraphQL API for unresolved issues
- **Memory Logging**: Tracks all interactions in Supabase
- **Meeting Scheduling**: Optional Google Calendar integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kiro Agents   │───▶│  FastAPI MCP     │───▶│  External APIs  │
│                 │    │  Microservice    │    │                 │
│ • Email Agent   │    │                  │    │ • AWS Bedrock   │
│ • Call Agent    │    │ • KB Lookup      │    │ • Supabase      │
└─────────────────┘    │ • Ticket Creation│    │ • Gmail API     │
                       │ • Email Sending  │    │ • SuperOps API  │
                       │ • Memory Logging │    │ • Google Cal    │
                       └──────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **AI Framework**: Kiro Agents
- **Backend**: FastAPI with MCP (Model Context Protocol)
- **AI Model**: AWS Bedrock (GPT-4o-mini)
- **Database**: Supabase (PostgreSQL + Vector embeddings)
- **Email**: Gmail API
- **Ticketing**: SuperOps GraphQL API
- **Calendar**: Google Calendar API
- **Deployment**: Docker + AWS

## 📋 Prerequisites

- Python 3.9+
- Docker & Docker Compose
- AWS Account with Bedrock access
- Supabase project
- Google Cloud Console project (for Gmail & Calendar APIs)
- SuperOps account with API access

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/SuperTickets.AI.git
cd SuperTickets.AI
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your credentials:

```bash
# AWS Bedrock
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Gmail API
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json

# SuperOps API
SUPEROPS_API_URL=https://api.superops.com/graphql
SUPEROPS_API_KEY=your_superops_api_key

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials/calendar_credentials.json
```

### 3. Run with Docker

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Or manually:**
```bash
docker-compose up -d
```

This will start:
- **Backend API** at `http://localhost:8000`
- **Web Dashboard** at `http://localhost:3000`
- **Grafana** at `http://localhost:3001`

### 4. Access the Dashboard

Open `http://localhost:3000` to access the web interface with:
- **Dashboard** - Real-time statistics from your database
- **System Status** - Backend health monitoring
- **Knowledge Base** - Search functionality testing
- **Create Tickets** - Manual ticket creation
- **Send Emails** - Email testing interface
- **Email Monitor** - Gmail integration status and activity

### 5. Connect Your Company Email

To enable automatic email processing:

1. **Setup Gmail API** (see [Email Integration Guide](docs/EMAIL_INTEGRATION.md))
2. **Place credentials** in `./credentials/gmail_credentials.json`
3. **Restart services** and authorize access
4. **Monitor integration** in the Email Monitor tab

### 5. Configure Kiro MCP

The MCP service will be available at `http://localhost:8000`. Kiro agents will automatically connect using the configuration in `.kiro/config/mcp.json`.

## 📁 Project Structure

```
SuperTickets.AI/
├── .kiro/
│   ├── specs/           # Product specifications
│   ├── agents/          # Kiro agent configurations
│   ├── config/          # MCP configuration
│   └── kb/              # Knowledge base
├── mcp_service/         # FastAPI MCP microservice
│   ├── routes/          # API endpoints
│   └── utils/           # Utility modules
├── tests/               # Test suite
├── credentials/         # API credentials (gitignored)
└── docs/                # Documentation
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_kb_lookup.py -v

# Run with coverage
pytest --cov=mcp_service tests/
```

## 🚢 Deployment

### AWS Deployment

1. **Setup Bedrock Access**:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

2. **Deploy to ECS**:
   ```bash
   docker build -t supertickets-ai .
   # Push to ECR and deploy to ECS
   ```

3. **Configure Load Balancer** for the MCP service endpoint

## 📖 API Documentation

Once running, visit:
- FastAPI Docs: `http://localhost:8000/docs`
- MCP Endpoints: `http://localhost:8000/mcp/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Create a GitHub issue
- Check the [documentation](./docs/)
- Review the knowledge base in `.kiro/kb/`