
# **Architectural Feasibility of Lightweight Geometric Kernels: Implementing Rebar Detailing via NumPy, Matplotlib, and NURBS-Python**

## **1\. Executive Summary**

The architectural paradigm of Architecture, Engineering, and Construction (AEC) software is currently undergoing a significant tectonic shift, moving away from monolithic, desktop-bound CAD kernels toward distributed, web-native, and lightweight computational stacks. This transition is driven by the industry's increasing demand for cloud collaboration, accessibility across devices, and the cost-inefficiency of licensing heavy proprietary geometric engines for tasks that do not require their full, bloat-heavy feature sets. The specific inquiry regarding the feasibility of utilizing **NumPy** and **Matplotlib**—supplemented by **geomdl (NURBS-Python)**—to generate and visualize reinforced concrete (rebar) geometry represents a critical investigation into this emerging "headless" CAD architecture.

The traditional reliance on heavy geometric kernels—such as Parasolid, ACIS, or the proprietary engines embedded within software like Revit, Tekla Structures, and Allplan—imposes severe constraints on modern web application development. These constraints manifest as prohibitive licensing costs, significant server-side compute overhead, and a complete lack of portability to client-side browser environments. Developers are forced to run geometry engines on backend servers, introducing latency and severing the interactive loop required for responsive design tools. Replacing these heavyweight dependencies with a pure Python stack leveraging scientific computing libraries offers a compelling alternative for domain-specific tasks like rebar detailing, where the geometric scope is constrained and well-defined.

This comprehensive report concludes that generating parametrically accurate, filleted rebar shapes using **NumPy** and **geomdl** is not only feasible but highly efficient for creating a lightweight, portable logic layer. The mathematical foundations of rebar detailing—primarily linear algebra for path definition and NURBS for fillet generation—can be fully replicated using these open-source libraries without the overhead of a B-Rep modeler. However, utilizing **Matplotlib** for the *interactive* component of a web application presents significant friction regarding user experience (UX) and 3D manipulation compared to WebGL-native libraries like Three.js. While Matplotlib excels at generating static, vector-based fabrication documentation (Bar Bending Schedules), it lacks the hardware acceleration and event-handling architecture required for a responsive 3D viewport.

Therefore, a hybrid architecture is identified as the optimal pathway: Python (via NumPy and geomdl) handles the *generative logic*—the "mathematical truth" of the rebar—while a dedicated web visualizer (Three.js) handles the interactive rendering. This logic layer can be pushed to the client-side using **Pyodide** (WebAssembly), creating a zero-latency, serverless CAD experience. This document provides an exhaustive technical analysis of the mathematical implementation of fillets via vector algebra, the extensive capabilities of the NURBS-Python ecosystem, the architectural integration of Pyodide for browser-side execution, and the strategic deployment of visualization libraries to match the specific needs of engineering validation versus fabrication documentation.

---

## **2\. Introduction: The Shift to Headless Geometry in AEC**

The software architecture supporting the Architecture, Engineering, and Construction (AEC) sectors is undergoing a profound structural transformation, driven by the necessity to decouple geometric logic from interface-heavy desktop environments. Historically, applications for reinforcement detailing (rebar) were tightly coupled plugins running atop monolithic platforms like Autodesk Revit, Allplan, or AutoCAD. These platforms provided what is known in the industry as the "Heavy CAD Kernel"—a massive, compiled library of geometric functions responsible for Boolean operations, solid modeling, complex intersections, and topology management. These kernels, often proprietary technologies like Siemens' Parasolid or Dassault's ACIS, are robust but cumbersome, licensed at significant cost, and fundamentally designed for workstation computing rather than the agile, distributed nature of the modern web.

The contemporary requirement for **web-native**, **collaborative**, and **lightweight** applications challenges this traditional model. As engineers and detailers move toward browser-based tools that facilitate real-time collaboration and data extraction from cloud repositories, the overhead of running a 500MB geometric engine just to define a bent steel bar becomes difficult to justify. The "headless" geometry revolution seeks to strip away the user interface and the heavy legacy code, leaving only the pure mathematical logic required to define shape and form.

The user's query posits a radical, yet increasingly viable, alternative: utilizing the standard scientific Python stack—**NumPy** and **Matplotlib**—to replicate the necessary functions of a CAD kernel for the specific domain of rebar detailing. This proposition suggests moving away from the "black box" geometry engines of the past toward an "explicit" geometry stack where every vertex, vector, and curve is defined and managed by open-source code. This report rigorously evaluates this proposition, analyzing the mathematical feasibility, computational performance, and architectural implications of such a shift.

### **2.1 The Scope of "Rebar Geometry"**

To determine the feasibility of a lightweight stack, one must first rigorously define the geometric complexity of rebar. Unlike an engine block with complex compound surfaces, or an architectural facade with arbitrary freeform curvature, reinforcement bars are geometrically primitive and highly constrained objects. They are fundamentally one-dimensional curves swept with a circular profile to create a volume. Their shape is not arbitrary; it is constraint-driven, defined by parameters such as concrete cover thickness, mandrel diameters (bending radii), and leg lengths. Furthermore, they are standardized; shapes must strictly adhere to engineering codes such as ACI 318, BS 8666, or Eurocode 2, which prescribe specific bend geometries and hook lengths.

