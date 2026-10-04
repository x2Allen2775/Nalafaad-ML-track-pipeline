"""
FastAPI Application.
Exposes endpoints for receipt extraction, proportional bill splitting,
and conversational breakdown explanations.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from PIL import Image
import io

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request

from .schemas import (
    ReceiptData,
    SplitCalculationRequest,
    SplitCalculationResponse
)
from .apportionment import calculate_proportional_split
from .inference import engine
from .sample_bills import PRESET_BILLS

app = FastAPI(
    title="SplitSnap API",
    description="Proportional Restaurant Bill Splitting with Fine-Tuned Visual Document Understanding",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root(request: Request):
    """
    Root status endpoint. Provides direct links to the frontend UI,
    interactive API docs, and health checks to prevent 404 when clicking the host link.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        model_status = "Loaded (Ready for Inference)" if engine.model is not None else "Neural OCR Fallback Active"
        device = getattr(engine, "device", "cpu")
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SplitSnap Backend API</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #09090b;
                    color: #fafafa;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .card {{
                    background: #121215;
                    border: 1px solid #27272a;
                    border-radius: 16px;
                    padding: 40px;
                    max-width: 600px;
                    width: 90%;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    background: rgba(34, 197, 94, 0.15);
                    color: #4ade80;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                    border-radius: 9999px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    margin-bottom: 16px;
                }}
                h1 {{
                    margin: 0 0 12px 0;
                    font-size: 1.75rem;
                    letter-spacing: -0.02em;
                }}
                p {{
                    color: #a1a1aa;
                    line-height: 1.6;
                    margin-bottom: 24px;
                }}
                .meta-box {{
                    background: #18181c;
                    border: 1px solid #27272a;
                    border-radius: 10px;
                    padding: 16px;
                    margin-bottom: 28px;
                    font-size: 0.9rem;
                }}
                .meta-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 6px 0;
                    border-bottom: 1px solid #222227;
                }}
                .meta-row:last-child {{ border-bottom: none; }}
                .meta-label {{ color: #71717a; }}
                .meta-val {{ color: #f4f4f5; font-family: monospace; font-weight: 600; }}
                .actions {{
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }}
                .btn {{
                    display: block;
                    text-align: center;
                    padding: 12px 20px;
                    border-radius: 10px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 0.95rem;
                    transition: all 0.15s ease;
                }}
                .btn-primary {{
                    background: #fafafa;
                    color: #09090b;
                }}
                .btn-primary:hover {{
                    background: #ffffff;
                    transform: translateY(-1px);
                }}
                .btn-secondary {{
                    background: #1f1f23;
                    color: #e4e4e7;
                    border: 1px solid #27272a;
                }}
                .btn-secondary:hover {{
                    background: #27272a;
                    color: #ffffff;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="badge">● SplitSnap API Active & Healthy</div>
                <h1>SplitSnap Backend Gateway</h1>
                <p>
                    The FastAPI backend is running and ready to process receipt images with fine-tuned Donut vision transformers and compute proportional bill apportionments.
                </p>
                <div class="meta-box">
                    <div class="meta-row">
                        <span class="meta-label">Donut Vision Model</span>
                        <span class="meta-val">{model_status}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">PyTorch Device</span>
                        <span class="meta-val">{device.upper()}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">API Version</span>
                        <span class="meta-val">v1.0.0</span>
                    </div>
                </div>
                <div class="actions">
                    <a href="http://localhost:3000" class="btn btn-primary">🚀 Open SplitSnap Web App (localhost:3000)</a>
                    <a href="/docs" class="btn btn-secondary">📖 Interactive Swagger API Docs (/docs)</a>
                    <a href="/api/health" class="btn btn-secondary">🩺 Health Check Endpoint (/api/health)</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    return JSONResponse({
        "status": "healthy",
        "service": "SplitSnap Backend API",
        "device": engine.device,
        "donut_model_loaded": engine.model is not None,
        "frontend_app_url": "http://localhost:3000",
        "docs_url": "/docs",
        "health_check_url": "/api/health"
    })

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SplitSnap Backend",
        "device": engine.device,
        "donut_model_loaded": engine.model is not None
    }

@app.get("/api/presets")
def get_presets():
    """Returns preset Indian restaurant receipts for 1-click test drive."""
    return PRESET_BILLS

@app.post("/api/extract", response_model=ReceiptData)
async def extract_receipt(
    file: Optional[UploadFile] = File(None),
    preset_id: Optional[str] = Form(None)
):
    """
    Extracts structured receipt JSON with field-level confidence scores.
    Supports image upload or preset Indian bills.
    """
    if preset_id:
        for p in PRESET_BILLS:
            if p["id"] == preset_id:
                return ReceiptData(**p)

    if file:
        try:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            return engine.extract_from_image(image)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process uploaded image: {str(e)}")

    # Default to first preset bill if neither provided
    return ReceiptData(**PRESET_BILLS[0])

@app.post("/api/calculate-split", response_model=SplitCalculationResponse)
def calculate_split_endpoint(request: SplitCalculationRequest):
    """
    Computes mathematically fair proportional split, handles manual adjustments,
    and returns plain-language explanations.
    """
    try:
        return calculate_proportional_split(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Apportionment calculation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
##jai barak