
# **Comparative Analysis of Web-Based Geometry Engines for Rebar Detailing: That Open Company Fragments vs. Bitbybit-dev OpenCascade**

## **1\. Introduction: The Computational Landscape of Web-Based Rebar Detailing**

The Architecture, Engineering, and Construction (AEC) industry stands at a technological precipice, transitioning from desktop-bound, file-based workflows to cloud-native, granular data ecosystems. Within this digital transformation, the specific domain of reinforcement bar (rebar) detailing presents a unique and formidable set of computational challenges that distinguish it from general architectural visualization or structural analysis. Rebar detailing is not merely about placing lines in space; it involves the generation, management, and fabrication-ready definition of massive datasets—often numbering in the hundreds of thousands of elements per project—where each element is a swept solid defined by strict engineering standards regarding bend radii, elongation, and varying diameters.

The shift to web-based applications for this purpose requires a rigorous evaluation of the underlying geometry engines. The browser environment, while increasingly capable due to WebAssembly (Wasm) and WebGL, imposes strict limits on memory heap size (typically 2GB to 4GB) and single-threaded execution cycles. Therefore, the choice of geometry library is the single most critical architectural decision for a rebar detailing platform. This report provides an exhaustive, expert-level comparative analysis between two leading open-source ecosystems that approach this problem from fundamentally different philosophical and technical angles: **That Open Company** (formerly the team behind IFC.js), specifically their **"Fragments"** protocol and **"Clay"** engine, and **"bitbybit-dev"**, a platform that acts as a bridge to the **OpenCascade Technology (OCCT)** and **Manifold** geometry kernels.

The analysis explores the technical architecture, geometric capabilities, performance characteristics, and strategic viability of both solutions. It posits that while That Open Company provides an unparalleled framework for the *visualization, streaming, and management* of massive federated BIM datasets 1, bitbybit-dev offers the necessary *mathematical robustness and parametric generative capabilities* required to author fabrication-grade rebar geometry from scratch.3 The following sections detail the evidence supporting this conclusion, dissecting the nuances of mesh-based versus boundary-representation (B-Rep) workflows in the context of heavy civil engineering requirements.

### **1.1 The Specificity of the Rebar Problem**

To evaluate these libraries effectively, one must define the computational profile of a rebar model. Unlike a wall or a slab, which are often simplified as bounding box extrusions during early design, rebar is high-frequency, high-fidelity geometry.

* **Geometric Complexity:** A single rebar is a swept solid—a circular cross-section extruded along a complex 3D path. The "elbows" or bends in this path must be filleted according to specific code mandates (e.g., ACI 318 or Eurocode 2), which dictate the radius as a multiple of the bar diameter.  
* **Data Volume:** A high-rise building may contain over 200,000 individual bars.  
* **Parametric Dependency:** Rebar geometry is dependent. If a concrete column changes size, the stirrups must update their width, the vertical bars must shift, and the hook lengths may need adjustment. This requires a geometry engine capable of solving constraints and regenerating solids in real-time.

The central conflict in web-based detailing is the "Polygon Explosion." Representing a smooth, cylindrical bar with a mesh requires hundreds of triangles. Multiplying this by 200,000 bars results in hundreds of millions of polygons, far exceeding the rendering budget of a standard web browser. This report analyzes how the **Fragments** protocol handles this visualization challenge versus how **OCCT** handles the generation challenge.

## **2\. That Open Company: Architecture of the "AECOsystem"**

That Open Company has evolved beyond a simple library provider into a comprehensive platform provider for the AECO (Architecture, Engineering, Construction, and Operations) sector. Their ecosystem, branded as the "AECOsystem," is bifurcated into **That Open Platform** (technology) and **That Open People** (community).5 Their technology stack is explicitly designed to democratize BIM software development, moving away from monolithic desktop apps toward modular, web-based components.6

### **2.1 The Fragments Protocol: Solving the Visualization Bottleneck**