This reduced geometric scope suggests that a general-purpose CAD kernel is indeed overkill. The vast majority of a heavy kernel's features—such as advanced surfacing, lofting with guide curves, or complex boolean subtraction—are irrelevant to rebar detailing. A domain-specific "micro-kernel" built on efficient array computing (NumPy) is a viable replacement because the problem space is bounded. The geometry of a rebar cage is essentially a collection of polylines with filleted corners, a problem set that sits comfortably within the domain of linear algebra and basic computational geometry.

### **2.2 The Proposed "Lightweight" Stack**

The user proposes a specific technological stack to replace the traditional kernel. This stack consists of three primary components, each playing a distinct role in the "headless" architecture:

* **NumPy:** This library serves as the foundational engine for linear algebra, vector storage, and coordinate transformations. It replaces the vector math libraries found in C++ kernels, providing high-performance array operations that are essential for handling the thousands of bars found in a typical structural element.1  
* **Matplotlib:** Proposed for visualization and interaction, this library is traditionally used for 2D plotting in data science. Its role in an engineering context requires careful scrutiny, particularly regarding its ability to handle 3D spatial manipulation versus static reporting.3  
* **NURBS-Python (geomdl):** Implicitly suggested by the mention of NURBS and explicitly referenced in the research material, this library provides the curve mathematics often missing in raw NumPy. It acts as the sophisticated geometric layer, handling the precise definition of curves, knots, and control points that are necessary for standard-compliant data exchange.4

This report will analyze how these components interact to generate valid rebar shapes, focusing on the critical mathematical challenge of **fillet generation** (the bends) and the architectural challenge of **interactive validation** in a constrained web context. We will explore how this stack can function not just as a script, but as a robust, scalable application backend.

---

## **3\. Mathematical Foundations of Rebar Geometry in Python**

The first and most significant hurdle in replacing a commercial CAD kernel is replicating its mathematical engine. A heavy kernel provides "black box" functions to the developer—commands like fillet(line1, line2, radius) or offset(curve, distance). In a NumPy-based architecture, these convenience functions do not exist. The developer must implement this logic explicitly using vector algebra. This section details the mathematical operations required to achieve parity with a standard CAD kernel using Python's scientific stack.

### **3.1 Vector Algebra as the Logic Engine**

**NumPy** is the de facto standard for numerical computing in Python, and for good reason. It excels at array-based operations, which translates perfectly to processing geometric points. In the context of rebar detailing, a polyline is simply a sequence of coordinates, which can be efficiently represented as a NumPy array of shape (N, 3), where N is the number of vertices.

#### **3.1.1 Coordinate Systems and Transformations**

Rebar is typically defined in a **local coordinate system** (usually a Planar 2D shape definition) and then transformed into a **global coordinate system** (its 3D placement within a concrete host element like a beam or column).6 This distinction is crucial for parametric modeling.

* **Local Definition:** A stirrup is defined on the XY plane, centered at the origin or relative to a local insertion point.  
* **Global Placement:** The shape is then transformed via a $4 \\times 4$ transformation matrix to align with the beam's rotation, inclination, and position in 3D space.

In a NumPy-centric workflow, this transformation is trivial and highly performant. The operation is a standard matrix multiplication:  
$$ \\text{Global\_Points} \= \\text{Local\_Points} \\times \\text{Rotation\_Matrix} \+ \\text{Translation\_Vector} $$  
Code implementation in NumPy would look like:

Python

global\_pts \= np.dot(local\_pts, rotation\_matrix) \+ origin\_vector

This operation is vectorized, meaning NumPy computes thousands of vertex positions in microseconds. This is orders of magnitude faster than iterating through object-oriented point classes in a typical BIM API wrapper (like the Revit API), where each point transformation incurs the overhead of a function call. This speed is not just a convenience; it is a critical enabler for "interactive validation," where a user might drag a handle on a web interface and expect the entire rebar cage to update immediately without lag.

#### **3.1.2 Polyline Data Structures**

The efficiency of NumPy extends to how the geometry is stored. A heavy kernel uses complex B-Rep (Boundary Representation) data structures where topology (faces, edges, vertices) is explicitly linked. For rebar, this connectivity overhead is unnecessary. An implicit representation—Centerline Polyline \+ Radius \+ Diameter—is sufficient for the logic layer.

$$P \= \\begin{bmatrix} x\_1 & y\_1 & z\_1 \\\\ x\_2 & y\_2 & z\_2 \\\\ \\vdots & \\vdots & \\vdots \\\\ x\_n & y\_n & z\_n \\end{bmatrix}$$  
This representation allows for efficient batch operations. For example, calculating the total length of steel required for a bill of materials (BOM) involves summing the Euclidean distances between consecutive points. In NumPy, this is a single line of code: numpy.sum(numpy.linalg.norm(numpy.diff(P, axis=0), axis=1)).2 This calculation runs at C-speed, bypassing the Python interpreter loop for the heavy lifting, which is essential when processing thousands of bars in a large structural model.

### **3.2 The Mathematics of the Fillet**

The core complexity in rebar geometry is the **fillet**: the operation of replacing the sharp vertex between two linear segments with a tangential arc of a specific radius ($r$). In rebar detailing, this radius is not arbitrary; it is mandated by the "Mandrel Diameter" specified in design codes.

To implement this in NumPy without a CAD kernel, we apply 3D Euclidean geometry principles. The algorithm must handle the inputs of three points defining a corner ($P\_{prev}$, $P\_{curr}$, $P\_{next}$) and a scalar radius ($r$).7

