"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Union
import logging
import sys

# Import configuration
try:
    from src.utils.config import settings
except Exception as e:
    import sys
    print(f"FATAL: Failed to import settings: {e}", file=sys.stderr)
    sys.exit(1)

from src.utils.logger import setup_logging
from src.utils.error_handler import error_handler, TravelAssistantException
from src.middleware.rate_limiter import RateLimiterMiddleware

# Import models
from src.models.response_models import ErrorResponse, PDFResponse, ChatResponse, ExplainResponse

# Import routes (will be created in Phase 4)
# from src.routes import chat, plan, edit, explain, pdf, health

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file or "app.log",
    log_dir="logs"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    
    # Initialize services here
    # - Connect to MCP servers
    # - Initialize RAG vector store
    # - Preload common cities (optional)
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Voice-First AI Travel Planning Assistant API",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add rate limiting middleware
app.add_middleware(
    RateLimiterMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour
)

# Add global error handler
app.add_exception_handler(TravelAssistantException, error_handler)
app.add_exception_handler(Exception, error_handler)


# Health check endpoint
@app.get("/api/test-n8n", tags=["Testing"])
async def test_n8n_connection():
    """
    Test n8n webhook connection.
    Useful for diagnosing DNS and connection issues.
    """
    try:
        from src.services.n8n_client import get_n8n_client
        
        n8n_client = get_n8n_client()
        if not n8n_client:
            return {
                "success": False,
                "error": "N8N_WEBHOOK_URL not configured",
                "message": "Please set N8N_WEBHOOK_URL in your .env file"
            }
        
        connection_test = n8n_client.test_connection()
        return connection_test
        
    except Exception as e:
        logger.error(f"n8n connection test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Connection test encountered an error"
        }
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns API status and basic information.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }

@app.get("/api/cors-config", tags=["Debug"])
async def get_cors_config():
    """
    Debug endpoint to show current CORS configuration.
    Useful for troubleshooting CORS issues.
    """
    return {
        "cors_origins": settings.cors_origins,
        "cors_origins_raw": settings.cors_origins_raw,
        "cors_allow_credentials": settings.cors_allow_credentials,
        "cors_allow_methods": settings.cors_allow_methods,
        "cors_allow_headers": settings.cors_allow_headers,
        "note": "Check that 'cors_origins' includes your frontend URL (e.g., https://sriram07ms-collab.github.io)"
    }


