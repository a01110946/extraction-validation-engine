# File: backend/src/services/geometry_calculator.py
"""
Headless geometry calculation engine using NumPy and geomdl.

Generates 3D coordinates and NURBS curves for reinforcement visualization
without relying on heavy CAD kernels.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from geomdl import NURBS, operations
from geomdl import exchange


class Point3D:
    """Simple 3D point container."""
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y, "z": self.z}


class LongitudinalBarGeometry:
    """Geometry data for a single longitudinal bar."""
    def __init__(
        self,
        bar_id: int,
        start_point: Point3D,
        end_point: Point3D,
        diameter_mm: float
    ):
        self.bar_id = bar_id
        self.start_point = start_point
        self.end_point = end_point
        self.diameter_mm = diameter_mm

    def to_dict(self) -> Dict:
        return {
            "bar_id": self.bar_id,
            "start": self.start_point.to_dict(),
            "end": self.end_point.to_dict(),
            "diameter_mm": self.diameter_mm,
            "type": "longitudinal"
        }


class StirrupGeometry:
    """Geometry data for a stirrup/tie with NURBS curves for bends."""
    def __init__(
        self,
        stirrup_id: str,
        path_points: List[Point3D],
        diameter_mm: float,
        shape: str,
        z_position: float
    ):
        self.stirrup_id = stirrup_id
        self.path_points = path_points
        self.diameter_mm = diameter_mm
        self.shape = shape
        self.z_position = z_position

    def to_dict(self) -> Dict:
        return {
            "stirrup_id": self.stirrup_id,
            "path": [pt.to_dict() for pt in self.path_points],
            "diameter_mm": self.diameter_mm,
            "shape": self.shape,
            "z_position": self.z_position,
            "type": "stirrup"
        }


class GeometryCalculator:
    """
    Calculates 3D geometry for reinforcement using NumPy and geomdl.

    Philosophy: Generate coordinates mathematically, not geometrically.
    The 3D model is a temporary visualization; structured data is the asset.
    """

    def __init__(self, column_height_mm: float = 3000.0):
        """
        Initialize calculator.

        Args:
            column_height_mm: Default column height for visualization
        """
        self.column_height_mm = column_height_mm

    def calculate_longitudinal_bars(
        self,
        width_mm: float,
        depth_mm: float,
        bar_diameter_mm: float,
        bar_count: int,
        bar_x_columns: int,
        bar_y_matrix: List[int],
        clear_cover_mm: float
    ) -> List[LongitudinalBarGeometry]:
        """
        Calculate coordinates for all longitudinal bars.

        Based on Colab Cell 7 logic with production enhancements.

        Args:
            width_mm: Section width (W)
            depth_mm: Section depth (D)
            bar_diameter_mm: Bar diameter
            bar_count: Total bars
            bar_x_columns: Number of columns along X
            bar_y_matrix: Bars per column
            clear_cover_mm: Concrete cover

        Returns:
            List of longitudinal bar geometries
        """
        bars: List[LongitudinalBarGeometry] = []

        # Calculate X positions (columns)
        x_positions = np.linspace(
            clear_cover_mm + bar_diameter_mm / 2,
            width_mm - clear_cover_mm - bar_diameter_mm / 2,
            bar_x_columns
        )

        bar_id = 0

        for col_index, num_bars_in_col in enumerate(bar_y_matrix):
            if num_bars_in_col == 0:
                continue

            # Calculate Y positions for this column
            if num_bars_in_col > 1:
                y_coords = np.linspace(
                    clear_cover_mm + bar_diameter_mm / 2,
                    depth_mm - clear_cover_mm - bar_diameter_mm / 2,
                    num_bars_in_col
                )
            else:
                # Single bar: center it
                y_coords = np.array([depth_mm / 2])

            current_x = x_positions[col_index]

            # Create bar geometries
            for y_coord in y_coords:
                start = Point3D(x=current_x, y=y_coord, z=0)
                end = Point3D(x=current_x, y=y_coord, z=self.column_height_mm)

                bars.append(
                    LongitudinalBarGeometry(
                        bar_id=bar_id,
                        start_point=start,
                        end_point=end,
                        diameter_mm=bar_diameter_mm
                    )
                )
                bar_id += 1

        return bars

    def calculate_rectangular_stirrup(
        self,
        internal_width_mm: float,
        internal_depth_mm: float,
        bar_diameter_mm: float,
        z_position: float,
        bend_radius_mm: Optional[float] = None
    ) -> List[Point3D]:
        """
        Calculate path points for a rectangular stirrup with filleted corners.

        Args:
            internal_width_mm: Internal clear width
            internal_depth_mm: Internal clear depth
            bar_diameter_mm: Stirrup bar diameter
            z_position: Z-coordinate (height)
            bend_radius_mm: Inside bend radius (default: 3 * bar_diameter)

        Returns:
            List of path points forming the stirrup perimeter
        """
        if bend_radius_mm is None:
            bend_radius_mm = 3 * bar_diameter_mm  # ACI minimum

        # Define corners (before fillet)
        # We'll create a simple rectangle for MVP
        # Future enhancement: Use geomdl to create exact NURBS arcs at corners

        half_w = internal_width_mm / 2
        half_d = internal_depth_mm / 2

        # Rectangular path (clockwise from bottom-left)
        points = [
            Point3D(-half_w, -half_d, z_position),  # Bottom-left
            Point3D(half_w, -half_d, z_position),   # Bottom-right
            Point3D(half_w, half_d, z_position),    # Top-right
            Point3D(-half_w, half_d, z_position),   # Top-left
            Point3D(-half_w, -half_d, z_position),  # Close path
        ]

        return points

    def calculate_stirrup_spacing_positions(
        self,
        spacing_pattern: List[Dict],
        total_height_mm: Optional[float] = None
    ) -> List[float]:
        """
        Calculate Z-positions for stirrups based on spacing pattern.

        Args:
            spacing_pattern: List of spacing items (e.g., [{"quantity": "1", "spacing": 50}, ...])
            total_height_mm: Total column height (defaults to instance height)

        Returns:
            List of Z-coordinates for each stirrup
        """
        if total_height_mm is None:
            total_height_mm = self.column_height_mm

        z_positions: List[float] = [0.0]  # Start at bottom
        current_z = 0.0

        for item in spacing_pattern:
            quantity = item["quantity"]
            spacing = item["spacing"]

            if quantity == "rest":
                # Fill remaining height
                while current_z + spacing < total_height_mm:
                    current_z += spacing
                    z_positions.append(current_z)
                break
            else:
                # Add specified number of spacings
                for _ in range(int(quantity)):
                    current_z += spacing
                    if current_z >= total_height_mm:
                        break
                    z_positions.append(current_z)

        return z_positions

    def generate_complete_geometry(
        self,
        extraction_data: dict
    ) -> Dict:
        """
        Generate complete 3D geometry from extraction data.

        This is the main entry point for geometry generation.

        Args:
            extraction_data: Validated extraction data (ColumnExtraction)

        Returns:
            Dictionary containing all geometry ready for Three.js
        """
        try:
            # Defensive checks for None values
            if extraction_data.get("geometry") is None:
                raise ValueError("geometry field is None in extraction_data")
            if extraction_data.get("longitudinal_reinforcement") is None:
                raise ValueError("longitudinal_reinforcement field is None in extraction_data")

            geometry = extraction_data["geometry"]
            concrete_specs = extraction_data.get("concrete_specifications") or {}
            long_reinforcement = extraction_data["longitudinal_reinforcement"]
            trans_reinforcement = extraction_data.get("transverse_reinforcement") or []

            # Filter out None values from lists
            trans_reinforcement = [item for item in trans_reinforcement if item is not None]
            long_reinforcement = [item for item in long_reinforcement if item is not None]
        except Exception as e:
            import json
            print(f"\n{'='*80}")
            print(f"ERROR in generate_complete_geometry:")
            print(f"Exception: {type(e).__name__}: {str(e)}")
            print(f"extraction_data type: {type(extraction_data)}")
            print(f"extraction_data content:")
            print(json.dumps(extraction_data, indent=2, default=str))
            print(f"{'='*80}\n")
            raise

        width = geometry["width_mm"]
        depth = geometry["depth_mm"]
        cover = concrete_specs.get("clear_cover_mm") or 40.0

        result = {
            "longitudinal_bars": [],
            "stirrups": [],
            "section": {
                "width_mm": width,
                "depth_mm": depth,
                "height_mm": self.column_height_mm,
                "cover_mm": cover
            }
        }

        # 1. Generate longitudinal bars
        for long_bar_group in long_reinforcement:
            bars = self.calculate_longitudinal_bars(
                width_mm=width,
                depth_mm=depth,
                bar_diameter_mm=long_bar_group.get("bar_diameter_mm") or 25.4,  # Default to 1 inch
                bar_count=long_bar_group["bar_count"],
                bar_x_columns=long_bar_group["bar_x_columns"],
                bar_y_matrix=long_bar_group["bar_y_matrix"],
                clear_cover_mm=cover
            )
            result["longitudinal_bars"].extend([bar.to_dict() for bar in bars])

        # 2. Generate stirrups
        for stirrup_data in trans_reinforcement:
            if stirrup_data["stirrup_shape"] == "rectangular":
                # Get internal dimensions
                stirrup_dims = stirrup_data.get("stirrup_dimensions") or {}
                if stirrup_dims:
                    internal_w = stirrup_dims.get("span_width_mm", width - 2 * cover)
                    internal_d = stirrup_dims.get("span_depth_mm", depth - 2 * cover)
                else:
                    internal_w = width - 2 * cover
                    internal_d = depth - 2 * cover

                # Calculate Z positions based on spacing
                z_positions = self.calculate_stirrup_spacing_positions(
                    stirrup_data["spacing_mm"]
                )

                # Generate stirrup at each Z position
                stirrup_diameter = stirrup_data.get("bar_diameter_mm") or 12.7  # Default to 1/2 inch
                for idx, z_pos in enumerate(z_positions):
                    path_points = self.calculate_rectangular_stirrup(
                        internal_width_mm=internal_w,
                        internal_depth_mm=internal_d,
                        bar_diameter_mm=stirrup_diameter,
                        z_position=z_pos
                    )

                    stirrup = StirrupGeometry(
                        stirrup_id=f"{stirrup_data.get('stirrup_id', 'stirrup')}_{idx}",
                        path_points=path_points,
                        diameter_mm=stirrup_diameter,
                        shape=stirrup_data["stirrup_shape"],
                        z_position=z_pos
                    )
                    result["stirrups"].append(stirrup.to_dict())

        return result


# Helper function for NURBS curve generation (future enhancement)
def create_circular_arc_nurbs(
    start_point: np.ndarray,
    end_point: np.ndarray,
    radius: float,
    center: np.ndarray
) -> NURBS.Curve:
    """
    Create a NURBS curve for a circular arc using geomdl.

    This is a placeholder for future enhancement to generate exact
    circular arcs at stirrup corners.

    Args:
        start_point: Arc start point [x, y, z]
        end_point: Arc end point
        radius: Arc radius
        center: Arc center point

    Returns:
        geomdl NURBS curve
    """
    # Create a degree-2 NURBS curve for circular arc
    curve = NURBS.Curve()
    curve.degree = 2

    # For a circular arc, we need 3 control points with weights
    # This is simplified; full implementation would calculate exact control points
    mid_point = (start_point + end_point) / 2
    mid_point = center + (mid_point - center) * (radius / np.linalg.norm(mid_point - center))

    curve.ctrlpts = [
        start_point.tolist(),
        mid_point.tolist(),
        end_point.tolist()
    ]

    # Weights for circular arc (rational B-spline)
    curve.weights = [1.0, np.cos(np.pi / 4), 1.0]  # For 90-degree arc

    # Knot vector for degree 2, 3 control points
    curve.knotvector = [0, 0, 0, 1, 1, 1]

    return curve
