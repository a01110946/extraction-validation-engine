# Extraction Validation Engine - Backend

AI-powered reinforced concrete extraction and validation backend built with FastAPI, Gemini 3, and MongoDB.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- Google API Key (for Gemini 3)

### Installation

1. **Install dependencies:**

```bash
cd backend
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

2. **Set up environment variables:**

```bash
cp .env.example .env
```

Edit `.env` and add your `GOOGLE_API_KEY`.

3. **Start MongoDB** (if running locally):

```bash
mongod
```

4. **Run the server:**

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## 📚 API Documentation

Once running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🎯 Key Endpoints

### `POST /api/v1/extract`
Upload an image and extract column data using Gemini 3.

**Request:**
- `file`: Image file (multipart/form-data)
- `auto_validate`: Boolean (default: true)

**Response:**
```json
{
  "success": true,
  "data": { /* ColumnExtraction object */ },
  "corrections_applied": ["list of ACI corrections"],
  "extracted_at": "2025-11-21T00:00:00"
}
```

### `POST /api/v1/validate`
Validate and heal extraction data using ACI 318 rules.

### `POST /api/v1/geometry`
Generate 3D geometry from extraction data.

**Response:**
```json
{
  "success": true,
  "geometry": {
    "longitudinal_bars": [...],
    "stirrups": [...],
    "section": { /* dimensions */ }
  }
}
```

### `POST /api/v1/extractions`
Save validated extraction to MongoDB.

### `GET /api/v1/extractions`
List all saved extractions.

## 🏗️ Architecture

```
backend/
├── src/
│   ├── models/          # Pydantic schemas
│   ├── services/        # Business logic
│   │   ├── gemini_extractor.py
│   │   ├── aci_validator.py
│   │   └── geometry_calculator.py
│   ├── api/             # FastAPI routes
│   ├── core/            # Config & database
│   └── utils/           # Helper functions
├── tests/               # Unit tests
├── main.py              # FastAPI app
└── pyproject.toml       # Dependencies
```

## 🧪 Testing

```bash
pytest tests/
```

## 📝 Development

Format code:
```bash
black src/
```

Lint:
```bash
ruff check src/
```

Type check:
```bash
mypy src/
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | **Required** |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `extraction_validation` |
| `API_PORT` | Server port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

## 🎓 Key Concepts

### The Four-Stage Pipeline

1. **Extraction (Gemini 3):** AI extracts structured data from drawings
2. **Validation (ACI 318):** Auto-heal missing data with code defaults
3. **Geometry (NumPy + geomdl):** Calculate 3D coordinates mathematically
4. **Visualization (Frontend):** Render in Three.js for human review

### "Illustration as Code"

The 3D model is **not** the asset. The **structured JSON data** is the asset. The 3D visualization is a temporary proof that the data is correct.

## 📖 Related Documentation

- [Project Definition](../docs/project-definition-and-architectural-blueprint.md)
- [Research Documents](../docs/research/)
- [Colab Notebook](../notebooks/Gemini_3_Column_original.ipynb)