The crown jewel of That Open Company’s offering for rebar applications is the **Fragments** library. It is described as a high-performance geometry system built atop Three.js, specifically engineered to display BIM models efficiently while maintaining granular control over individual items.2

#### **2.1.1 The Mechanics of Instancing**

In a raw Three.js implementation, loading a rebar cage with 5,000 identical stirrups would typically involve creating 5,000 individual Mesh objects. Each object incurs CPU-to-GPU communication overhead (draw calls) and memory overhead for the geometry data.

**Fragments** utilizes **Instanced Mesh** technology to solve this.7

* **Deduplication:** The engine analyzes the incoming data (whether from an IFC file or generated via API) and identifies identical geometries. For a rebar cage, it recognizes that all 12mm stirrups are the same shape, merely rotated and translated.  
* **Matrix Storage:** It stores the geometry definition *once* in memory. It then creates a Fragment which contains that single geometry and a Float32Array of transformation matrices.  
* **Performance Implication:** This allows the GPU to render thousands of bars in a single draw call. The memory footprint is reduced drastically—often by orders of magnitude—transforming a multi-gigabyte geometry load into a manageable megabyte-scale stream.8

#### **2.1.2 Serialization via FlatBuffers**

A critical, often overlooked advantage of the Fragments protocol is its serialization method. That Open Company employs **FlatBuffers**, a cross-platform serialization library developed by Google.7

* **Zero-Copy Access:** Unlike JSON, which requires expensive parsing (CPU time) to convert text into JavaScript objects, FlatBuffers allows the application to access data directly from the binary buffer without unpacking it.  
* **Speed:** This results in near-instantaneous loading of geometric data. For a rebar app where users might switch between different reinforcement zones, the ability to stream frag files instantly is a massive UX advantage over parsing OBJ or glTF files.9  
* **Interoperability:** Because FlatBuffers is schema-driven and language-agnostic, a backend service written in C\#, Python, or C++ can generate .frag files that the web frontend consumes natively.8

### **2.2 The "Clay" Engine: Editing vs. Generation**

Recent announcements from That Open Company highlight **"Clay"**, a component described as a "lightweight BIM modelling engine" capable of creating and editing geometry.6

#### **2.2.1 Direct Modeling Paradigm**

The analysis of the available documentation suggests that Clay is architected around a **Direct Modeling** paradigm. It allows users to push, pull, and manipulate geometric primitives within the browser, similar to the interaction model of SketchUp.10

* **Mesh-Based Operations:** Clay appears to operate primarily on the mesh level within the Three.js scene graph. It provides tools for boolean operations (e.g., cutting a hole in a wall) and geometric adjustments.11  
* **Limitations for Rebar:** While powerful for architectural massing or minor edits, direct modeling is insufficient for *generative* rebar detailing. Rebar is defined by strict parametric rules (centerline path \+ radius \+ diameter). Clay does not appear to possess a constraint solver or a B-Rep kernel capable of maintaining the mathematical integrity of a swept pipe during complex parametric updates. It is a tool for *shaping*, not *engineering*.12

### **2.3 BIM Tiles and Streaming**

For massive datasets, That Open Company has introduced **BIM Tiles**.10 Similar to how Google Maps streams map tiles based on zoom level, BIM Tiles allows a rebar app to stream geometry.

* **Spatial Indexing:** The library spatially indexes the fragments. If the user is zoomed into a specific column-beam joint, the system only loads and renders the rebar fragments relevant to that volume.13  
* **Memory Safety:** This ensures that even if the total project contains 10 million bars, the browser memory is never overwhelmed, as off-screen data is dynamically disposed of.14

### **2.4 The Component Ecosystem (OBC)**

The **Open BIM Components (OBC)** library provides the scaffolding for a complete application.

