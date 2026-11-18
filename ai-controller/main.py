"""
Main Entry Point for AI Controller FastAPI Application.
Configures CORS, middleware, routers, lifespan events, and global exception handlers.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from config import settings
from controller import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_controller.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("=" * 60)
    logger.info("Starting AI Financial Assistant Controller")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Firebase Project: {settings.FIREBASE_PROJECT_ID}")
    logger.info(f"Allowed CORS Origins: {settings.cors_origins_list}")
    logger.info(f"Gemini Configured: {bool(settings.GEMINI_API_KEY)}")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down AI Controller")


app = FastAPI(
    title="Expense Tracker AI Controller",
    description="Advanced RAG-based AI Financial Assistant integrated with Firebase and ChromaDB",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
# Never use wildcard in production when authorization headers are present
origins = settings.cors_origins_list
logger.info(f"Configuring CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global Request Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

# Generic Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request."
        }
    )

# Include Controller Router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
