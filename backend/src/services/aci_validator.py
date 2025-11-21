# File: backend/src/services/aci_validator.py
"""
ACI 318-19 Validation and Auto-Correction Service.

Implements mandatory defaults for:
- Hook lengths (90°, 135°, 180°)
- Bend diameters
- Concrete cover requirements
- Bar spacing validation
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
from pydantic import BaseModel, Field


class BarSize(str, Enum):
    """Standard rebar sizes (metric mm)."""
    NO_3 = "9.5"    # #3 (3/8")
    NO_4 = "12.7"   # #4 (1/2")
    NO_5 = "15.9"   # #5 (5/8")
    NO_6 = "19.1"   # #6 (3/4")
    NO_8 = "25.4"   # #8 (1")
    NO_9 = "28.7"   # #9 (1-1/8")
    NO_10 = "32.3"  # #10 (1-1/4")
    NO_11 = "35.8"  # #11 (1-3/8")
    NO_14 = "43.0"  # #14 (1-3/4")
    NO_18 = "57.3"  # #18 (2-1/4")


class ExposureCondition(str, Enum):
    """ACI 318-19 Table 20.6.1.3.1 exposure conditions."""
    CAST_AGAINST_EARTH = "cast_against_earth"
    WEATHER_EXPOSED = "weather_exposed"
    INTERIOR_SLABS = "interior_slabs"
    INTERIOR_BEAMS_COLUMNS = "interior_beams_columns"


class HookType(str, Enum):
    """Standard hook configurations."""
    STANDARD_90 = "90_degree"
    STANDARD_180 = "180_degree"
    SEISMIC_135 = "135_degree_seismic"


class ACIDefaults(BaseModel):
    """Container for calculated ACI 318 default values."""
    hook_extension_mm: float = Field(description="Hook extension length")
    bend_diameter_mm: float = Field(description="Minimum bend diameter")
    min_cover_mm: float = Field(description="Minimum concrete cover")
    min_spacing_mm: float = Field(description="Minimum bar spacing")


class ACIValidator:
    """
    ACI 318-19 validation and auto-correction engine.

    The "Lawyer" that ensures all data is code-compliant.
    """

    # ACI 318-19 Table 20.6.1.3.1 - Minimum Cover (mm)
    COVER_REQUIREMENTS: Dict[ExposureCondition, Dict[str, float]] = {
        ExposureCondition.CAST_AGAINST_EARTH: {"all": 76.2},  # 3.0"
        ExposureCondition.WEATHER_EXPOSED: {
            "large": 50.8,  # 2.0" for #6-#18
            "small": 38.1   # 1.5" for #3-#5
        },
        ExposureCondition.INTERIOR_BEAMS_COLUMNS: {"all": 38.1},  # 1.5"
        ExposureCondition.INTERIOR_SLABS: {"all": 19.1},  # 0.75"
    }

    @staticmethod
    def calculate_hook_extension(
        bar_diameter_mm: float,
        hook_type: HookType = HookType.STANDARD_90
    ) -> float:
        """
        Calculate hook extension per ACI 318-19 Section 25.3.1.

        Args:
            bar_diameter_mm: Bar diameter in millimeters
            hook_type: Type of hook (90°, 180°, or 135° seismic)

        Returns:
            Extension length in millimeters
        """
        db = bar_diameter_mm

        if hook_type == HookType.STANDARD_90:
            # Extension = 12db for all sizes
            return 12 * db

        elif hook_type == HookType.STANDARD_180:
            # Extension = max(4db, 2.5")
            return max(4 * db, 63.5)  # 2.5" = 63.5mm

        elif hook_type == HookType.SEISMIC_135:
            # Extension = max(6db, 3.0")
            return max(6 * db, 76.2)  # 3.0" = 76.2mm

        return 12 * db  # Default fallback

    @staticmethod
    def calculate_bend_diameter(
        bar_diameter_mm: float,
        hook_type: HookType = HookType.STANDARD_90
    ) -> float:
        """
        Calculate minimum inside bend diameter per ACI 318-19 Table 25.3.2.

        Args:
            bar_diameter_mm: Bar diameter in millimeters
            hook_type: Type of hook

        Returns:
            Minimum inside bend diameter in millimeters
        """
        db = bar_diameter_mm

        # Determine bar size category
        if db <= 25.4:  # #3 through #8
            bend_factor = 6
        elif db <= 35.8:  # #9, #10, #11
            bend_factor = 8
        else:  # #14, #18
            bend_factor = 10

        return bend_factor * db

    @staticmethod
    def get_minimum_cover(
        bar_diameter_mm: float,
        exposure: ExposureCondition = ExposureCondition.INTERIOR_BEAMS_COLUMNS
    ) -> float:
        """
        Get minimum concrete cover per ACI 318-19 Table 20.6.1.3.1.

        Args:
            bar_diameter_mm: Bar diameter in millimeters
            exposure: Exposure condition

        Returns:
            Minimum cover in millimeters
        """
        requirements = ACIValidator.COVER_REQUIREMENTS[exposure]

        if "all" in requirements:
            return requirements["all"]

        # Weather-exposed case: check bar size
        if bar_diameter_mm >= 19.1:  # #6 and larger
            return requirements["large"]
        else:  # #3-#5
            return requirements["small"]

    @staticmethod
    def calculate_minimum_spacing(
        bar_diameter_mm: float,
        aggregate_size_mm: float = 25.0  # Default 1" aggregate
    ) -> float:
        """
        Calculate minimum clear spacing per ACI 318-19 Section 25.2.

        Args:
            bar_diameter_mm: Bar diameter
            aggregate_size_mm: Maximum aggregate size

        Returns:
            Minimum clear spacing in millimeters
        """
        # ACI 318-19 25.2.1: Clear spacing >= max(db, 25mm, 1.33 * aggregate)
        return max(
            bar_diameter_mm,
            25.0,
            1.33 * aggregate_size_mm
        )

    @staticmethod
    def validate_bar_fit(
        section_width_mm: float,
        section_depth_mm: float,
        bar_diameter_mm: float,
        bar_count: int,
        bar_x_columns: int,
        bar_y_matrix: List[int],
        clear_cover_mm: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that bars physically fit within the section.

        Args:
            section_width_mm: Section width
            section_depth_mm: Section depth
            bar_diameter_mm: Bar diameter
            bar_count: Total bar count
            bar_x_columns: Number of columns along X
            bar_y_matrix: Bars per column
            clear_cover_mm: Concrete cover

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Calculate effective dimensions
        w_eff = section_width_mm - 2 * clear_cover_mm - bar_diameter_mm
        d_eff = section_depth_mm - 2 * clear_cover_mm - bar_diameter_mm

        # Check X-axis spacing
        if bar_x_columns > 1:
            x_spacing = w_eff / (bar_x_columns - 1)
            min_spacing = ACIValidator.calculate_minimum_spacing(bar_diameter_mm)

            if x_spacing < min_spacing:
                return False, (
                    f"Insufficient X-spacing: {x_spacing:.1f}mm < "
                    f"minimum {min_spacing:.1f}mm"
                )

        # Check Y-axis spacing
        max_y_bars = max(bar_y_matrix)
        if max_y_bars > 1:
            y_spacing = d_eff / (max_y_bars - 1)
            min_spacing = ACIValidator.calculate_minimum_spacing(bar_diameter_mm)

            if y_spacing < min_spacing:
                return False, (
                    f"Insufficient Y-spacing: {y_spacing:.1f}mm < "
                    f"minimum {min_spacing:.1f}mm"
                )

        return True, None

    @staticmethod
    def heal_extraction(
        extraction_data: dict,
        exposure: ExposureCondition = ExposureCondition.INTERIOR_BEAMS_COLUMNS
    ) -> Tuple[dict, List[str]]:
        """
        Auto-heal incomplete extraction by injecting ACI 318 defaults.

        Args:
            extraction_data: Raw extraction from Gemini
            exposure: Exposure condition for cover calculation

        Returns:
            Tuple of (healed_data, list_of_corrections_applied)
        """
        corrections: List[str] = []
        healed = extraction_data.copy()

        # 1. Inject default cover if missing
        if healed.get("concrete_specifications"):
            concrete_specs = healed["concrete_specifications"]

            if concrete_specs.get("clear_cover_mm") is None:
                # Get first longitudinal bar diameter for cover calc
                long_bars = healed.get("longitudinal_reinforcement", [])
                if long_bars and long_bars[0].get("bar_diameter_mm"):
                    bar_dia = long_bars[0]["bar_diameter_mm"]
                    default_cover = ACIValidator.get_minimum_cover(bar_dia, exposure)
                    concrete_specs["clear_cover_mm"] = default_cover
                    corrections.append(
                        f"Injected clear_cover_mm={default_cover:.1f}mm "
                        f"per ACI 318 {exposure.value}"
                    )

        # 2. Process longitudinal reinforcement
        for idx, long_bar in enumerate(healed.get("longitudinal_reinforcement", [])):
            bar_dia = long_bar.get("bar_diameter_mm")

            if bar_dia:
                # Calculate hook defaults (for future use)
                hook_ext = ACIValidator.calculate_hook_extension(bar_dia)
                bend_dia = ACIValidator.calculate_bend_diameter(bar_dia)

                # Store for potential future use
                long_bar["_aci_defaults"] = {
                    "hook_extension_mm": hook_ext,
                    "bend_diameter_mm": bend_dia
                }
                corrections.append(
                    f"Bar {idx}: Calculated ACI defaults "
                    f"(hook={hook_ext:.1f}mm, bend_dia={bend_dia:.1f}mm)"
                )

        # 3. Validate bar fit
        geometry = healed.get("geometry", {})
        concrete_specs = healed.get("concrete_specifications", {})
        long_bars = healed.get("longitudinal_reinforcement", [])

        if geometry and concrete_specs and long_bars:
            width = geometry.get("width_mm")
            depth = geometry.get("depth_mm")
            cover = concrete_specs.get("clear_cover_mm")

            if width and depth and cover and long_bars[0].get("bar_diameter_mm"):
                first_bar = long_bars[0]
                is_valid, error = ACIValidator.validate_bar_fit(
                    section_width_mm=width,
                    section_depth_mm=depth,
                    bar_diameter_mm=first_bar["bar_diameter_mm"],
                    bar_count=first_bar["bar_count"],
                    bar_x_columns=first_bar["bar_x_columns"],
                    bar_y_matrix=first_bar["bar_y_matrix"],
                    clear_cover_mm=cover
                )

                if not is_valid:
                    corrections.append(f"⚠️ VALIDATION ERROR: {error}")
                else:
                    corrections.append("✓ Bar spacing validation passed")

        return healed, corrections