* **High-Level Tools:** It includes pre-built components for raycasting (selection), clipping planes (sections), and dimensioning.14  
* **Memory Management:** The Disposer component is critical for long-running Single Page Applications (SPAs). In a rebar app where users constantly generate and regenerate options, failing to dispose of Three.js geometries causes memory leaks that crash the tab. OBC handles this cleanup automatically.14  
* **Community and Support:** The ecosystem is supported by "That Open People" and the "Pioneers" program, which funds development and provides advanced support to enterprise users, suggesting a sustainable commercial backing for the open-source tools.6

## **3\. Bitbybit-dev: The Power of Kernel Abstraction**

Bitbybit-dev represents a fundamentally different approach to the web geometry problem. Rather than building a bespoke engine on top of a rendering library (like TOC does with Three.js), bitbybit-dev acts as a sophisticated middleware or "wrapper" that exposes established, industrial-strength CAD kernels to the web environment.4

### **3.1 OpenCascade Technology (OCCT) Integration**

The primary engine leveraged by bitbybit-dev for heavy geometric lifting is **OpenCascade Technology (OCCT)**. OCCT is a C++ library that has been the backbone of open-source CAD (e.g., FreeCAD) for decades. Bitbybit-dev wraps the Wasm port of this kernel, making it accessible via TypeScript.16

#### **3.1.1 Boundary Representation (B-Rep)**

OCCT operates on **B-Rep** data structures, not meshes. This distinction is vital for rebar.

* **Mathematical Precision:** In a mesh, a circle is a polygon with $N$ sides. In B-Rep, a circle is a mathematical definition (center, radius, normal).  
* **Sweeping Capabilities:** OCCT provides advanced algorithms like BRepOffsetAPI\_MakePipe. This function allows a developer to define a complex 3D wire (the rebar centerline path) and a face (the circular cross-section) and mathematically "sweep" the profile along the path.3  
* **Fillet Handling:** Crucially, OCCT handles the topology of fillets (bends) automatically. When generating a stirrup, the kernel calculates the precise geometry required to create a smooth tangent transition between the straight leg and the curved corner, ensuring the solid is valid and watertight.19

### **3.2 Manifold Integration**

Recognizing that OCCT can be computationally heavy for certain operations, bitbybit-dev also integrates **Manifold**.20

* **Performance Booleans:** Manifold is a newer geometry library explicitly optimized for extremely fast boolean operations on mesh data.  
* **Rebar Use Case:** While OCCT is ideal for *generating* the pristine rebar shape, Manifold is potentially superior for *clash detection*. An application could tessellate the rebar and concrete into high-res meshes and use Manifold to check for collisions in milliseconds, a task that might be slower using OCCT's precise analytic booleans.20

### **3.3 Asynchronous Processing via Web Workers**

A major architectural contribution of bitbybit-dev is the encapsulation of these kernels into **Web Workers** via packages like @bitbybit-dev/occt-worker.21

* **The Blocking Problem:** Geometric calculations in OCCT are CPU-intensive. Running a "sweep" operation for 1,000 bars on the main browser thread would freeze the UI, rendering the app unresponsive.  
* **The Worker Solution:** Bitbybit-dev’s architecture forces these calculations onto a background thread. The main application sends a message ("Generate Stirrup Type A"), the worker crunches the B-Rep math, tessellates the result into a mesh, and sends the lightweight buffers back to the main thread for rendering. This ensures a fluid 60 FPS user experience even during heavy computation.20

### **3.4 Visual Programming and TypeScript Support**

Bitbybit-dev lowers the barrier to entry by offering dual interfaces:

1. **Visual Programming:** Integration with Rete and Blockly allows structural engineers who may not be expert coders to define rebar logic using node-based graphs.7  
2. **Monaco Editor:** For professional developers, it provides full TypeScript support with IntelliSense in the browser (via the Monaco editor), enabling the development of complex, algorithmic rebar generation scripts.4

### **3.5 Interoperability and Export**

Because bitbybit-dev maintains the geometry as B-Reps (until visualization), it supports exporting to **STEP (.stp)** and **IGES** formats.3

