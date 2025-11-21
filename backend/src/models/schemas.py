# File: backend/src/models/schemas.py
"""
Pydantic schemas for reinforced concrete element extraction.
Based on Gemini 3 Colab extraction logic with production enhancements.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


# --- Sub-Components ---

class SpacingItem(BaseModel):
    """
    Represents a spacing pattern for transverse reinforcement.

    Example: "10@100" means 10 spaces at 100mm spacing.
    Special case: quantity="rest" means remaining length.
    """
    quantity: str = Field(
        ...,
        description="Number of spaces (e.g., '10') or 'rest' for remaining length"
    )
    spacing: float = Field(
        ...,
        ge=0.001,
        description="Spacing distance in millimeters"
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: str) -> str:
        """Ensure quantity is either 'rest' or a positive integer."""
        if v.lower() == "rest":
            return "rest"
        try:
            if int(v) <= 0:
                raise ValueError("Quantity must be positive")
            return v
        except ValueError:
            raise ValueError("Quantity must be 'rest' or a positive integer")


class StirrupDimensions(BaseModel):
    """Internal clear dimensions that a stirrup/tie encloses."""
    span_width_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Internal clear width the tie encloses"
    )
    span_depth_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Internal clear depth the tie encloses"
    )


class TransverseReinforcement(BaseModel):
    """
    Stirrups, ties, and hoops for shear/confinement.
    Includes spacing patterns and geometric dimensions.
    """
    stirrup_id: Optional[str] = Field(
        None,
        description="Verbatim ID/name from drawing"
    )
    stirrup_type: Literal[
        "main_stirrup",
        "intermediate_stirrup",
        "internal_tie",
        "cross_tie"
    ]
    bar_diameter_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Bar diameter in millimeters"
    )
    stirrup_dimensions: Optional[StirrupDimensions] = None
    stirrup_shape: Literal[
        "rectangular",
        "circular",
        "L-shaped",
        "U-shaped",
        "diamond",
        "custom"
    ]
    spacing_mm: List[SpacingItem] = Field(
        ...,
        min_length=1,
        description="Spacing pattern (required)"
    )
    reference_code: Optional[str] = Field(
        None,
        description="Verbatim callout text from drawing"
    )
    zone: Optional[str] = Field(
        None,
        description="Location zone (e.g., 'top', 'bottom', 'full_height')"
    )


class LongitudinalReinforcement(BaseModel):
    """
    Main flexural/axial reinforcement bars.
    Uses prescriptive placement logic (bar_x_columns, bar_y_matrix).
    """
    bar_group_id: Optional[str] = Field(
        None,
        description="Identifier if bars are grouped"
    )
    bar_diameter_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Bar diameter in millimeters"
    )
    bar_count: int = Field(
        ...,
        ge=1,
        description="Total number of bars (required)"
    )
    reference_code: str = Field(
        ...,
        description="Verbatim callout text (e.g., '14Ø5/8')"
    )
    zone: Optional[str] = Field(
        None,
        description="Location zone"
    )

    # NEW: Prescriptive placement fields
    bar_x_columns: int = Field(
        ...,
        ge=1,
        description="Number of vertical columns along X-axis"
    )
    bar_y_matrix: List[int] = Field(
        ...,
        min_length=1,
        description="Bar count per column (must sum to bar_count)"
    )

    @model_validator(mode="after")
    def validate_bar_placement(self) -> "LongitudinalReinforcement":
        """Ensure bar_y_matrix matches bar_x_columns and sums to bar_count."""
        if len(self.bar_y_matrix) != self.bar_x_columns:
            raise ValueError(
                f"bar_y_matrix length ({len(self.bar_y_matrix)}) "
                f"must equal bar_x_columns ({self.bar_x_columns})"
            )

        matrix_sum = sum(self.bar_y_matrix)
        if matrix_sum != self.bar_count:
            raise ValueError(
                f"Sum of bar_y_matrix ({matrix_sum}) "
                f"must equal bar_count ({self.bar_count})"
            )

        return self


class ConcreteSpecs(BaseModel):
    """Concrete material properties."""
    concrete_strength: str = Field(
        ...,
        description="Concrete strength (e.g., 'f\\'c=280kg/cm2')"
    )
    modulus_of_elasticity: Optional[str] = Field(
        None,
        description="Elastic modulus"
    )
    clear_cover_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Clear cover to reinforcement (required for 3D)"
    )


class Geometry(BaseModel):
    """Cross-section geometric properties."""
    cross_section_type: Literal[
        "rectangular",
        "circular",
        "L-shaped",
        "T-shaped"
    ]
    width_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Width for rectangular sections"
    )
    depth_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Depth for rectangular sections"
    )
    diameter_mm: Optional[float] = Field(
        None,
        ge=0.001,
        description="Diameter for circular sections"
    )

    @model_validator(mode="after")
    def validate_dimensions(self) -> "Geometry":
        """Ensure required dimensions are present based on section type."""
        if self.cross_section_type == "circular":
            if self.diameter_mm is None:
                raise ValueError("diameter_mm required for circular sections")
        elif self.cross_section_type in ["rectangular", "L-shaped", "T-shaped"]:
            if self.width_mm is None or self.depth_mm is None:
                raise ValueError(
                    f"width_mm and depth_mm required for {self.cross_section_type} sections"
                )
        return self


class ElementIdentification(BaseModel):
    """Element identification and metadata."""
    type_of_element: str = Field(
        ...,
        description="Element type (e.g., 'Column', 'Beam')"
    )
    element_id: str = Field(
        ...,
        description="Unique element identifier (e.g., 'C-02')"
    )
    level_reference: Optional[str] = Field(
        None,
        description="Floor/level reference"
    )
    section_reference: Optional[str] = Field(
        None,
        description="Section reference"
    )
    scale: Optional[str] = Field(
        None,
        description="Drawing scale (e.g., '1/25')"
    )


class ReinforcementLayout(BaseModel):
    """High-level reinforcement layout summary."""
    total_vertical_bars: Optional[int] = Field(
        None,
        ge=0,
        description="Total longitudinal bars"
    )
    total_stirrup_sets: Optional[int] = Field(
        None,
        ge=0,
        description="Total stirrup/tie sets"
    )
    reinforcement_pattern: Optional[str] = Field(
        None,
        description="Simplified pattern description (e.g., '3 Rectangular + 1 C-Tie')"
    )


# --- Main Container ---

class ColumnExtraction(BaseModel):
    """
    Complete extraction result for a reinforced concrete column.
    This is the top-level schema returned by Gemini 3.
    """
    element_identification: ElementIdentification
    geometry: Geometry
    concrete_specifications: Optional[ConcreteSpecs] = None
    longitudinal_reinforcement: List[LongitudinalReinforcement] = Field(
        ...,
        min_length=1,
        description="At least one longitudinal bar group required"
    )
    transverse_reinforcement: List[TransverseReinforcement] = Field(
        default_factory=list,
        description="Stirrups and ties"
    )
    reinforcement_layout: ReinforcementLayout

    # NEW: Metadata for database storage
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Extraction timestamp"
    )
    validated: bool = Field(
        default=False,
        description="Whether this extraction has been validated by a human"
    )
    validation_notes: Optional[str] = Field(
        None,
        description="Human validator notes"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "element_identification": {
                    "type_of_element": "Column",
                    "element_id": "C-02",
                    "level_reference": "CIM AL T8P",
                    "scale": "1/25"
                },
                "geometry": {
                    "cross_section_type": "rectangular",
                    "width_mm": 420.0,
                    "depth_mm": 700.0
                },
                "concrete_specifications": {
                    "concrete_strength": "f'c=280kg/cm2",
                    "clear_cover_mm": 40.0
                },
                "longitudinal_reinforcement": [
                    {
                        "bar_diameter_mm": 15.875,
                        "bar_count": 14,
                        "reference_code": "14Ø5/8\"",
                        "zone": "global",
                        "bar_x_columns": 3,
                        "bar_y_matrix": [6, 2, 6]
                    }
                ],
                "transverse_reinforcement": [
                    {
                        "stirrup_type": "main_stirrup",
                        "bar_diameter_mm": 8.0,
                        "stirrup_shape": "rectangular",
                        "spacing_mm": [
                            {"quantity": "1", "spacing": 50.0},
                            {"quantity": "7", "spacing": 100.0},
                            {"quantity": "rest", "spacing": 250.0}
                        ]
                    }
                ],
                "reinforcement_layout": {
                    "total_vertical_bars": 14,
                    "reinforcement_pattern": "3 Rectangular + 1 C-Tie"
                }
            }
        }
