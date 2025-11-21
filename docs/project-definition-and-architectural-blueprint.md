Based on our extensive research and your specific architectural requirements, I have prepared a comprehensive **Project Definition & Architectural Blueprint**.

These documents are written to serve as the "North Star" for your development team. They define the **what**, the **how**, and most importantly, the **why** behind every technical decision we have made, specifically addressing the shift from heavy CAD kernels to a lightweight, data-driven web stack.

---

# 📁 DOCUMENT SET: Structural AI Validation Engine
**Date:** November 21, 2025
**Version:** 1.0-Executive
**Status:** Approved for Implementation

---

## 📄 Document 1: Executive Vision & Problem Statement

### 1.1 The Core Problem: The "Semantic Gap"
The AEC industry is facing a data interoperability crisis. We have legacy data locked in 2D PDF blueprints (pixels) and a requirement to produce high-fidelity Building Information Models (BIM) in Revit (parametric constraints).

Current "Scan-to-BIM" or "PDF-to-BIM" solutions fail because they treat the problem as a **geometric** translation. They try to "trace" lines into meshes. This results in "dumb" geometry—shapes that look like columns but lack the engineering intelligence (load capacity, cover rules, rebar grading) required for analysis and fabrication.

Furthermore, Artificial Intelligence (LLMs/Vision Models) is probabilistic. A model like Gemini 3.0 is incredibly powerful at extracting text and recognizing patterns, but it hallucinates. It might see 7 bars where there are 8, or misread a spacing digit. We cannot pipe AI output directly into a construction database without a **deterministic validation layer**.

### 1.2 The Solution: "Illustration as Code"
We are building a **Headless Validation Engine**.
Instead of trying to run heavy CAD software (Revit/Rhino) in the browser, we are building a lightweight, web-based "Visual Validator."

This tool does not *create* the final BIM element. It creates a **Visual Proxy**—a mathematically accurate, 3D representation derived purely from code (Python/NumPy). This allows a human engineer to visually verify the AI's extraction. Once the human approves the visual, we discard the geometry and save the **Parameters (JSON)**.

**The Philosophy:** The 3D model is not the asset. The **Structured Data (Pydantic Schema)** is the asset. The 3D model is just a temporary visualization of that data.

### 1.3 Business Value
1.  **Speed:** Eliminates manual modeling from scratch. We move from "Modeling" to "Reviewing."
2.  **Integrity:** Enforces ACI 318 compliance *before* the data ever reaches Revit. We stop "illegal" geometry at the gate.
3.  **Scalability:** By removing heavy CAD kernels from the web layer, the application runs on any browser, anywhere, with zero server-side licensing costs for geometry generation.

---

## 📄 Document 2: Technical Architecture & Workflow

### 2.1 The "Four-Stage" Data Lifecycle

#### Stage 1: The Extraction (The "Brain")
* **Input:** 2D PDF / Images of Cross-Sections.
* **Engine:** Gemini 3.0 (Multimodal LLM).
* **Mechanism:** We use **Pydantic** to force the AI to output structured JSON.
* **Innovation:** We do not ask the AI to "draw." We ask it to "fill the form." (e.g., `bar_count: 8`, `spacing: 200`).
* *Reference:* Your Google Colab experiment successfully proved this stage. The schema is the contract.

#### Stage 2: The Logic & Auto-Correction (The "Lawyer")
* **Input:** Raw JSON from Stage 1.
* **Engine:** Python (Pydantic Validators + Custom ACI Logic).
* **Mechanism:**
    * The system detects missing data (e.g., AI missed the hook length).
    * **ACI 318 Injection:** The system calculates the mandatory defaults (e.g., `hook_length = 12 * bar_diameter`).
    * **Validation:** Checks for physical impossibilities (e.g., do 8 bars actually fit in a 300mm width?).
* **Output:** A "Healed" JSON object that is mathematically sound.

#### Stage 3: The Visual Validation (The "Viewer")
* **Input:** Healed JSON.
* **Engine:** **NumPy + Geomdl** (Math) & **Three.js** (Rendering).
* **Mechanism:**
    * **Serverless Math:** Python (via Pyodide) uses NumPy to calculate the vector algebra (tangency points, centers of bends) and Geomdl to generate NURBS curves.
    * **GPU Rendering:** Three.js takes these curves and renders them as `TubeGeometry` or `InstancedMesh`.
    * **User Action:** The user sees the 3D cage. If it looks wrong, they update the *number* in the sidebar. The 3D regenerates instantly.
* **Decision:** We prioritize **Latency** (speed of update) over **CAD Precision** in this step.

