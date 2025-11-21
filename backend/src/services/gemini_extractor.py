# File: backend/src/services/gemini_extractor.py
"""
Gemini 3 extraction service.
Handles AI-powered data extraction from construction drawings.
"""

from google import genai
from google.genai import types
from typing import Optional
from pathlib import Path

from ..core.config import settings
from ..models.schemas import ColumnExtraction


# System prompt from Colab (Cell 4)
SYSTEM_PROMPT = """
Role: You are a precise structural extractor and expert construction estimator, specializing in converting drawing graphics into geometric input data for 3D modeling.
Task: Analyze the column cross-section image and extract all technical and PRESCRIPTIVE specifications.

Critical Extraction Rules for 3D Modeling:
1. **Strict Observation:** Extract ALL visible information. Do not guess. Use null for missing values.
2. **Standardization:** All dimensions MUST be converted to **millimeters (mm)**.
3. **Verbatim:** For IDs, references, and concrete strength, copy the exact text.

**Prescriptive Rules for Reinforcement (Crucial for 3D Scripting):**
A. **Longitudinal Bar Placement (bar_x_columns & bar_y_matrix):**
    - Analyze the visual grid of the longitudinal bars.
    - 'bar_x_columns': Count the total number of vertical columns (along the W dimension).
    - 'bar_y_matrix': Provide a list detailing the number of bars in each of those vertical columns, starting from the left.
B. **Transverse Tie Dimensions (span_width_mm / span_depth_mm):**
    - For all stirrups/ties, calculate the **internal clear dimension** they span.
C. **Spacing Standardization:** For variable spacing indicators (e.g., "Rto." [Resto], "Rem.", or "Rest"), the **quantity** field in the spacing array MUST be the verbatim English word: **"rest"** (all lowercase).
D. **Required Fields:** Ensure 'bar_count', 'reference_code', 'stirrup_type', and 'spacing_mm' are never null.
"""


class GeminiExtractor:
    """Gemini 3 extraction service."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key (defaults to settings)
        """
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.async_client = self.client.aio

        self.thinking_config = types.ThinkingConfig(
            include_thoughts=True,
            thinking_level=settings.GEMINI_THINKING_LEVEL
        )

    async def extract_from_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> ColumnExtraction:
        """
        Extract column data from an image using Gemini 3.

        Args:
            image_bytes: Image file bytes
            mime_type: Image MIME type

        Returns:
            Parsed ColumnExtraction object

        Raises:
            Exception: If extraction fails
        """
        # Prepare request config
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ColumnExtraction,
            thinking_config=self.thinking_config
        )

        # Call Gemini API
        response = await self.async_client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type
                        ),
                        types.Part.from_text(
                            text="Extract the column specifications."
                        ),
                    ]
                )
            ],
            config=config
        )

        # Parse response
        # The response.parsed property is automatically a Pydantic object
        return response.parsed
