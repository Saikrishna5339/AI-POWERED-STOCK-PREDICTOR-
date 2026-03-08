"""
FastAPI application main file - StockAI Pro (Indian Stock Market)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from backend.api.routes import router

# Create FastAPI app
app = FastAPI(
    title="StockAI Pro - Indian Stock Market Platform",
    description="AI-powered Indian Stock Market Prediction and Analysis using LSTM, TA, and Sentiment",
    version="2.0.0",
    docs_url="/docs",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main dashboard"""
    template_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>StockAI Pro</h1><p>Frontend not found. Check frontend/templates/index.html</p>"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "StockAI Pro API is running", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    from backend.config import API_HOST, API_PORT

    print("\n" + "=" * 55)
    print("  StockAI Pro - Indian Stock Market Platform v2.0")
    print("=" * 55)
    print(f"  Dashboard: http://localhost:{API_PORT}")
    print(f"  API Docs:  http://localhost:{API_PORT}/docs")
    print("=" * 55 + "\n")

    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