* **Fabrication Readiness:** CNC rebar bending machines typically require vector or analytical data, not meshes. A STEP file generated by OCCT contains the precise analytic curves required for fabrication machinery. A mesh export from a purely visualization-based library would require error-prone reverse engineering to recover these curves.

## **4\. Geometric Deep Dive: The Rebar Generation Challenge**

To understand the practical application of these tools, we must analyze the specific geometric problem of generating a bent reinforcement bar.

### **4.1 The "Sweep" Problem in Detail**

Consider the generation of a standard U-bar (Shape Code 21\) with two 90-degree bends.

Approach A: Mesh-Based Generation (That Open Company/Three.js)  
Without a kernel, the developer works with THREE.TubeGeometry or constructs a custom mesh algorithm.

* **Process:** The developer must manually calculate the vertices of the centerline. To create the bend, they must mathematically interpolate points along a curve (e.g., a Bezier or Catmull-Rom spline) that approximates the bend radius.  
* **Issues:**  
  * **Approximation:** The resulting bend is a segmented polygon, not a true arc.  
  * **Artifacts:** "Kinking" or self-intersection often occurs at the inner radius of tight bends if the mesh algorithm is not sophisticated.  
  * **Texture Mapping:** Managing UV coordinates for rebar rib patterns across a manually generated mesh bend is non-trivial.  
  * **Data Loss:** Once generated as a mesh, the semantic knowledge that "this is a 16mm radius bend" is lost. It is just a collection of triangles.

Approach B: Kernel-Based Generation (Bitbybit-dev/OCCT)  
The developer defines the topology: "A linear edge of length $L1$, an arc of radius $R$, and a linear edge of length $L2$."

* **Process:** The makePipe algorithm sweeps the circular profile.  
* **Advantages:**  
  * **Validity:** The kernel guarantees the resulting solid is manifold (watertight).  
  * **Tangency:** The transition from straight to curved is mathematically perfect.  
  * **Parametric History:** The underlying wire remains available. If the user changes the bend radius, the kernel simply re-sweeps the profile.  
  * **Fabrication Data:** The length of the centerline wire (for cutting lists) can be queried directly from the kernel with high precision (GProp\_GProps), accounting for the elongation at the neutral axis if configured.

### **4.2 The Tessellation Tax**

A critical performance consideration identified in the research is the "Tessellation Tax."

* **The Conflict:** Browsers cannot render B-Reps directly; they must be tessellated into meshes.  
* **The Cost:** Converting an OCCT shape to a mesh is computationally expensive. Doing this for 10,000 unique bars is unfeasible.  
* **The Strategy:** This drives the necessity of a hybrid approach. The application should use OCCT to generate the *unique* shapes (e.g., the 5 types of bars in the project) and then use That Open Company's Fragments to *instance* those meshes thousands of times. Relying on OCCT to output 10,000 unique meshes would cause a "Polygon Explosion" and crash the browser.

## **5\. Comparison of Business and Strategic Viability**

The choice of library dictates not just technical capability but also the long-term business stability of the software product.

### **5.1 Ecosystem Maturity and Support**

**That Open Company** has cultivated a highly active, domain-specific community.

* **Documentation:** Extensive documentation, tutorials, and API references are available.23  
* **Commercial Support:** The "Pioneers" program and "That Open University" indicate a model where the open-source core is sustained by paid training and enterprise support services.10 This suggests longevity and a roadmap aligned with industry needs (e.g., IFC4 support).  
* **BIM Alignment:** The tools are built by BIM experts for BIM problems. Features like "Spatial Tree" navigation and "IFC Property" extraction are native.6

**Bitbybit-dev** serves a broader "computational design" market.

