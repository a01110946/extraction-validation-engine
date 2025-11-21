# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered reinforced concrete extraction and validation engine** that transforms 2D construction drawings into validated 3D data through a four-stage pipeline:

1. **Extraction (Gemini 3.0 Pro)** → Structured data from images
2. **Validation (ACI 318-19)** → Auto-healing with engineering defaults
3. **Geometry (NumPy + geomdl)** → Headless 3D coordinate calculation
4. **Visualization (Three.js)** → Interactive web validation

**Core Philosophy:** "Illustration as Code" - The structured JSON data is the asset, not the 3D model. The visualization is temporary proof that the data is correct.

## Development Commands

### Backend (Python 3.11+)

```bash
cd backend

# Install dependencies (development mode)
pip install -e .
pip install -e ".[dev]"  # Includes pytest, black, ruff, mypy

# Start server
python main.py
# OR with uvicorn directly
uvicorn main:app --reload

# Run tests
pytest tests/

# Code quality
black src/                    # Format code
ruff check src/               # Lint
mypy src/                     # Type check
```

**Backend runs at:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

### Frontend (Node.js 18+)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

**Frontend runs at:** `http://localhost:5173`

### Prerequisites

- **MongoDB:** Must be running (`mongod` or MongoDB Atlas)
- **Environment:** Copy `backend/.env.example` to `backend/.env` and add `GOOGLE_API_KEY`

## Architecture

### Backend Structure (`backend/src/`)

```
models/
├── schemas.py              # Pydantic models (ColumnExtraction, LongitudinalReinforcement, etc.)

services/
├── gemini_extractor.py     # AI extraction using Gemini 3.0 Pro
├── aci_validator.py        # ACI 318-19 validation/healing engine
├── geometry_calculator.py  # NumPy-based 3D coordinate generation

api/
├── routes.py               # FastAPI endpoints (8 routes)

core/
├── config.py               # Pydantic settings (env vars)
├── database.py             # MongoDB async driver (Motor)
```

### Frontend Structure (`frontend/src/`)

```
components/
├── ImageUpload.jsx         # Drag-and-drop with react-dropzone
├── Viewer3D.jsx            # Three.js viewer (@react-three/fiber)
├── EditForm.jsx            # Real-time editing with live geometry updates

services/
├── api.js                  # Axios client (8 API methods)

store/
├── useExtractionStore.js   # Zustand state management
```

### Key Data Flow

1. **Upload Image** → `POST /api/v1/extract`
   - Gemini extracts structured data
   - ACI validator auto-heals missing values
   - Returns `ColumnExtraction` JSON

2. **Generate Geometry** → `POST /api/v1/geometry`
   - Input: Validated extraction data
   - NumPy calculates 3D coordinates
   - Returns geometry for Three.js (bars, stirrups, section)

3. **Edit & Regenerate** → Frontend calls `/geometry` on field change
   - Live updates in Three.js viewer
   - No database save until user clicks "Save & Validate"

4. **Save** → `POST /api/v1/extractions`
   - Stores complete extraction + metadata in MongoDB
   - Includes validation status and notes

### Pydantic Schema Hierarchy

```
ColumnExtraction
├── element_identification: ElementIdentification
├── geometry: Geometry (width, depth, shape)
├── concrete_specs: ConcreteSpecs (fc', cover)
├── longitudinal_reinforcement: LongitudinalReinforcement
│   ├── bar_count: int (total bars)
│   ├── bar_x_columns: int (columns in X direction)
│   ├── bar_y_matrix: List[int] (bars per column, must sum to bar_count)
│   └── bar_diameter_mm: float
└── transverse_reinforcement: List[TransverseReinforcement]
    ├── stirrup_type: "main_stirrup" | "intermediate_stirrup" | etc.
    ├── spacing_mm: List[SpacingItem] (e.g., "10@100", "rest@250")
    └── stirrup_dimensions: StirrupDimensions
```

**Critical Validator:** `bar_y_matrix` must sum to `bar_count` (enforced in Pydantic)

### ACI 318-19 Validation Rules

The `aci_validator.py` service implements code-compliant defaults:

