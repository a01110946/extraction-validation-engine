# Extraction Validation Engine - Frontend

React + Vite frontend with Three.js visualization for AI-powered reinforced concrete validation.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn

### Installation

1. **Install dependencies:**

```bash
cd frontend
npm install
```

2. **Start development server:**

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

## 🏗️ Architecture

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── ImageUpload.jsx    # Drag-and-drop upload
│   │   ├── Viewer3D.jsx       # Three.js 3D viewer
│   │   └── EditForm.jsx       # Data editing form
│   ├── services/         # API client
│   │   └── api.js             # Backend communication
│   ├── store/            # State management
│   │   └── useExtractionStore.js  # Zustand store
│   ├── App.jsx           # Main app component
│   └── main.jsx          # Entry point
├── package.json
└── vite.config.js
```

## 🎨 Key Technologies

- **React 18:** UI framework
- **Vite:** Build tool and dev server
- **@react-three/fiber:** React renderer for Three.js
- **@react-three/drei:** Three.js helpers and components
- **Three.js:** WebGL 3D rendering
- **Zustand:** Lightweight state management
- **Axios:** HTTP client
- **react-dropzone:** Drag-and-drop file upload

## 🔧 Development

### Build for production:

```bash
npm run build
```

### Preview production build:

```bash
npm run preview
```

### Lint:

```bash
npm run lint
```

## 📦 Components

### `ImageUpload`
- Drag-and-drop image upload
- Triggers backend extraction automatically
- Displays loading state during processing

### `Viewer3D`
- Hardware-accelerated 3D visualization using WebGL
- Renders longitudinal bars as red cylinders
- Renders stirrups as blue polylines
- Concrete section outline
- Interactive camera controls (orbit, pan, zoom)

### `EditForm`
- Edit extracted data fields
- Real-time geometry regeneration on field changes
- Display ACI 318 auto-corrections
- Save validated extractions to database

## 🎯 Workflow

1. **Upload:** User drops image → Gemini extracts data
2. **Validate:** ACI 318 rules auto-heal missing data
3. **Visualize:** NumPy calculates coordinates → Three.js renders
4. **Edit:** User modifies data → Geometry regenerates instantly
5. **Save:** Store validated extraction to MongoDB

## 🔗 API Integration

The frontend communicates with the FastAPI backend via:

- `POST /api/v1/extract` - Extract from image
- `POST /api/v1/geometry` - Generate 3D geometry
- `POST /api/v1/extractions` - Save to database
- `GET /api/v1/extractions` - List saved extractions

## 🌐 Environment Variables

Create `.env.local` (optional):

```env
VITE_API_URL=http://localhost:8000
```

## 📖 Related Documentation

- [Backend README](../backend/README.md)
- [Project Definition](../docs/project-definition-and-architectural-blueprint.md)