* **Niche:** It appeals to advanced algorithmic designers, digital fabricators, and 3D printing enthusiasts.20  
* **Integration:** The platform demonstrates commercial viability through integrations like "3D Bits" for Shopify, proving the tech stack works in production e-commerce environments.25  
* **Dependency:** It relies heavily on the upstream maintenance of the opencascade.js and manifold projects. While bitbybit adds significant value through wrapping and workers, the core mathematical engines are external dependencies.

### **5.2 Licensing and Legal**

* **That Open Company:** Primarily uses permissive licenses (MPL 2.0 or MIT) for its components 26, making it safe for proprietary commercial SaaS development.  
* **Bitbybit-dev:** The wrapper libraries are MIT licensed.17 However, developers must be aware that the core **OpenCascade** kernel is LGPL. While utilizing it via dynamic linking (or Wasm) generally satisfies LGPL requirements, strictly proprietary, closed-source modifications to the *kernel itself* would trigger copyleft provisions. For standard usage (using the library to generate geometry), it is generally commercially safe.

## **6\. Workflow Synthesis: The Hybrid Architecture**

The research data overwhelmingly suggests that neither tool is a complete solution for a production-grade rebar detailing application. That Open Company lacks the kernel strength for creation; Bitbybit-dev lacks the instancing engine for large-scale rendering. Therefore, the optimal architecture is a **Hybrid Implementation**.

### **6.1 Architectural Blueprint**

The following table outlines the proposed responsibility assignment for each library within a single application:

| Functional Requirement | Technology Solution | Rationale |
| :---- | :---- | :---- |
| **Input Handling** | React / Vue \+ **OBC UI** | Standard UI frameworks for user input; OBC for BIM-specific widgets.10 |
| **Geometry Calculation** | **Bitbybit-dev (OCCT Worker)** | Offload math to worker thread. Use OCCT to generating valid swept solids with precise bend radii.22 |
| **Fabrication Data** | **Bitbybit-dev (OCCT)** | Extract centerline lengths and export STEP files for CNC machines.3 |
| **Mesh Conversion** | **Bitbybit-dev (Tessellation)** | Convert B-Rep solids to high-fidelity meshes within the worker. |
| **Scene Management** | **That Open Company (Fragments)** | Receive meshes from worker. Create FragmentsGroup. Apply instancing matrices.2 |
| **Large Model Streaming** | **That Open Company (BIM Tiles)** | Stream geometry segments based on camera position to manage memory.13 |
| **Interaction (Picking)** | **That Open Company (OBC)** | Use OBC's optimized raycaster to select individual bars within the instance group.27 |
| **File I/O** | **That Open Company (Web-IFC)** | Handle import/export of the full project context in IFC format.28 |

### **6.2 Step-by-Step Workflow**

