# SuperTickets.AI - Technical Specifications

## Technology Stack

### Core Framework
- **Kiro Agents**: AI agent orchestration and workflow management
- **FastAPI**: High-performance async web framework for MCP service
- **Python 3.9+**: Primary development language

### AI and ML
- **AWS Bedrock**: Managed AI service
  - Model: GPT-4o-mini
  - Region: us-east-1
  - Max tokens: 4096
- **Vector Embeddings**: text-embedding-ada-002 compatible
- **Similarity Search**: Cosine similarity with 0.8 threshold

### Database and Storage
- **Supabase**: 
  - PostgreSQL with pgvector extension
  - Vector similarity search
  - Real-time subscriptions
  - Row-level security

### External APIs
- **Gmail API v1**: Email processing and sending
- **Google Calendar API v3**: Meeting scheduling
- **SuperOps GraphQL API**: Ticket management
- **AWS Bedrock Runtime**: AI model inference

## Development Environment

### Dependencies
```python
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
supabase==2.0.0
google-api-python-client==2.108.0
google-auth==2.23.4
boto3==1.34.0
openai==1.3.0  # For embeddings compatibility
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Docker Configuration
- **Base Image**: python:3.9-slim
- **Port**: 8000 (FastAPI service)
- **Health Check**: `/health` endpoint
- **Multi-stage build** for production optimization

## API Specifications

### MCP Endpoints
```
POST /mcp/kb_lookup
POST /mcp/create_ticket  
POST /mcp/send_email
POST /mcp/log_memory
POST /mcp/schedule_meeting
GET /health
GET /docs
```

### Request/Response Schemas
```python
# KB Lookup Request
{
  "query": "string",
  "threshold": 0.8,
  "limit": 5
}

# Ticket Creation Request
{
  "title": "string",
  "description": "string", 
  "priority": "high|medium|low",
  "category": "string",
  "customer_email": "string"
}

# Email Response Request
{
  "to": "string",
  "subject": "string",
  "body": "string",
  "thread_id": "string"
}
```

## Database Schema

### Supabase Tables
```sql
-- Support interactions log
CREATE TABLE support_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_type VARCHAR(50) NOT NULL,
  customer_email VARCHAR(255) NOT NULL,
  issue_description TEXT NOT NULL,
  ai_analysis JSONB,
  resolution_type VARCHAR(50),
  ticket_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge base entries
CREATE TABLE knowledge_base (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  category VARCHAR(100),
  tags TEXT[],
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create vector similarity index
CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

## Configuration Files

### Environment Variables
```bash
# AWS Bedrock
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# Gmail API
GMAIL_CREDENTIALS_PATH=./credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./credentials/gmail_token.json

# SuperOps
SUPEROPS_API_URL=https://api.superops.com/graphql
SUPEROPS_API_KEY=

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials/calendar_credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=./credentials/calendar_token.json

# Application
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

## Performance Requirements

### Response Times
- KB lookup: < 2 seconds
- Ticket creation: < 5 seconds  
- Email sending: < 3 seconds
- AI analysis: < 10 seconds

### Scalability
- Concurrent requests: 100+
- Daily email volume: 10,000+
- Knowledge base size: 100,000+ entries

### Reliability
- Uptime: 99.9%
- Error rate: < 1%
- Retry mechanisms for all external APIs

## Security Implementation

### Authentication
- OAuth 2.0 for Google services
- API keys for SuperOps and Supabase
- AWS IAM roles for Bedrock access

### Data Protection
- Encryption at rest (Supabase)
- TLS 1.3 for all API communications
- PII anonymization in logs
- Credential rotation every 90 days

### Access Control
- Role-based permissions
- API rate limiting
- Request validation and sanitization