- **Hook lengths:**
  - 90° standard: 12db
  - 180° standard: max(4db, 2.5")
  - 135° seismic: max(6db, 3.0")

- **Bend diameters:**
  - #3-#8: 6db minimum
  - #9-#11: 8db
  - #14-#18: 10db

- **Cover requirements:** Based on `ExposureCondition` enum
  - `CAST_AGAINST_EARTH`: 75mm (#5 and smaller), 50mm (larger)
  - `WEATHER_EXPOSED`: 50mm (#6 and larger), 40mm (smaller)
  - `INTERIOR_BEAMS_COLUMNS`: 40mm default

**Auto-Healing:** If values are missing, validator injects defaults and returns `corrections` list

### Geometry Calculation Algorithm

**Longitudinal Bars (`geometry_calculator.py`):**
1. Calculate effective dimensions (subtract cover × 2)
2. Distribute bars in X-axis columns using `np.linspace`
3. For each column, distribute bars in Y-axis
4. Generate start/end coordinates (Z=0 to Z=column_height)

**Stirrups:**
1. Parse spacing patterns: `SpacingItem(quantity="10", spacing=100)` → 10 spaces at 100mm
2. Handle `quantity="rest"` for remaining length
3. Generate rectangular path points (4 corners)
4. Calculate Z-positions for each stirrup instance

**Output format for Three.js:**
```json
{
  "longitudinal_bars": [
    {"bar_id": 0, "start": {x, y, z}, "end": {x, y, z}, "diameter_mm": 15.875}
  ],
  "stirrups": [
    {"stirrup_id": "stirrup_0", "path": [{x, y, z}, ...], "z_position": 0}
  ],
  "section": {"width_mm": 420, "depth_mm": 700, "height_mm": 3000}
}
```

### Three.js Rendering (`Viewer3D.jsx`)

- **Longitudinal bars:** `CylinderGeometry` (red metallic material)
- **Stirrups:** Polyline segments with `CylinderGeometry` (blue material)
- **Concrete section:** Wireframe `BoxGeometry` (gray)
- **Scene:** Orbit controls, grid helper (500mm cells), ambient + point lighting

## Configuration

### Environment Variables (`backend/.env`)

Required:
- `GOOGLE_API_KEY` - Gemini 3.0 API key (from Google AI Studio)

Optional (with defaults):
- `MONGODB_URL` - MongoDB connection string (default: `mongodb://localhost:27017`)
- `MONGODB_DATABASE` - Database name (default: `extraction_validation`)
- `API_HOST` - Server host (default: `0.0.0.0`)
- `API_PORT` - Server port (default: `8000`)
- `CORS_ORIGINS` - Comma-separated allowed origins (default: `http://localhost:5173,http://localhost:3000`)
- `GEMINI_MODEL` - Model name (default: `gemini-3-pro-preview`)
- `GEMINI_THINKING_LEVEL` - Thinking level (default: `HIGH`)
- `DEFAULT_COLUMN_HEIGHT_MM` - Default height (default: `3000.0`)

### Frontend Environment (`frontend/.env.local`)

Optional:
- `VITE_API_URL` - Backend URL (default: `http://localhost:8000`)

## Known Issues & Technical Debt

**Critical (Phase 4 priorities):**
- No authentication - API is public
- No input validation on file uploads
- No rate limiting
- Zero test coverage

**Medium:**
- Hardcoded column height (should be extracted)
- Stirrup corners not filleted (sharp instead of ACI-compliant bends)
- No undo/redo in EditForm

**See `PROJECT_STATUS.md` for complete Phase 4 roadmap**

## Development Patterns

### Adding New Structural Elements (e.g., Beams, Slabs)

1. **Define Pydantic schema** in `backend/src/models/schemas.py`
   - Follow prescriptive pattern (no "draw this", use parameters)
   - Add validators for physical constraints

2. **Extend ACI validator** in `backend/src/services/aci_validator.py`
   - Add element-specific code rules
   - Implement auto-healing logic

3. **Add geometry calculator** method in `backend/src/services/geometry_calculator.py`
   - Use NumPy for coordinate math
   - Return Three.js-compatible format

4. **Update API routes** in `backend/src/api/routes.py`
   - Add extraction/validation/geometry endpoints

5. **Create React component** in `frontend/src/components/`
   - 3D viewer component
   - Edit form component

### Testing Strategy (When Implementing)

**Backend unit tests (`pytest`):**
- Mock Gemini API responses (use `pytest-asyncio`)
- Test ACI calculations (hook lengths, cover, etc.)
- Test geometry edge cases (single bar, odd counts, large dimensions)
- Test Pydantic validators (bar_y_matrix sum, etc.)

**Frontend tests (`vitest` + React Testing Library):**
- Component rendering
- User interactions (drag-and-drop, form edits)
- API service mocking

**Integration tests:**
- End-to-end workflow: Upload → Extract → Validate → Save
- Use FastAPI `TestClient` with test database

## Working with Gemini Extraction

**System prompt location:** `backend/src/services/gemini_extractor.py`

**Key extraction principles:**
1. **Prescriptive, not descriptive** - Ask AI to fill a form, not "draw"
2. **Use `response_schema`** - Enforce Pydantic model structure
3. **Thinking mode** - Set `GEMINI_THINKING_LEVEL=HIGH` for complex drawings
4. **Handle failures gracefully** - Gemini may timeout or hallucinate

**Debugging extractions:**
- Check raw Gemini response in logs
- Validate against Pydantic schema manually
- Test with sample images from `notebooks/`

## Prescriptive Bar Placement

Instead of asking AI to place bars spatially, we use a deterministic schema:

```python
bar_count = 14           # Total bars
bar_x_columns = 3        # 3 columns in X direction
bar_y_matrix = [6, 2, 6] # Bars per column (must sum to 14)
```

This allows exact coordinate calculation:
- X positions: `np.linspace(0, effective_width, bar_x_columns)`
- Y positions per column: `np.linspace(0, effective_depth, bars_in_column)`

**Advantage:** No ambiguity, no hallucinations, mathematically precise

## MongoDB Collections

**Collection:** `extractions`

**Document structure:**
```json
{
  "_id": ObjectId,
  "element_identification": {...},
  "geometry": {...},
  "concrete_specs": {...},
  "longitudinal_reinforcement": {...},
  "transverse_reinforcement": [...],
  "validated": false,           // Human validation flag
  "validation_notes": null,     // Human comments
  "saved_at": ISODate,
  "updated_at": ISODate         // On updates
}
```

**Indexes to add (Phase 4):**
- `element_identification.element_id`
- `extracted_at`
- Compound: `validated` + `extracted_at`

## Common Tasks

### Running the full stack locally

```bash
# Terminal 1 - MongoDB
mongod

# Terminal 2 - Backend
cd backend
python main.py

# Terminal 3 - Frontend
cd frontend
npm run dev

# Open browser: http://localhost:5173
```

### Adding a new ACI rule

1. Edit `backend/src/services/aci_validator.py`
2. Add rule to `heal_extraction()` or create new helper method
3. Return correction message in `corrections` list
4. Test with sample extraction data

### Modifying 3D visualization

1. Edit `frontend/src/components/Viewer3D.jsx`
2. Three.js objects use `@react-three/fiber` declarative syntax
3. Hot reload will update automatically
4. Check geometry data structure from `/api/v1/geometry` response

### Changing bar placement algorithm

1. Edit `backend/src/services/geometry_calculator.py`
2. Modify `generate_longitudinal_bars()` method
3. Keep output format compatible with Three.js viewer
4. Test with various `bar_x_columns` and `bar_y_matrix` configurations

## Reference Documentation

- **Quick Start:** `QUICKSTART.md` - 5-minute setup guide
- **Project Status:** `PROJECT_STATUS.md` - MVP completion, Phase 4-5 roadmap
- **Project Definition:** `docs/project-definition-and-architectural-blueprint.md` - Architectural philosophy
- **Research:** `docs/research/` - ACI standards, geometry libraries
- **Backend README:** `backend/README.md`
- **Frontend README:** `frontend/README.md`
- **Original Notebook:** `notebooks/Gemini_3_Column_original.ipynb` - Colab experiment

## Phase Roadmap (See PROJECT_STATUS.md for details)

- **Phase 1-3:** ✅ Complete (MVP working)
- **Phase 4:** Production hardening (testing, error handling, performance, security, deployment)
- **Phase 5:** BIM integration (Speckle, Grasshopper, Revit, IFC export)