1. **Initialization:** The app initializes a Three.js scene using OBC.Components. Ideally, it starts the bitbybit-dev Web Workers in the background to ready the kernel.  
2. **User Action:** The user selects a concrete column (imported via web-ifc) and applies a "Stirrup Pattern" (e.g., \#4 bar @ 12" spacing).  
3. **Async Generation:**  
   * The app sends the column's bounding box and rebar parameters to the **Bitbybit Worker**.  
   * **Inside Worker:** OCCT calculates the rounded rectangle path and sweeps the circular profile. It performs boolean subtractions if checking for interference.  
   * **Tessellation:** The worker tessellates the resulting solid into a buffer geometry (vertices/normals).  
4. **Data Handoff:** The worker transfers the buffer (Zero-Copy) back to the main thread.  
5. **Visualization:**  
   * The main thread takes the single geometry buffer.  
   * It calculates the 20 positions along the column where this stirrup repeats.  
   * It uses OBC.FragmentsGroup to create a single Fragment with 20 instances.  
6. **Result:** The user sees 20 perfectly formed stirrups instantly. The memory cost is that of *one* stirrup. The UI remains responsive throughout the process.

## **7\. Conclusion**

In the contest between **That Open Company** and **bitbybit-dev** for rebar detailing supremacy, the answer is not "one or the other," but "which tool for which task?"

**That Open Company** is the definitive solution for **visualization and data structure**. Its Fragments protocol is the only open-source technology currently available that can realistically render the hundreds of thousands of elements required for a commercial-grade rebar application in a browser. Its deep integration with IFC ensures the application remains a valid citizen of the OpenBIM ecosystem.

**Bitbybit-dev** is the definitive solution for **geometry authoring**. It provides the raw mathematical power of OpenCascade in a developer-friendly, asynchronous package. Attempting to build a rebar generator without such a kernel—relying on mesh manipulation or "Clay"—would result in a fragile system incapable of meeting the strict precision requirements of structural fabrication.

Therefore, the recommendation for professional development teams is to **integrate both**. Use bitbybit-dev as the "computational engine" to manufacture the virtual steel, and use That Open Company as the "storage and display engine" to organize it into a performant, navigable Building Information Model. This symbiotic architecture maximizes the strengths of the modern web stack, delivering an application that is both mathematically rigorous and visually performant.

#### **Works cited**

1. An Integrated Open-Source Digital Twin Platform for Federal Built Assets in Canada, accessed November 19, 2025, [https://awards.buildingsmart.org/gallery/NpJQxbDr/olDdENvO?search=008f0660e1c72b45-22](https://awards.buildingsmart.org/gallery/NpJQxbDr/olDdENvO?search=008f0660e1c72b45-22)  
2. FragmentsManager | That Open docs, accessed November 19, 2025, [https://docs.thatopen.com/Tutorials/Components/Core/FragmentsManager](https://docs.thatopen.com/Tutorials/Components/Core/FragmentsManager)  
3. OpenCascade Solid Geometry Kernel Integrated Into "Bit by bit developers" Web Application, accessed November 19, 2025, [https://www.youtube.com/watch?v=K8gDhXYR2x0](https://www.youtube.com/watch?v=K8gDhXYR2x0)  
4. @bitbybit-dev/base \- npm, accessed November 19, 2025, [https://www.npmjs.com/package/@bitbybit-dev/base](https://www.npmjs.com/package/@bitbybit-dev/base)  
5. That Open Company, accessed November 19, 2025, [https://thatopen.com/](https://thatopen.com/)  
6. That Open Company \- OSArch Community, accessed November 19, 2025, [https://community.osarch.org/discussion/1551/that-open-company](https://community.osarch.org/discussion/1551/that-open-company)  
7. Power of Fragments. A simple yet magnificent wrapper around… | by vishwajeet mane | Medium, accessed November 19, 2025, [https://medium.com/@manevishwajeet1/power-of-fragments-b06b0af4132b](https://medium.com/@manevishwajeet1/power-of-fragments-b06b0af4132b)  
8. Getting started | That Open docs, accessed November 19, 2025, [https://docs.thatopen.com/fragments/getting-started](https://docs.thatopen.com/fragments/getting-started)  
9. ThatOpen/engine\_fragment \- GitHub, accessed November 19, 2025, [https://github.com/ThatOpen/engine\_fragment](https://github.com/ThatOpen/engine_fragment)  
10. Pioneers \- That Open Company, accessed November 19, 2025, [https://thatopen.com/f003-p02-pioneers-pre-apply-closed](https://thatopen.com/f003-p02-pioneers-pre-apply-closed)  
11. IFC-native web-based modeler: Free and open-source \- Blender 3D Architect, accessed November 19, 2025, [https://www.blender3darchitect.com/bim/ifc-native-web-based-modeler-free-and-open-source/](https://www.blender3darchitect.com/bim/ifc-native-web-based-modeler-free-and-open-source/)  
12. I've never been an artist but I love 3d printing. So 5 years ago I went through ... | Hacker News, accessed November 19, 2025, [https://news.ycombinator.com/item?id=45458986](https://news.ycombinator.com/item?id=45458986)  
13. IFC BIM tiles implementation for streaming geometries \- (open bim components library), accessed November 19, 2025, [https://stackoverflow.com/questions/78116171/ifc-bim-tiles-implementation-for-streaming-geometries-open-bim-components-lib](https://stackoverflow.com/questions/78116171/ifc-bim-tiles-implementation-for-streaming-geometries-open-bim-components-lib)  
14. 🧹 Keeping them clean | That Open docs, accessed November 19, 2025, [https://docs.thatopen.com/components/clean-components-guide](https://docs.thatopen.com/components/clean-components-guide)  
15. Comprehensive framework for dynamic energy assessment of building systems using IFC graphs and Modelica \- ResearchGate, accessed November 19, 2025, [https://www.researchgate.net/publication/389148303\_Comprehensive\_framework\_for\_dynamic\_energy\_assessment\_of\_building\_systems\_using\_IFC\_graphs\_and\_Modelica](https://www.researchgate.net/publication/389148303_Comprehensive_framework_for_dynamic_energy_assessment_of_building_systems_using_IFC_graphs_and_Modelica)  
16. Bit By Bit Developers \- GitHub, accessed November 19, 2025, [https://github.com/bitbybit-dev](https://github.com/bitbybit-dev)  
17. bitbybit-dev/occt \- NPM, accessed November 19, 2025, [https://www.npmjs.com/package/@bitbybit-dev/occt](https://www.npmjs.com/package/@bitbybit-dev/occt)  
18. Pipe/tube along path \- sketchucation, accessed November 19, 2025, [https://community.sketchucation.com/topic/149577/pipe-tube-along-path](https://community.sketchucation.com/topic/149577/pipe-tube-along-path)  
19. New Bitbybit Release Packed With CAD Features \- Use With ThreeJS & BabylonJS Game Engines \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=9Ee4q0ErSKk](https://www.youtube.com/watch?v=9Ee4q0ErSKk)  
20. Excited To Support Manifold 3D Geometry Kernel In BITBYBIT DEV Platform For Creative CAD Programming \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=kFB-XwS79ws](https://www.youtube.com/watch?v=kFB-XwS79ws)  
21. bitbybit-dev/bitbybit-occt-worker: This package exposes bitbybit-occt package through a webworker as a separate asynchronous API that is also using a variant of memoization caching. \- GitHub, accessed November 19, 2025, [https://github.com/bitbybit-dev/bitbybit-occt-worker](https://github.com/bitbybit-dev/bitbybit-occt-worker)  
22. bitbybit-dev/occt-worker \- NPM, accessed November 19, 2025, [https://npmjs.com/package/@bitbybit-dev/occt-worker](https://npmjs.com/package/@bitbybit-dev/occt-worker)  
23. @thatopen/components | That Open docs, accessed November 19, 2025, [https://docs.thatopen.com/api/@thatopen/components/](https://docs.thatopen.com/api/@thatopen/components/)  
24. From STEP to GLTF \- Convert PRO CAD 3D Models For 3D Bits Shopify App \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=7mqd2FLlpcU](https://www.youtube.com/watch?v=7mqd2FLlpcU)  
25. bitbybit dev \- YouTube, accessed November 19, 2025, [https://www.youtube.com/@bitbybitdev](https://www.youtube.com/@bitbybitdev)  
26. That Open \- GitHub, accessed November 19, 2025, [https://github.com/ThatOpen](https://github.com/ThatOpen)  
27. Open-bim-components \- Global ID/Express ID from Selection \- Stack Overflow, accessed November 19, 2025, [https://stackoverflow.com/questions/78195325/open-bim-components-global-id-express-id-from-selection](https://stackoverflow.com/questions/78195325/open-bim-components-global-id-express-id-from-selection)  
28. ThatOpen/engine\_web-ifc: Reading and writing IFC files with Javascript, at native speeds., accessed November 19, 2025, [https://github.com/ThatOpen/engine\_web-ifc](https://github.com/ThatOpen/engine_web-ifc)