# Main chat endpoint
@app.post("/api/chat", tags=["Chat"], response_model=Union[ChatResponse, ErrorResponse])
async def chat(request: Request):
    """
    Main chat endpoint for voice/text input.
    Handles trip planning, editing, and explanations.
    """
    try:
        from src.models.request_models import ChatRequest
        from src.models.response_models import ErrorResponse
        from src.orchestrator.orchestrator import get_orchestrator
        from src.orchestrator.intent_classifier import get_intent_classifier
        
        # Parse request body
        body = await request.json()
        chat_request = ChatRequest(**body)
        
        # Get orchestrator and intent classifier
        orchestrator = get_orchestrator()
        intent_classifier = get_intent_classifier()
        
        # Get or create session
        session_id = chat_request.session_id
        if not session_id:
            from src.orchestrator.conversation_manager import get_conversation_manager
            conversation_manager = get_conversation_manager()
            session_id = conversation_manager.create_session()
        
        # Classify intent
        logger.info(f"Classifying intent for message: {chat_request.message[:100]}")
        classification = intent_classifier.classify_intent(chat_request.message)
        intent = classification.get("intent", "OTHER")
        logger.info(f"Classified intent: {intent} (confidence: {classification.get('confidence', 0)})")
        
        # Route to appropriate handler
        if intent == "PLAN_TRIP":
            result = orchestrator.plan_trip(session_id, chat_request.message)
        elif intent == "EDIT_ITINERARY":
            result = orchestrator.edit_itinerary(session_id, chat_request.message)
        elif intent == "EXPLAIN":
            result = orchestrator.explain_decision(session_id, chat_request.message)
        else:
            # Default to planning if intent unclear
            logger.info(f"Unclear intent '{intent}', defaulting to PLAN_TRIP")
            result = orchestrator.plan_trip(session_id, chat_request.message)
        
        logger.info(f"Orchestrator result status: {result.get('status')}")
        
        # Convert result to ChatResponse
        if result.get("status") == "error":
            logger.error(f"Orchestrator returned error: {result.get('message')}")
            return ErrorResponse(
                status="error",
                error_type="CHAT_ERROR",
                message=result.get("message", "An error occurred"),
                details=result
            )
        
        # For clarifying questions, ensure message field is set from question if needed
        if result.get("status") == "clarifying" and not result.get("message") and result.get("question"):
            result["message"] = result.get("question")
        
        # Build ChatResponse
        sources = result.get("sources", [])
        if sources is None:
            sources = []
        
        # Ensure sources is a list
        if not isinstance(sources, list):
            logger.warning(f"Sources is not a list, got {type(sources)}: {sources}")
            sources = []
        
        logger.info(f"Building ChatResponse with {len(sources)} sources")
        
        response = ChatResponse(
            status=result.get("status", "success"),
            message=result.get("message"),
            itinerary=result.get("itinerary"),
            sources=sources,
            evaluation=result.get("evaluation"),
            session_id=result.get("session_id", session_id),
            clarifying_questions_count=result.get("clarifying_questions_count", 0),
            question=result.get("question")
        )
        
        logger.info(f"Returning ChatResponse with status: {response.status}, sources: {len(response.sources or [])}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


# Direct planning endpoint
@app.post("/api/plan", tags=["Planning"])
async def plan_trip(request: Request):
    """
    Direct trip planning endpoint.
    Creates an itinerary from preferences.
    """
    # TODO: Implement in Phase 4
    # 1. Parse request body (PlanRequest)
    # 2. Call orchestrator.plan_trip()
    # 3. Return PlanResponse
    
    raise HTTPException(
        status_code=501,
        detail="Plan endpoint not yet implemented. Coming in Phase 4."
    )


# Edit endpoint
@app.post("/api/edit", tags=["Editing"])
async def edit_itinerary(request: Request):
    """
    Edit itinerary endpoint.
    Modifies existing itinerary based on voice/text command.
    """
    # TODO: Implement in Phase 5
    # 1. Parse request body (EditRequest)
    # 2. Get session and current itinerary
    # 3. Call orchestrator.edit_itinerary()
    # 4. Return EditResponse
    
    raise HTTPException(
        status_code=501,
        detail="Edit endpoint not yet implemented. Coming in Phase 5."
    )


# Explanation endpoint
@app.post("/api/explain", tags=["Explanation"], response_model=Union[ExplainResponse, ErrorResponse])
async def explain_decision(request: Request):
    """
    Explanation endpoint.
    Provides explanations for itinerary decisions.
    """
    try:
        from src.models.request_models import ExplainRequest
        from src.models.response_models import ExplainResponse, ErrorResponse
        from src.orchestrator.orchestrator import get_orchestrator
        
        # Parse request body
        body = await request.json()
        explain_request = ExplainRequest(**body)
        
        # Get orchestrator
        orchestrator = get_orchestrator()
        
        # Get session ID
        session_id = explain_request.session_id
        if not session_id:
            from src.orchestrator.conversation_manager import get_conversation_manager
            conversation_manager = get_conversation_manager()
            session_id = conversation_manager.create_session()
        
        # Get question text
        question = explain_request.question or "Why did you create this itinerary?"
        
        # Call orchestrator to explain
        result = orchestrator.explain_decision(session_id, question)
        
        # Convert result to ExplainResponse
        if result.get("status") == "error":
            return ErrorResponse(
                status="error",
                error_type="EXPLAIN_ERROR",
                message=result.get("message", "An error occurred while generating explanation"),
                details=result
            )
        
        return ExplainResponse(
            status=result.get("status", "success"),
            explanation=result.get("explanation", result.get("message", "")),
            sources=result.get("sources", []),
            reasoning=result.get("reasoning"),
            alternatives=result.get("alternatives"),
            uncertainty=result.get("uncertainty")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explain endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )


# PDF generation endpoint
@app.post("/api/generate-pdf", tags=["PDF"], response_model=Union[PDFResponse, ErrorResponse])
async def generate_pdf(request: Request):
    """
    PDF generation endpoint.
    Triggers n8n workflow to generate and email PDF itinerary.
    """
    try:
        from src.models.request_models import GeneratePDFRequest
        from src.models.response_models import PDFResponse, ErrorResponse
        from src.orchestrator.conversation_manager import get_conversation_manager
        from src.services.n8n_client import get_n8n_client
        
        # Parse request body
        body = await request.json()
        pdf_request = GeneratePDFRequest(**body)
        
        # Get conversation manager
        conversation_manager = get_conversation_manager()
        
        # Get session and itinerary
        session = conversation_manager.get_session(pdf_request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please plan a trip first."
            )
        
        if not session.itinerary:
            raise HTTPException(
                status_code=400,
                detail="No itinerary found. Please plan a trip first."
            )
        
        # Get n8n client
        n8n_client = get_n8n_client()
        if not n8n_client:
            raise HTTPException(
                status_code=503,
                detail="PDF generation service is not configured. Please set N8N_WEBHOOK_URL in your .env file."
            )
        
        # Test connection before attempting PDF generation
        connection_test = n8n_client.test_connection()
        if not connection_test.get("success"):
            error_detail = connection_test.get("error", "Connection test failed")
            suggestions = connection_test.get("suggestions", [])
            detail_msg = f"n8n webhook connection test failed: {error_detail}"
            if suggestions:
                detail_msg += "\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
            raise HTTPException(
                status_code=503,
                detail=detail_msg
            )
        
        # Log that we're attempting PDF generation
        logger.info(f"Generating PDF for session {pdf_request.session_id}, email: {pdf_request.email}")
        
        # Call n8n webhook
        result = n8n_client.generate_pdf_and_email(
            itinerary=session.itinerary,
            sources=session.sources or [],
            email=pdf_request.email
        )
        
        # Return response
        # Handle case where email_sent is None (unknown) from empty/non-JSON responses
        email_sent = result.get("email_sent")
        if email_sent is None:
            # If email_sent is None (unknown), default to False but add warning in message
            email_sent = False
            if "empty response" in result.get("message", "").lower():
                result["message"] = result.get("message", "") + " Please check n8n execution logs to verify email was sent."
        
        return PDFResponse(
            status=result.get("status", "success"),
            message=result.get("message", "PDF generated successfully"),
            email_sent=email_sent,
            pdf_url=result.get("pdf_url"),
            email_address=result.get("email_address") or pdf_request.email,
            generated_at=result.get("generated_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Returns API information.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/api/chat",
            "plan": "/api/plan",
            "edit": "/api/edit",
            "explain": "/api/explain",
            "pdf": "/api/generate-pdf"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