#### Stage 4: The Instantiation (The "Factory")
* **Input:** Validated, Approved JSON (stored in Database).
* **Engine:** **Grasshopper + Rhino.Inside.Revit + Speckle**.
* **Mechanism:**
    * Grasshopper pulls the JSON.
    * It uses the JSON to drive parametric creation scripts.
    * It instantiates **Native Revit Families** (not dumb meshes).
* **Result:** A fully documented, fabrication-ready Revit model.

---

## 📄 Document 3: Strategic Decisions & The "Discard Log"

This section documents *why* we chose specific tools and explicitly *why* we rejected others. This prevents future team members from re-litigating settled architectural decisions.

### 3.1 The "Visualization" Decision
**Decision:** Use **Three.js** (WebGL) for the viewer, driven by **NumPy** math.
**Discarded:** **Matplotlib** (Matplotly).
* **Reasoning:** Your Colab experiment used Matplotlib. It works for static generation, but it is CPU-bound. In a web app, if a user rotates the model or edits a bar, Matplotlib has to re-render the entire image. This creates "lag." Three.js runs on the GPU, allowing 60 FPS interaction even with thousands of bars.
* **Exceptions:** We *will* keep Matplotlib logic in reserve for generating **PDF Reports** (Bar Bending Schedules) where static, vector-perfect quality is needed for printing.

### 3.2 The "Geometry Kernel" Decision
**Decision:** Use **NumPy + Geomdl** (Open Source, Lightweight).
**Discarded:** **Rhino.Compute** (Server-Side CAD).
* **Reasoning:** Rhino.Compute is powerful but introduces two fatal flaws for this specific web app:
    1.  **Cost:** It charges per core-hour. Scaling to thousands of users becomes expensive.
    2.  **Latency:** Every time a user changes a value, we must send data to a server, wait for Rhino to think, and send a mesh back. This round-trip (300ms+) kills the "instant feel" of the app.
* **Alternative:** By using NumPy in the browser (via WebAssembly/Pyodide), we get **Zero Latency** calculation for free.

### 3.3 The "2D Drawing" Decision
**Decision:** Test **Maker.js** (Client-side) vs. **ezdxf** (Server-side).
* **Reasoning:** We are undecided on the user experience for 2D.
    * *Maker.js* allows instant 2D drafting in the browser (great for quick checks).
    * *ezdxf* generates CAD-standard `.dxf` files (great for final export).
* **Strategy:** We will implement a simple Maker.js viewer for the UI, but use `ezdxf` in the backend to generate the downloadable files for the engineers.

---

## 📄 Document 4: Implementation Roadmap (High Level)

### Phase 1: The "Healed" Data Core
* **Goal:** Define the Single Source of Truth.
* **Tasks:**
    1.  Finalize the Pydantic Schemas (incorporating the `bar_x_columns` / `bar_y_matrix` logic from your Colab).
    2.  Implement the `ACIDefaults` class (the auto-injector for hook lengths and cover).
    3.  Test: Feed raw Gemini output into the Validator and verify it outputs a "complete" JSON without crashing.

### Phase 2: The "Headless" Math Engine
* **Goal:** Generate coordinates without a CAD engine.
* **Tasks:**
    1.  Port your Colab `calculate_bar_coordinates` logic into a standalone Python module.
    2.  Integrate `geomdl` to handle the bend radii (fillets) mathematically.
    3.  Ensure this script outputs a clean list of points/vectors (JSON) that a frontend can understand.

### Phase 3: The Web Visualizer
* **Goal:** See the rebar.
* **Tasks:**
    1.  Set up a React/Vue frontend.
    2.  Implement Three.js viewer.
    3.  Create the "Data-to-Mesh" bridge: Function that takes Phase 2 JSON and creates `TubeGeometry` in Three.js.

### Phase 4: The Loop
* **Goal:** Edit and Save.
* **Tasks:**
    1.  Build the UI Sidebars (Inputs for diameter, spacing, counts).
    2.  Connect UI inputs to the Phase 2 Math Engine.
    3.  Implement the "Save to Database" button.

### Phase 5: The Bridge (Post-MVP)
* **Goal:** Revit Integration.
* **Tasks:**
    1.  Set up Speckle streams.
    2.  Build the Grasshopper script to pull JSON and drive `Rhino.Inside.Revit`.

---

**Closing Note:**
We are building a tool that separates **Engineering Logic** (Python) from **Geometric Representation** (Three.js). By refusing to couple these two tightly, we gain speed, flexibility, and full ownership of our technology stack.