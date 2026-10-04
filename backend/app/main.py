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