1. **Vector Definition:** We first define the vectors describing the two legs of the bend. The incoming vector is $\\vec{u} \= P\_{curr} \- P\_{prev}$, and the outgoing vector is $\\vec{v} \= P\_{next} \- P\_{curr}$.  
2. **Normalization:** These vectors must be normalized to unit length to simplify angle calculations. $\\hat{u} \= \\vec{u} / \\|\\vec{u}\\|$ and $\\hat{v} \= \\vec{v} / \\|\\vec{v}\\|$.  
3. **Angle Calculation:** The angle between the segments is derived from the dot product. The half-angle of the corner ($\\theta/2$) is $\\alpha \= \\arccos(\\hat{u} \\cdot \\hat{v}) / 2$.  
4. **Bisector Vector:** The center of the fillet circle lies on the angle bisector. The bisector vector $\\vec{b}$ is the vector sum of the *reversed* incoming unit vector and the outgoing unit vector (assuming the layout points away from the vertex): $\\vec{b} \= (\\hat{v} \- \\hat{u})$.  
5. **Geometric Properties:** Using basic trigonometry, we calculate the key distances:  
   * **Tangent Distance ($T$):** The distance from the sharp corner vertex to the start/end of the arc along the legs. $T \= r / \\tan(\\alpha)$.  
   * **Center Distance ($D$):** The distance from the sharp corner vertex to the center of the fillet circle. $D \= r / \\sin(\\alpha)$.  
6. **Control Points Calculation:** With these scalars, we can locate the critical points in 3D space:  
   * $P\_{start} \= P\_{curr} \- T \\cdot \\hat{u}$  
   * $P\_{end} \= P\_{curr} \+ T \\cdot \\hat{v}$  
   * $Center \= P\_{curr} \+ D \\cdot (\\vec{b} / \\|\\vec{b}\\|)$

**Insight:** This calculation sequence requires no geometry library—only standard NumPy functions (norm, dot, cross, arccos). This explicitly confirms the feasibility of a "kernel-less" solver. The result is mathematically exact and indistinguishable from a CAD kernel's output. By implementing this logic directly, the developer gains full control over edge cases, such as when the tangent distance $T$ exceeds the length of the leg segment—a common validation error in rebar detailing that heavy kernels often obscure with generic error codes.

### **3.3 Handling 3D Skew Lines and Validation**

While most rebar bends are planar (lying flat on the XY plane), complex rebar shapes like "cranked" bars or transitions between columns of different sizes may involve non-coplanar lines. A heavy kernel solves 3D fillets automatically using generalized algorithms. In a NumPy-based approach, the developer must implement validation to check for coplanarity.

This is done using the scalar triple product. If the scalar triple product of the three vectors defining the corner is zero (or within a machine epsilon tolerance), the lines are coplanar, and a simple circular fillet is possible. If they are skew, a planar fillet is geometrically impossible, and the system must flag this as an invalid rebar shape.9 This "error handling" logic, which is built-in to kernels like Parasolid, must be explicitly coded in the Python layer. However, this explicit control allows for better user feedback; instead of a generic "Operation Failed," the app can report "Legs 2 and 3 are not coplanar; a planar bend cannot be formed," guiding the user toward a correct input.

---

## **4\. The geomdl Ecosystem: A Pythonic CAD Kernel**

While NumPy handles the raw linear algebra, representing the curved geometry in a standardized, exchangeable format requires a higher-level abstraction. A rebar is not just a collection of points; it is a curve with mathematical continuity. **NURBS-Python (geomdl)** is the ideal candidate to fill this role, effectively acting as a lightweight, domain-specific kernel.4

### **4.1 What is geomdl?**

geomdl is a pure Python library (with optional C-extensions via geomdl.core for performance) designed to create, store, and evaluate NURBS (Non-Uniform Rational B-Splines) curves and surfaces.10 Unlike NumPy, which deals in discrete points, geomdl deals in **equations**.

* **Dependency-Free:** A critical advantage for the user's web application goal is that geomdl does not require OpenCASCADE or other heavy binary dependencies. This makes it highly portable to web environments via Pyodide, allowing it to run directly in the browser.10  
* **Standards Compliant:** It adheres to typical NURBS definitions (Knot vectors, Weights, Degrees, Control Points), making it compatible with data exchange formats like OBJ, STL, or JSON export to Three.js.11 This ensures that the geometry generated in the Python layer can be accurately consumed by other tools in the BIM ecosystem.

### **4.2 Generating Rebar Shapes with geomdl**

A rebar shape is essentially a **Multi-Curve**: a sequence of straight lines connected by arcs. In NURBS terms, this is represented as a piecewise curve with $C^0$ continuity at the sharp corners (if modeling the schematic representation) or $G^1$ continuity at the tangents (if modeling the physical filleted bar).

#### **4.2.1 The Explicit NURBS Approach**

Instead of discretizing the arc into 100 small straight line segments (which creates heavy data payloads), geomdl allows defining the arc exactly using a **Rational B-Spline**. The "Rational" part of NURBS is crucial here, as it allows for the exact representation of conic sections, including circles, which is impossible with standard polynomial B-splines (like those used in simple SVG paths).

To create a perfect 90-degree fillet arc in geomdl 12:

* **Degree:** The curve must be Degree 2 (Quadratic).  
* **Control Points:** We use 3 control points: $P\_{start}$, $P\_{corner}$, and $P\_{end}$. These are derived from the NumPy logic described in Section 3.2.  
* **Weights:** This is the key. To get a circular arc, the weight of the middle control point ($P\_{corner}$) must be set to $\\sin(45^\\circ) \\approx 0.7071$. The start and end points have a weight of $1.0$.  
* **Knot Vector:** A standard clamped knot vector \`\` ensures the curve passes through the start and end control points.

This generates a mathematically perfect circular arc.13 This approach is superior to the "polygonal approximation" methods often used in game engines, because it maintains the precision required for engineering fabrication data. CNC bending machines need the exact radius and arc length, not a faceted approximation. geomdl provides this engineering-grade fidelity.

#### **4.2.2 The shapes Module**

geomdl includes a shapes module containing shortcuts for generating common analytic geometries.14 While the built-in library focuses on generic shapes like Circle or Star, the architecture is extensible. For a rebar web app, the developer would essentially extend this module to create a geomdl.shapes.rebar library.

This custom library would implement classes such as Stirrup, Hook, and Crank. These classes would encapsulate the parametric logic:

Python

class Stirrup(geomdl.BSpline.Curve):  
    def \_\_init\_\_(self, width, height, cover, diameter):  
        \# 1\. Calculate centerline dimensions (width \- 2\*cover \- diameter)  
        \# 2\. Use NumPy to find the 4 corner points and 8 tangent points  
        \# 3\. Construct the Knot Vector for a multi-span NURBS  
        \# 4\. Set Control Points and Weights  
        \# 5\. Call super().\_\_init\_\_ to finalize the curve

This approach encapsulates the "Kernel" logic within a lightweight Python class structure, making the code modular and maintainable.

### **4.3 Exporting for the Web**

A critical feature of geomdl is its ability to export data in various formats. It natively supports saving surfaces and curves as OBJ, STL, or JSON.10

* **JSON Export:** This is the most valuable feature for a web application architecture. geomdl can serialize the NURBS data (control points, weights, knots, degree) into a lightweight JSON object.  
* **Client-Side Reconstruction:** This JSON can be sent to the frontend (Three.js), which can then reconstruct the exact curve using its own NURBSCurve geometry loader. This workflow is extremely bandwidth-efficient, transmitting only a few kilobytes of mathematical definition rather than megabytes of tessellated mesh data.11

### **4.4 Volumetric Generation (Sweeps)**

While the curve defines the path of the rebar, the visual representation requires volume—a pipe. geomdl includes functionality for sweeping surfaces along a rail curve in its construct module.17 However, generating a full high-resolution mesh for every bar in Python (server-side or in WASM) can be CPU-intensive and memory-heavy.

* **NURBS Surfaces:** geomdl can mathematically generate a NURBS surface representing the pipe.  
* **Tessellation Strategy:** For web visualization, it is often more efficient to send the *curve data* to the browser and let the GPU-accelerated JavaScript library (Three.js) handle the volumetric meshing (using TubeGeometry). This avoids the bottleneck of generating and serializing millions of triangles in Python.

---

## **5\. Visualization: Matplotlib vs. Three.js**

The user query explicitly asks about using **Matplotlib** to "visualize" these rebar elements for the web app. This section critically analyzes the capabilities of Matplotlib in an engineering context and contrasts it with web-native alternatives.

### **5.1 Matplotlib for Engineering Graphics**

Matplotlib is the workhorse of scientific Python plotting. Its capabilities for **2D technical drawing** are robust and well-suited for specific aspects of the rebar detailing workflow.3

#### **5.1.1 Strengths: Static Reporting and Documentation**

For generating the **Bar Bending Schedule (BBS)**—the legal document sent to the factory for fabrication—Matplotlib is excellent.

* **Dimensioning:** Using the ax.annotate system with arrowprops, developers can create precise dimension lines (e.g., "\<--- 500mm \---\>").18 While Matplotlib does not have an automatic "Dimension Tool" like AutoCAD, a wrapper function draw\_dimension(point\_a, point\_b) can be easily written to place text and arrows at the correct coordinates.  
* **SVG Output:** Matplotlib natively exports to Scalable Vector Graphics (SVG).20 This is a massive advantage for a web app. The Python backend can generate a vector-perfect, print-ready image of the rebar shape. This SVG can be embedded directly into the HTML DOM of the web report, ensuring high-quality printing and scaling without pixelation.  
* **Validation Plots:** Engineers often need to verify properties like curvature to ensure no "kinking" occurs. Matplotlib can plot the curvature graph ($\\kappa$) of the NURBS curve alongside the shape, a technical validation feature that standard 3D viewers often lack.4

#### **5.1.2 Weaknesses: Interactive 3D Modeling**

For the **interactive web app component**—where a user wants to rotate the rebar cage, inspect connections, or drag handles—Matplotlib is fundamentally ill-suited.

* **The Backend Problem:** Matplotlib is not a real-time rendering engine; it is a static plotting library. It draws "Artists" to a canvas. In a browser context (via Pyodide), it typically uses a specific backend (module://matplotlib\_pyodide.html5\_canvas\_backend) to draw to an HTML5 Canvas.23  
* **Performance Limits:** Rotating a 3D plot in Matplotlib involves re-projecting every point in Python and re-drawing the entire canvas. This process is CPU-bound and sluggish compared to WebGL, which is GPU-bound. Benchmarks show that rotating a plot with thousands of segments in Matplotlib is significantly slower than in Three.js.24  
* **Z-Order Artifacts:** Matplotlib's mplot3d toolkit is widely known to have issues with depth sorting. It draws elements in a sorted order based on their centroid, which often leads to visual artifacts where a rebar that should be "behind" a column visually appears "in front" of it.25 This destroys the spatial intuition required for checking complex reinforcement cages.  
* **Interaction Limits:** Implementing "CAD-style" interactions—such as hover-to-highlight, click-to-select edge, or snap-to-vertex—requires extensive custom event handling in Matplotlib. While possible, it is brittle and difficult to maintain in a web environment compared to the native event systems of DOM-based or WebGL libraries.27

### **5.2 The Alternative: Headless Python \+ Three.js Frontend**

The industry standard solution—and the strong recommendation of this report—is a **Hybrid Compute** architecture.

1. **Python (NumPy/Geomdl):** Acts as the "Geometry Server" (or logic layer). It calculates the mathematics of the shape.  
2. **Three.js:** Acts as the "View Layer." It receives the geometry data and renders it using WebGL.28

**Advantages of Three.js:**

* **Performance:** Three.js handles geometry on the GPU, allowing it to render thousands of bars at 60 frames per second (FPS).  
* **Visual Fidelity:** It supports PBR (Physically Based Rendering) materials, allowing rebar to look like metallic steel, along with proper shadows and depth buffering.  
* **Interactivity:** It has native support for raycasting (mouse selection), rotation, zooming, and snapping, providing the "CAD feel" users expect.

Implementation Workflow:  
The Python script generates the curve using geomdl. It then exports a JSON object containing the mathematical definition:

JSON

{  
  "type": "NURBS",  
  "degree": 2,  
  "knots": ,  
  "controlPoints": \[, \[10,10,0,0.707\], \]  
}

The Three.js frontend parses this JSON and uses it to draw the curve. This architecture keeps the *logic* in Python (satisfying the user's desire to use NumPy for generation) but offloads the *pixels* to the browser's GPU, playing to the strengths of each technology.30

---

## **6\. Web Feasibility: Pyodide and WASM**

The user's query specifies a "web app." Traditionally, Python logic runs on a backend server (Django/Flask). However, modern web architecture allows for a **Serverless Client-Side** approach using **Pyodide**.

### **6.1 Architecture of a Client-Side CAD App**

Pyodide is a distribution of Python compiled to WebAssembly (WASM). It allows the Python runtime—including the C-extensions of NumPy and Matplotlib—to run entirely inside the user's browser.32

* **Feasibility:** It is completely feasible to bundle the custom "Rebar Geometry" Python library (built on numpy and geomdl) as a pure Python Wheel (.whl) and load it into the browser using micropip.34  
* **Deployment Model:**  
  1. The user navigates to rebar-app.com.  
  2. The browser downloads the Pyodide runtime, numpy.js, and the custom rebar\_logic.whl.  
  3. All geometric calculations happen locally on the user's machine.  
* **Workflow:** When the user inputs parameters (e.g., "Stirrup, 300x500, dia=12"), the browser executes the Python code via WASM. NumPy calculates the vectors, geomdl computes the NURBS control points, and the script returns the JSON data to the JavaScript layer for Three.js to render.

### **6.2 Performance Considerations**

* **Execution Speed:** NumPy operations in WASM run at near-native speeds (typically 1x-2x slower than native C++, but orders of magnitude faster than pure Python). For rebar geometry, which involves thousands of operations rather than billions (like fluid dynamics), this is more than fast enough for real-time performance.36  
* **Startup Time:** The initial load of Pyodide is heavy (\~10MB). The application will require a loading screen. However, once loaded, the app works instantly and even offline.  
* **Threading:** By default, WASM runs on the browser's main thread, which can freeze the UI during heavy calculations. For complex rebar cages, the Python execution should be moved to a **Web Worker** to keep the interface responsive.32

---

## **7\. Comparative Analysis: Lightweight vs. Heavy Kernel**

To contextualize the decision, we present a comparative analysis between the proposed lightweight stack and the traditional heavy kernel approach.

| Feature | Heavy Kernel (e.g., Parasolid/Revit API) | Lightweight Stack (NumPy/Geomdl/Three.js) |
| :---- | :---- | :---- |
| **Geometry Source** | Proprietary "Black Box" Engine | Explicit Vector Algebra (Open Source) |
| **Fillet Handling** | Automatic, robust Fillet() commands | Manual implementation of vector math logic |
| **Licensing** | Expensive per-seat or server core costs | Free (MIT/BSD Open Source) |
| **Deployment** | Server-side only (typically Windows-bound) | Client-side (WASM) or Serverless Linux |
| **File Size** | Heavy DLLs (\>100MBs) | Lightweight Python Wheels (\~10MBs) |
| **Visualization** | Built-in but often restrictive | Fully custom via Three.js / WebGL |
| **Validation** | Advanced topology & solid operations | Basic distance checks & rule-based logic |
| **Learning Curve** | High (Complex, proprietary APIs) | High (Requires math/geometry knowledge) |

**Key Insight:** The trade-off is between **Licensing Cost** and **Development Effort**. The heavy kernel provides convenient functions but costs money and restricts deployment. The lightweight stack is free and portable but requires the developer to write the low-level geometric logic (fillets, offsets) themselves.

---

## **8\. Algorithms for Specific Rebar Shapes**

To validate the feasibility, we must demonstrate how specific, common rebar shapes would be generated using the lightweight stack.

### **8.1 The Stirrup Algorithm (Python Implementation)**

The stirrup is the most ubiquitous rebar shape. The algorithmic flow in the proposed stack is as follows:

1. **Inputs:** Beam\_Width, Beam\_Height, Cover, Diameter.  
2. **Mandrel Lookup:** Retrieve the bending radius based on the diameter (e.g., for $d=12mm$, Mandrel=$4d=48mm$).37  
3. **Centreline Calculation:** Define the rectangular path. $W\_c \= \\text{Beam\\\_Width} \- 2 \\times \\text{Cover} \- \\text{Diameter}$.  
4. **Corner Generation:** Iterate through the 4 corners of the rectangle. At each corner, apply the compute\_fillet\_parameters() logic (Section 3.2) using NumPy to find the start and end tangent points.  
5. **Hook Addition:** The start and end of the loop are not merely joined; they must overlap and bend inwards to form seismic hooks (typically $135^\\circ$). This requires defining two additional path segments.  
   * Extend the vector from the last tangent point.  
   * Rotate this vector by $135^\\circ$ using a standard 2D rotation matrix in NumPy.  
6. **Assembly:** Combine all control points (Legs \+ Arcs \+ Hooks) into a single geomdl.BSpline.Curve object.  
7. **Output:** A single NURBS curve representing the detailed stirrup, ready for export.

### **8.2 3D Visualization of the Bar (The "Pipe" Problem)**

A NURBS curve is mathematically a 1D line—it is infinitely thin. Real rebar has thickness.

* **Matplotlib:** To show thickness, one would have to use mplot3d.art3d.Poly3DCollection to draw a tube. This essentially means generating a mesh of triangles in Python. This is computationally very expensive and renders poorly in Matplotlib.26  
* **Three.js:** The library has a native TubeGeometry which takes a path (curve) and a radius. It generates the 3D mesh (vertices/faces) directly on the GPU. This confirms the hybrid approach is superior: Python defines the *path* (low data), while WebGL generates the *volume* (high visual impact).

---

## **9\. Validation and Interaction Strategies**

The user query emphasizes "interactive validation." This implies checking the geometry against rules and allowing user manipulation.

### **9.1 Geometric Validation Logic**

In a heavy kernel, the system might throw an error if a fillet is too large. In the lightweight stack, validation is a set of explicit Python checks:

* **Minimum Bend Radius:** The script checks the calculated radius against the design code table (ACI/Eurocode). If calc\_radius \< min\_radius, the function raises a ValueError with a descriptive message.  
* **Interference (Clash Detection):** NumPy can efficiently calculate the distances between the stirrup legs and longitudinal bars. scipy.spatial.distance.cdist can compute the distance matrix between all bar centers to detect clashes.38 If the distance is less than the sum of the radii ($D \< r\_1 \+ r\_2$), a clash is detected.

### **9.2 Interactive Parametric Editing**

In a CAD kernel, "dragging" a rebar leg invokes a complex constraint solver. In the lightweight stack, we simulate this via a reactive loop:

1. **Event:** The user drags a handle on the Three.js web canvas.  
2. **Update:** JavaScript sends the new width parameter to the Pyodide/Python environment.  
3. **Recalculate:** Python re-runs the Stirrup() function. Because NumPy is fast, this takes milliseconds.  
4. **Redraw:** Python sends the new knot vectors and control points to JavaScript. Three.js updates the geometry buffer.

This "parametric regeneration" loop is standard in modern web configurators and is entirely feasible with this stack, providing a user experience that rivals native desktop CAD applications.

---

## **10\. Limitations and Strategic Risks**

While the lightweight approach is feasible and attractive, it carries specific risks that must be acknowledged.

1. **The "Re-inventing the Wheel" Risk:** By rejecting a CAD kernel, the developer accepts the burden of maintaining low-level geometric algorithms. Edge cases that standard kernels solved decades ago—such as self-intersecting offsets or fillets where the radius exceeds the segment length—must be handled manually in the Python code.39  
2. **Topology Operations:** NumPy is not a B-Rep modeler. If the app needs to perform Boolean operations (e.g., "Subtract this cylinder from this block" to create a void), NumPy/Geomdl cannot do this easily. This stack is strictly for *constructive* geometry (generating shapes from parameters), not *destructive* editing of solids.  
3. **Matplotlib's Web Limitations:** As noted, relying on Matplotlib for the primary web interface is a UX dead-end. It should be strictly relegated to reporting functionality only.

---

## **11\. Conclusion and Recommendations**

This exhaustive analysis confirms that **it is entirely feasible to use NumPy and geomdl to replace heavy CAD kernels for the specific domain of rebar detailing.** The mathematical complexity of rebar geometry—primarily sweeps along filleted polylines—is well within the capabilities of these scientific computing libraries. The "Kernel" is no longer a single black-box library but a composed stack of **NumPy** (algebra), **geomdl** (curves), and **custom logic** (constraints).

However, for the **visualization** aspect, **Matplotlib** is insufficient for the interactive 3D component and should be paired with **Three.js**. Matplotlib remains invaluable for generating high-quality, vector-based **2D Bar Bending Schedules**.

### **Strategic Recommendations for Implementation:**

1. **Adopt geomdl for the Data Model:** Use it to store and evaluate the curves. It provides the rigorous definition required for manufacturing (CAM) output.  
2. **Use NumPy for the "Solver":** Implement a custom RebarSolver class that takes parameters (cover, diameter, spacing) and outputs the geomdl control points. Use NumPy for all vector math (offsets, fillets).  
3. **Discard Matplotlib for Viewport:** Use **Three.js** for the interactive 3D window. Pass the curve data from Python to JS via JSON.  
4. **Retain Matplotlib for Documentation:** Use it to generate the automated PDF/SVG "bending schedules" that engineers need for fabrication.  
5. **Leverage Pyodide:** Execute the Python solver in the client browser (WASM) to eliminate server costs, reduce latency, and enable offline capability.

By following this architecture, the user can build a "headless" CAD application that is lightweight, performant, and cost-effective, effectively disrupting the traditional dependency on heavy, expensive geometric kernels.

#### **Works cited**

1. NumPy in ArcGIS—ArcGIS Pro | Documentation, accessed November 20, 2025, [https://pro.arcgis.com/en/pro-app/3.4/arcpy/get-started/working-with-numpy-in-arcgis.htm](https://pro.arcgis.com/en/pro-app/3.4/arcpy/get-started/working-with-numpy-in-arcgis.htm)  
2. NumPy, accessed November 20, 2025, [https://numpy.org/](https://numpy.org/)  
3. Matplotlib — Visualization with Python, accessed November 20, 2025, [https://matplotlib.org/](https://matplotlib.org/)  
4. geomdl \- PyPI, accessed November 20, 2025, [https://pypi.org/project/geomdl/](https://pypi.org/project/geomdl/)  
5. NURBS-Python v5.x Documentation — NURBS-Python 5.4.1.dev10+g9d2555a documentation, accessed November 20, 2025, [https://nurbs-python.readthedocs.io/](https://nurbs-python.readthedocs.io/)  
6. Reinforcement \- Python API Documentation, accessed November 20, 2025, [https://pythonparts.allplan.com/latest/manual/features/reinforcement/](https://pythonparts.allplan.com/latest/manual/features/reinforcement/)  
7. Find max radius of an arc between two lines in 3D \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/75428828/find-max-radius-of-an-arc-between-two-lines-in-3d](https://stackoverflow.com/questions/75428828/find-max-radius-of-an-arc-between-two-lines-in-3d)  
8. simple fillet example with numpy \- GitHub Gist, accessed November 20, 2025, [https://gist.github.com/alanbernstein/fa436f2654d4408f2bda5c5d9089e845](https://gist.github.com/alanbernstein/fa436f2654d4408f2bda5c5d9089e845)  
9. Fillet Calculus3D \- Python API Documentation, accessed November 20, 2025, [https://pythonparts.allplan.com/2024/api\_reference/InterfaceStubs/NemAll\_Python\_Geometry/FilletCalculus3D/](https://pythonparts.allplan.com/2024/api_reference/InterfaceStubs/NemAll_Python_Geometry/FilletCalculus3D/)  
10. NURBS-Python, accessed November 20, 2025, [https://web.me.iastate.edu/idealab/c-nurbs-python.html](https://web.me.iastate.edu/idealab/c-nurbs-python.html)  
11. Export ThreeJS Geometry to JSON \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/30959385/export-threejs-geometry-to-json](https://stackoverflow.com/questions/30959385/export-threejs-geometry-to-json)  
12. Basics — NURBS-Python 5.4.1.dev10+g9d2555a documentation \- Read the Docs, accessed November 20, 2025, [https://nurbs-python.readthedocs.io/en/5.x/basics.html](https://nurbs-python.readthedocs.io/en/5.x/basics.html)  
13. How can I use Python to select one (spline control) point of a NURBS curve?, accessed November 20, 2025, [https://blender.stackexchange.com/questions/221132/how-can-i-use-python-to-select-one-spline-control-point-of-a-nurbs-curve](https://blender.stackexchange.com/questions/221132/how-can-i-use-python-to-select-one-spline-control-point-of-a-nurbs-curve)  
14. orbingol/geomdl-shapes: Generate common B-spline, NURBS and analytic geometries, accessed November 20, 2025, [https://github.com/orbingol/geomdl-shapes](https://github.com/orbingol/geomdl-shapes)  
15. geomdl.shapes \- PyPI, accessed November 20, 2025, [https://pypi.org/project/geomdl.shapes/](https://pypi.org/project/geomdl.shapes/)  
16. geomdl \- PyPI, accessed November 20, 2025, [https://pypi.org/project/geomdl/3.7.0/](https://pypi.org/project/geomdl/3.7.0/)  
17. Geometry Constructors and Extractors \- NURBS-Python \- Read the Docs, accessed November 20, 2025, [https://nurbs-python.readthedocs.io/en/5.x/module\_construct.html](https://nurbs-python.readthedocs.io/en/5.x/module_construct.html)  
18. Annotating dimensions in matplotlib \- python \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/14892619/annotating-dimensions-in-matplotlib](https://stackoverflow.com/questions/14892619/annotating-dimensions-in-matplotlib)  
19. Plotting distance arrows in technical drawing \- python \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/14612637/plotting-distance-arrows-in-technical-drawing](https://stackoverflow.com/questions/14612637/plotting-distance-arrows-in-technical-drawing)  
20. Exporting an svg file from a Matplotlib figure \- Tutorials Point, accessed November 20, 2025, [https://www.tutorialspoint.com/exporting-an-svg-file-from-a-matplotlib-figure](https://www.tutorialspoint.com/exporting-an-svg-file-from-a-matplotlib-figure)  
21. How can I get the output of a matplotlib plot as an SVG? \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/24525111/how-can-i-get-the-output-of-a-matplotlib-plot-as-an-svg](https://stackoverflow.com/questions/24525111/how-can-i-get-the-output-of-a-matplotlib-plot-as-an-svg)  
22. Best visualization library for clean SVG exports? \- Python \- Reddit, accessed November 20, 2025, [https://www.reddit.com/r/Python/comments/1gh5y83/best\_visualization\_library\_for\_clean\_svg\_exports/](https://www.reddit.com/r/Python/comments/1gh5y83/best_visualization_library_for_clean_svg_exports/)  
23. I made an online editor that runs matplotlib in your browser : r/Python \- Reddit, accessed November 20, 2025, [https://www.reddit.com/r/Python/comments/1aju5b7/i\_made\_an\_online\_editor\_that\_runs\_matplotlib\_in/](https://www.reddit.com/r/Python/comments/1aju5b7/i_made_an_online_editor_that_runs_matplotlib_in/)  
24. Three-Dimensional Plotting in Matplotlib | Python Data Science Handbook, accessed November 20, 2025, [https://jakevdp.github.io/PythonDataScienceHandbook/04.12-three-dimensional-plotting.html](https://jakevdp.github.io/PythonDataScienceHandbook/04.12-three-dimensional-plotting.html)  
25. Create a CAD model from python surface plot \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/42004787/create-a-cad-model-from-python-surface-plot](https://stackoverflow.com/questions/42004787/create-a-cad-model-from-python-surface-plot)  
26. Matplotlib: save 3D volume plot to numpy array \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/51275627/matplotlib-save-3d-volume-plot-to-numpy-array](https://stackoverflow.com/questions/51275627/matplotlib-save-3d-volume-plot-to-numpy-array)  
27. Interactive figures — Matplotlib 3.10.7 documentation, accessed November 20, 2025, [https://matplotlib.org/stable/users/explain/figure/interactive.html](https://matplotlib.org/stable/users/explain/figure/interactive.html)  
28. Three Dimensional Visualization — Learn Multibody Dynamics, accessed November 20, 2025, [https://moorepants.github.io/learn-multibody-dynamics/visualization.html](https://moorepants.github.io/learn-multibody-dynamics/visualization.html)  
29. How to use three.js with python syntax \- Showcase, accessed November 20, 2025, [https://discourse.threejs.org/t/how-to-use-three-js-with-python-syntax/43113](https://discourse.threejs.org/t/how-to-use-three-js-with-python-syntax/43113)  
30. How to export and import 3d models into threejs of .js file? \- Questions, accessed November 20, 2025, [https://discourse.threejs.org/t/how-to-export-and-import-3d-models-into-threejs-of-js-file/40952](https://discourse.threejs.org/t/how-to-export-and-import-3d-models-into-threejs-of-js-file/40952)  
31. Curve – three.js docs, accessed November 20, 2025, [https://threejs.org/docs/pages/Curve.html](https://threejs.org/docs/pages/Curve.html)  
32. Using Pyodide — Version 0.29.0, accessed November 20, 2025, [https://pyodide.org/en/stable/usage/index.html](https://pyodide.org/en/stable/usage/index.html)  
33. Getting started — Version 0.29.0 \- Pyodide, accessed November 20, 2025, [https://pyodide.org/en/stable/usage/quickstart.html](https://pyodide.org/en/stable/usage/quickstart.html)  
34. Loading custom Python code — Version 0.30.0.dev0 \- Pyodide, accessed November 20, 2025, [https://pyodide.org/en/latest/usage/loading-custom-python-code.html](https://pyodide.org/en/latest/usage/loading-custom-python-code.html)  
35. Is it possible to build python wheel in browser using wasm for pyodide? \- Stack Overflow, accessed November 20, 2025, [https://stackoverflow.com/questions/65185874/is-it-possible-to-build-python-wheel-in-browser-using-wasm-for-pyodide](https://stackoverflow.com/questions/65185874/is-it-possible-to-build-python-wheel-in-browser-using-wasm-for-pyodide)  
36. Building and testing Python packages out of tree — Version 0.26.4 \- Pyodide, accessed November 20, 2025, [https://pyodide.org/en/0.24.4/development/building-and-testing-packages.html](https://pyodide.org/en/0.24.4/development/building-and-testing-packages.html)  
37. Reinforcement shape definition \- allplan python api, accessed November 20, 2025, [https://pythonparts.allplan.com/latest/manual/features/reinforcement/shape\_definition/](https://pythonparts.allplan.com/latest/manual/features/reinforcement/shape_definition/)  
38. Introducing scikit-geometry. The Python ecosystem is lacking a… | by Wolf Vollprecht, accessed November 20, 2025, [https://wolfv.medium.com/introducing-scikit-geometry-ae1dccaad5fd](https://wolfv.medium.com/introducing-scikit-geometry-ae1dccaad5fd)  
39. How to calculate maximum fillet radius between two lines? \- McNeel Forum, accessed November 20, 2025, [https://discourse.mcneel.com/t/how-to-calculate-maximum-fillet-radius-between-two-lines/105998](https://discourse.mcneel.com/t/how-to-calculate-maximum-fillet-radius-between-two-lines/105998)