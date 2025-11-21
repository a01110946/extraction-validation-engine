# File: backend/src/api/routes.py
"""
FastAPI routes for extraction and validation workflow.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

from ..models.schemas import ColumnExtraction
from ..services.gemini_extractor import GeminiExtractor
from ..services.aci_validator import ACIValidator, ExposureCondition
from ..services.geometry_calculator import GeometryCalculator
from ..core.database import database
from ..core.config import settings

router = APIRouter(prefix="/api/v1")

# Initialize services
gemini_extractor = GeminiExtractor()
aci_validator = ACIValidator()


@router.post("/extract")
async def extract_from_image(
    file: UploadFile = File(...),
    auto_validate: bool = True
):
    """
    Extract column data from an uploaded image using Gemini 3.

    Args:
        file: Uploaded image file (PNG, JPG, JPEG)
        auto_validate: Whether to automatically apply ACI validation/healing

    Returns:
        Extracted and optionally validated column data
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (PNG, JPG, JPEG)"
        )

    try:
        # Read image bytes
        image_bytes = await file.read()

        # Extract using Gemini
        extraction: ColumnExtraction = await gemini_extractor.extract_from_image(
            image_bytes=image_bytes,
            mime_type=file.content_type
        )

        # Convert to dict for processing
        extraction_dict = extraction.model_dump(mode='json')

        # Apply ACI validation if requested
        corrections = []
        if auto_validate:
            extraction_dict, corrections = aci_validator.heal_extraction(
                extraction_dict,
                exposure=ExposureCondition.INTERIOR_BEAMS_COLUMNS
            )

        return {
            "success": True,
            "data": extraction_dict,
            "corrections_applied": corrections,
            "extracted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/validate")
async def validate_extraction(
    extraction_data: dict = Body(...),
    exposure: ExposureCondition = ExposureCondition.INTERIOR_BEAMS_COLUMNS
):
    """
    Validate and heal extraction data using ACI 318 rules.

    Args:
        extraction_data: Raw or partial extraction data
        exposure: Exposure condition for cover requirements

    Returns:
        Healed extraction data with corrections listed
    """
    try:
        healed_data, corrections = aci_validator.heal_extraction(
            extraction_data,
            exposure=exposure
        )

        return {
            "success": True,
            "data": healed_data,
            "corrections": corrections
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/geometry")
async def generate_geometry(
    extraction_data: dict = Body(...),
    column_height_mm: Optional[float] = None
):
    """
    Generate 3D geometry from extraction data.

    Args:
        extraction_data: Validated extraction data
        column_height_mm: Column height (defaults to 3000mm)

    Returns:
        3D geometry data ready for Three.js visualization
    """
    try:
        import sys
        import json
        height = column_height_mm or settings.DEFAULT_COLUMN_HEIGHT_MM

        print(f"\n{'='*80}", flush=True)
        print(f"DEBUG: Full extraction_data:", flush=True)
        print(json.dumps(extraction_data, indent=2, default=str), flush=True)
        print(f"{'='*80}\n", flush=True)
        sys.stdout.flush()

        calculator = GeometryCalculator(column_height_mm=height)
        geometry = calculator.generate_complete_geometry(extraction_data)

        return {
            "success": True,
            "geometry": geometry
        }

    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        raise HTTPException(
            status_code=500,
            detail=error_details
        )


@router.post("/extractions")
async def save_extraction(
    extraction_data: dict = Body(...),
    validated: bool = False,
    validation_notes: Optional[str] = None
):
    """
    Save extraction to MongoDB.

    Args:
        extraction_data: Complete extraction data
        validated: Whether human has validated
        validation_notes: Optional validator notes

    Returns:
        Saved extraction with MongoDB ID
    """
    try:
        # Add metadata
        extraction_data["validated"] = validated
        extraction_data["validation_notes"] = validation_notes
        extraction_data["saved_at"] = datetime.utcnow()

        # Insert into MongoDB
        collection = database.get_collection("extractions")
        result = await collection.insert_one(extraction_data)

        return {
            "success": True,
            "id": str(result.inserted_id),
            "message": "Extraction saved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Save failed: {str(e)}"
        )


@router.get("/extractions")
async def list_extractions(
    skip: int = 0,
    limit: int = 20,
    validated_only: bool = False
):
    """
    List saved extractions from MongoDB.

    Args:
        skip: Number to skip (pagination)
        limit: Maximum results to return
        validated_only: Only return human-validated extractions

    Returns:
        List of extractions
    """
    try:
        collection = database.get_collection("extractions")

        # Build query
        query = {}
        if validated_only:
            query["validated"] = True

        # Fetch documents
        cursor = collection.find(query).skip(skip).limit(limit).sort("saved_at", -1)
        extractions = await cursor.to_list(length=limit)

        # Convert ObjectId to string
        for ext in extractions:
            ext["_id"] = str(ext["_id"])

        return {
            "success": True,
            "count": len(extractions),
            "data": extractions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetch failed: {str(e)}"
        )


@router.get("/extractions/{extraction_id}")
async def get_extraction(extraction_id: str):
    """
    Get a single extraction by ID.

    Args:
        extraction_id: MongoDB ObjectId as string

    Returns:
        Extraction data
    """
    try:
        from bson import ObjectId

        collection = database.get_collection("extractions")
        extraction = await collection.find_one({"_id": ObjectId(extraction_id)})

        if not extraction:
            raise HTTPException(status_code=404, detail="Extraction not found")

        extraction["_id"] = str(extraction["_id"])

        return {
            "success": True,
            "data": extraction
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fetch failed: {str(e)}"
        )


@router.put("/extractions/{extraction_id}")
async def update_extraction(
    extraction_id: str,
    extraction_data: dict = Body(...),
    validated: Optional[bool] = None,
    validation_notes: Optional[str] = None
):
    """
    Update an existing extraction.

    Args:
        extraction_id: MongoDB ObjectId as string
        extraction_data: Updated extraction data
        validated: Update validation status
        validation_notes: Update validation notes

    Returns:
        Success status
    """
    try:
        from bson import ObjectId

        collection = database.get_collection("extractions")

        # Build update document
        update_doc = {"$set": extraction_data}

        if validated is not None:
            update_doc["$set"]["validated"] = validated

        if validation_notes is not None:
            update_doc["$set"]["validation_notes"] = validation_notes

        update_doc["$set"]["updated_at"] = datetime.utcnow()

        # Update
        result = await collection.update_one(
            {"_id": ObjectId(extraction_id)},
            update_doc
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Extraction not found")

        return {
            "success": True,
            "message": "Extraction updated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "extraction-validation-engine",
        "version": "0.1.0"
    }
