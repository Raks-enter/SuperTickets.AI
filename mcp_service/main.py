"""
SuperTickets.AI - FastAPI MCP Microservice
Main application entry point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from .routes import kb_lookup, create_ticket, send_email, read_email, log_memory, analytics, email_automation_control
# from .routes import schedule_meeting  # Temporarily disabled - missing pytz
from .utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting SuperTickets.AI MCP Service")
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        # Initialize connections
        try:
            supabase = get_supabase_client()
            logger.info("✅ Supabase connection established")
        except Exception as e:
            logger.warning(f"⚠️ Supabase connection failed: {e}")
            logger.info("Service will start without Supabase (some features may not work)")
    else:
        logger.warning("⚠️ Supabase credentials not found in environment variables")
        logger.info("Service will start without Supabase (some features may not work)")
    
    # Auto-start email automation service
    try:
        from .services.email_automation_service import email_automation_service
        
        # Initialize and start the automation service
        if await email_automation_service.initialize():
            # Start monitoring in background
            import asyncio
            asyncio.create_task(email_automation_service.start_monitoring())
            logger.info("🤖 Email automation service started automatically")
        else:
            logger.warning("⚠️ Email automation service failed to initialize")
    except Exception as e:
        logger.error(f"❌ Failed to start email automation: {e}")
    
    yield
    
    # Stop automation service on shutdown
    try:
        from .services.email_automation_service import email_automation_service
        await email_automation_service.stop_monitoring()
        logger.info("🤖 Email automation service stopped")
    except Exception as e:
        logger.error(f"Error stopping automation service: {e}")
    
    logger.info("Shutting down SuperTickets.AI MCP Service")

# Create FastAPI app
app = FastAPI(
    title="SuperTickets.AI MCP Service",
    description="AI-powered support triage system with MCP endpoints",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "supertickets-ai-mcp",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "SuperTickets.AI MCP Service",
        "version": "1.0.0",
        "description": "AI-powered support triage system",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "mcp": "/mcp/*"
        }
    }

# Include MCP route modules
app.include_router(kb_lookup.router, prefix="/mcp", tags=["Knowledge Base"])
app.include_router(create_ticket.router, prefix="/mcp", tags=["Ticketing"])
app.include_router(send_email.router, prefix="/mcp", tags=["Email"])
app.include_router(read_email.router, prefix="/mcp", tags=["Email Reading"])
app.include_router(log_memory.router, prefix="/mcp", tags=["Memory"])
# app.include_router(schedule_meeting.router, prefix="/mcp", tags=["Calendar"])  # Temporarily disabled
app.include_router(analytics.router, prefix="", tags=["Analytics"])
app.include_router(email_automation_control.router, prefix="/mcp", tags=["Email Automation"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Request ID middleware
@app.middleware("http")
async def add_request_id(request, call_next):
    """Add request ID for tracking"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )