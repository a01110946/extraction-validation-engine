# Extraction Validation Engine

> AI-powered reinforced concrete extraction and validation platform for construction engineering.

**Philosophy:** "Illustration as Code" - The 3D model is not the asset. The **structured data** is the asset. The 3D visualization is temporary proof that the data is correct.

![Project Status](https://img.shields.io/badge/status-MVP-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18+-blue)

---

## 🎯 Overview

This platform solves the **semantic gap** in AEC data workflows by combining:

1. **AI Extraction (Gemini 3.0 Pro):** Extracts structured data from 2D construction drawings
2. **Code Validation (ACI 318-19):** Auto-heals missing data with engineering defaults
3. **Headless Geometry (NumPy + geomdl):** Generates 3D coordinates mathematically (no CAD kernel)
4. **Web Visualization (Three.js):** Hardware-accelerated validation interface

### The Four-Stage Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│   Stage 1   │───▶│   Stage 2    │───▶│    Stage 3     │───▶│   Stage 4    │
│ Extraction  │    │  Validation  │    │  Geometry Calc │    │ Visualization│
│  (Gemini)   │    │  (ACI 318)   │    │ (NumPy/geomdl) │    │  (Three.js)  │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘
  2D PDF/Image        JSON + Defaults      Coordinates          3D Web View
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** (local or Atlas)
- **Google API Key** (for Gemini 3)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/extraction-validation-engine.git
cd extraction-validation-engine
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Start MongoDB (if local)
mongod

# Run backend server
python main.py
```

Backend runs at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 4. Test with Sample Data

1. Navigate to `http://localhost:5173`
2. Drag and drop a column cross-section image from `notebooks/` (if you have sample images)
3. Wait for extraction and geometry generation
4. Review the 3D visualization
5. Edit any fields as needed
6. Click "Save & Validate"

---

## 📁 Project Structure

```
extraction-validation-engine/
├── backend/                # FastAPI Python backend
│   ├── src/
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   ├── gemini_extractor.py    # AI extraction
│   │   │   ├── aci_validator.py       # Code validation
│   │   │   └── geometry_calculator.py # Math engine
│   │   ├── api/           # FastAPI routes
│   │   └── core/          # Config & database
│   ├── tests/
│   ├── main.py
│   └── pyproject.toml
│
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── ImageUpload.jsx
│   │   │   ├── Viewer3D.jsx      # Three.js viewer
│   │   │   └── EditForm.jsx
│   │   ├── services/      # API client
│   │   ├── store/         # Zustand state
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── notebooks/              # Jupyter/Colab experiments
│   └── Gemini_3_Column_original.ipynb
│
├── docs/                   # Documentation
│   ├── project-definition-and-architectural-blueprint.md
│   └── research/           # Technical research docs
│
└── README.md
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **AI Extraction** | Gemini 3.0 Pro | Structured data extraction from images |
| **Backend** | FastAPI + Python | API server and business logic |
| **Validation** | ACI 318-19 | Code-compliant auto-correction |
| **Geometry** | NumPy + geomdl | Headless coordinate calculation |
| **Database** | MongoDB | Document storage |
| **Frontend** | React + Vite | Web interface |
| **3D Rendering** | Three.js + @react-three/fiber | Hardware-accelerated visualization |

---

## 📖 Key Concepts

### "Illustration as Code"

Traditional Scan-to-BIM tools try to generate CAD geometry directly. This fails because:
- AI hallucinates (7 bars instead of 8)
- Geometry is hard to validate
- CAD kernels are expensive and slow

**Our approach:**
1. Extract **parameters** (bar count, diameter, spacing) → Pydantic schemas
2. Validate parameters → ACI 318 rules
3. Calculate **coordinates** → NumPy (serverless, instant)
4. Visualize **temporarily** → Three.js (user approves)
5. Save **JSON** → MongoDB (the real asset)
6. Instantiate BIM → Later, via Grasshopper/Speckle (Phase 5)

### Prescriptive Bar Placement

Instead of asking AI to "draw" rebar, we ask it to fill a form:

```json
{
  "bar_count": 14,
  "bar_x_columns": 3,
  "bar_y_matrix": [6, 2, 6]
}
```

This deterministic schema lets us calculate exact coordinates mathematically.

---

## 🎨 Screenshots

### Upload Interface
*Drag-and-drop image upload with automatic extraction*

### 3D Validation View
*Interactive Three.js viewer showing longitudinal bars (red) and stirrups (blue)*

### Edit Form
*Real-time data editing with ACI 318 correction feedback*

---

## 🧪 Development

### Backend Testing

```bash
cd backend
pytest tests/
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Code Quality

```bash
# Backend
black backend/src/
ruff check backend/src/
mypy backend/src/

# Frontend
npm run lint
```

---

## 📚 Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Project Definition](docs/project-definition-and-architectural-blueprint.md)
- [Research Documents](docs/research/)

---

## 🗺️ Roadmap

### Phase 1: Data Core ✅
- [x] Pydantic schemas
- [x] ACI 318 validator
- [x] Gemini extraction

### Phase 2: Math Engine ✅
- [x] NumPy coordinate calculation
- [x] geomdl NURBS curves
- [x] Stirrup spacing logic

### Phase 3: Web Visualizer ✅
- [x] React + Vite app
- [x] Three.js 3D viewer
- [x] Edit form UI

### Phase 4: Production (In Progress)
- [ ] Unit tests
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] User authentication

### Phase 5: BIM Integration (Future)
- [ ] Speckle streams
- [ ] Grasshopper scripts
- [ ] Rhino.Inside.Revit
- [ ] Native Revit families

---

## 🤝 Contributing

Contributions welcome! Please read the project definition document first to understand the architectural philosophy.

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- Google Gemini team for multimodal AI capabilities
- ACI 318-19 for structural concrete code standards
- Three.js community for WebGL rendering
- Open-source contributors of NumPy, geomdl, FastAPI, and React

---

## 📧 Contact

For questions or collaboration inquiries, please open an issue on GitHub.

---

**Built with the philosophy that code compliance should be enforced by software, not spreadsheets.**
