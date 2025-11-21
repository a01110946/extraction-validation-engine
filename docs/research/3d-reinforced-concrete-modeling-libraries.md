
# **Computational Frameworks for ACI-Compliant Reinforced Concrete Modeling: A Technical Evaluation of Python and JavaScript Ecosystems**

## **1\. Introduction: The Semantic Gap in Automated Structural Design**

The architecture, engineering, and construction (AEC) industry stands at a precipice of a digital transformation driven by the convergence of probabilistic artificial intelligence and deterministic structural engineering. The specific challenge of developing a web-based application capable of extracting reinforced concrete (RC) structural elements—columns, beams, walls, and foundations—from static imagery and converting them into high-fidelity, three-dimensional Building Information Models (BIM) represents a non-trivial exercise in computational geometry and semantic data structuring. This report provides an exhaustive technical analysis of the software ecosystems required to bridge the "semantic gap" between the unstructured pixel data processed by Large Language Models (LLMs) and the rigorous, mathematically defined schema required by modern construction standards, specifically the American Concrete Institute’s ACI 318 code.

The transition from an image to a constructible model requires a pipeline that moves through several states of data fidelity: from the probabilistic token outputs of an LLM, to the structured validation of Pydantic schemas, to the implicit parametric definitions of the Industry Foundation Classes (IFC), and finally to the explicit tessellated geometry required for web-based visualization. This report posits that no single language or library can effectively handle this entire pipeline. Instead, a hybrid architecture is required: a Python-based backend acting as the "compliance engine" for physics and BIM schema generation, and a JavaScript-based frontend dedicated to performant visualization and user interactivity.

We analyze the capabilities, limitations, and integration strategies of key libraries including **IfcOpenShell**, **ConcreteProperties**, and **CadQuery** on the server side, and **Three.js**, **Web-IFC**, and **Speckle** on the client side. Special attention is paid to the nuances of reinforced concrete detailing—specifically the algorithmic generation of rebar cages involving complex stirrup geometries, hook bends, and spacing rules—which distinguishes this application from generic 3D modeling tools. The report further explores how these libraries can be orchestrated to ensure compliance with American standards, providing a pathway from raw extraction to engineering-grade validation.

---

## **2\. The Python Computational Backend: Geometry, Physics, and Standards**

Python serves as the foundational bedrock for the proposed application. Its dominance in the AEC sector is not merely a function of syntax popularity but is rooted in its extensive ecosystem of libraries that handle scientific computing, geometry processing, and BIM interoperability. In the context of an app that leverages LLMs and Pydantic, Python acts as the logical bridge, translating the extracted JSON schemas into interoperable engineering data.

### **2.1 IfcOpenShell: The Backbone of Programmatic BIM**

For any application aiming to produce professional-grade structural models, the ability to generate Industry Foundation Classes (IFC) files is non-negotiable. **IfcOpenShell** stands as the definitive open-source library for parsing, modifying, and creating IFC data using Python.1 Unlike generic CAD libraries that might represent a column as a simple extrusion, IfcOpenShell is schema-aware, enforcing the strict hierarchy and typing required by the ISO 16739 standard. This semantic richness is critical when modeling reinforced concrete, where the distinction between the concrete "host" and the steel "reinforcement" must be preserved for downstream analysis and quantity take-offs.

#### **2.1.1 The Semantics of Reinforced Concrete**

The primary challenge in creating ACI-compliant models is the accurate representation of reinforcement. IfcOpenShell allows for the instantiation of IfcReinforcingBar entities, which are semantically distinct from generic geometric objects. A single IfcReinforcingBar instance can represent a single bar or a group of identical bars (e.g., a row of longitudinal reinforcement), depending on its type definition and placement parameters.2

The library supports the assignment of these bars to their host elements—IfcColumn, IfcBeam, IfcWall, or IfcFooting—via the IfcRelAggregates or IfcRelContainedInSpatialStructure relationships.1 This logical containment is essential for the user's web app; it ensures that when a user selects a column in a viewer, the associated rebar cage is recognized as a constituent part of that assembly, rather than floating, unrelated geometry. Furthermore, the library supports the definition of IfcMaterial properties, allowing the Python backend to assign specific steel grades (e.g., ASTM A615 Grade 60\) to the rebar entities, which is a fundamental requirement for ACI 318 compliance.3

#### **2.1.2 Implicit Geometry and the IfcSweptDiskSolidPolygonal**

One of the most significant technical insights regarding IfcOpenShell is its handling of rebar geometry through implicit definition. Rather than storing a heavy triangular mesh for every ridge on a rebar, IfcOpenShell utilizes the IfcSweptDiskSolidPolygonal entity. This entity defines the rebar geometry by sweeping a 2D circular profile (the cross-section) along a 3D polyline (the directrix).4

This approach is highly efficient but introduces a geometric complexity regarding the "bending" of steel. A standard polyline consists of linear segments meeting at sharp vertices. However, ACI 318 mandates strict minimum bend radii for rebar hooks and stirrup corners to prevent the crushing of concrete inside the bend and the fracture of the steel bar. For example, a standard stirrup hook must have a bend diameter of at least $4d\_b$ for bar sizes \#3 through \#5. If the Python script were to generate a simple rectangular polyline for a stirrup, the resulting model would feature physically impossible 90-degree sharp corners.

IfcOpenShell addresses this through the FilletRadius attribute within the IfcSweptDiskSolidPolygonal class.4 By programmatically setting this attribute to the calculated ACI minimum radius, the library automatically generates the smooth toroidal transition between the linear segments of the stirrup. Research indicates that properly utilizing this attribute is the difference between a schematic model and a constructible one; failure to set the FilletRadius results in "straight" corners that would flag errors in any clash detection or code-checking software.5

#### **2.1.3 Explicit Geometry Conversion for Analysis**

While implicit geometry is ideal for file storage, the web application may require explicit geometry for tasks like generating cross-section images or performing boolean operations (e.g., subtracting the volume of a pipe penetration from a wall). IfcOpenShell includes a robust geometry engine based on the Open CASCADE Technology (OCCT) kernel.6 This engine can tessellate the parametric IFC entities into explicit boundary representations (B-Rep) or triangular meshes.

This capability enables a powerful workflow: the Python backend can generate the compliant IfcReinforcingBar, use the geometry engine to convert it to a mesh, and then slice that mesh at specific intervals to generate the "cross-sections" requested by the user. This ensures that the 2D drawings generated by the app are strictly derived from the 3D model, maintaining absolute consistency between the two views.

### **2.2 ConcreteProperties: The Physics of the Section**

The user’s query emphasizes the need for "extracting information," which implies a utility beyond mere drawing. Structural engineering is the study of capacity and behavior. **ConcreteProperties** is a specialized Python library identified in the research that bridges the gap between geometric modeling and structural analysis.7 It is essential for validating the Pydantic data extracted by the LLM against physical realities.

#### **2.2.1 Automated Section Analysis**

Once the LLM extracts the geometric arrangement (e.g., a 12x12 inch column with 4 \#8 bars), concreteproperties can be employed to calculate the section’s engineering properties. The library discretizes the composite section into fibers of concrete and steel, allowing for the calculation of:

* **Gross Properties ($I\_g$):** The properties of the uncracked section, used for initial stiffness estimates.  
* **Cracked Properties ($I\_{cr}$):** The properties of the section after the concrete tension zone has failed, crucial for accurate deflection calculations.  
* **Ultimate Capacities:** The library calculates the moment capacity ($M\_n$) and axial capacity ($P\_n$) by iterating through strain compatibility states.8

#### **2.2.2 Interaction Diagrams and ACI Compliance**

For the "structural columns" mentioned in the user query, a static capacity number is insufficient. Columns are subjected to combined axial loads and bending moments. The standard method for analyzing this is the P-M (Axial-Moment) Interaction Diagram, which defines the safe operating envelope of the column.

ConcreteProperties automates the generation of these diagrams.9 By integrating this library, the web app can generate a visual plot showing the column's capacity curve alongside the LLM-extracted data. This allows for immediate "sanity checks." For instance, if the extracted rebar configuration results in a capacity that is drastically lower than what is typical for a column of that size, or if the reinforcement ratio $\\rho$ falls outside the ACI 318 limits (1% to 8%), the application can flag this as a potential extraction error. This moves the application from being a passive modeling tool to an active engineering assistant.10

#### **2.2.3 Stress-Strain Profiling**

The library also supports the generation of stress profile plots, showing the distribution of compressive and tensile forces across the cross-section under a given load.8 Visualizing this data can help users understand the mechanics of the generated element, reinforcing the educational or analytical value of the platform.

### **2.3 CadQuery: Parametric Solid Modeling for Complex Geometry**

While IfcOpenShell is the master of the BIM schema, it operates largely on implicit primitives. For generating complex, non-standard concrete geometries—such as corbels, tapered retaining walls, or intricate foundation piers—**CadQuery** offers a robust parametric alternative.11

CadQuery is a Python library that wraps the Open CASCADE kernel (OCCT), providing a fluent API for constructive solid geometry (CSG) and boundary representation (B-Rep) modeling. It is often described as "jQuery for CAD" because of its ability to chain commands, such as workplane().rect().extrude().faces("\>Z").hole().11

* **Procedural Generation:** CadQuery’s logic aligns perfectly with the structured data output of Pydantic. If the LLM identifies a "Beam with a ledge," CadQuery scripts can parametrically define that ledge based on variables (width, depth, ledge height).  
* **Precision Modeling:** Unlike mesh-based modelers (like standard Blender scripting), CadQuery uses B-Reps, which support precise mathematical definitions of curves and surfaces. This allows for operations like adding chamfers or fillets to concrete edges with manufacturing-level precision.11  
* **Interoperability:** CadQuery can export STEP files, which are widely used in mechanical CAD and can be imported into most BIM software. It can also generate high-quality STL or GLTF meshes for the frontend viewer.

The research suggests using CadQuery as a "geometry engine" supplement to IfcOpenShell. For standard prismatic elements (rectangular beams/columns), IfcOpenShell is sufficient. For elements with complex subtractive geometry (e.g., a wall with a hexagonal opening pattern), CadQuery can generate the geometry, which can then be tessellated and wrapped in an IFC container.

### **2.4 StructuralCodes and Handcalcs: The Reporting Layer**

To strictly adhere to ACI standards, the application must do more than model; it must verify. The **StructuralCodes** library serves as a growing repository of design code models, allowing developers to decouple the engineering logic from the application code.12 While currently heavily focused on Eurocode, its architecture supports the implementation of ACI 318 material models and safety factors.

Furthermore, the **Handcalcs** library offers a unique value proposition for a professional engineering app. It allows Python calculations to be rendered as LaTeX-formatted reports that resemble handwritten engineering notes.14

* **Transparency:** Structural engineers are often skeptical of "black box" outputs. By using Handcalcs, the web app can generate a PDF report showing exactly *how* the rebar development length or the column capacity was calculated, displaying the formulas, variable substitutions, and final results.  
* **Documentation:** This feature transforms the extracted model into a documented engineering artifact, providing the user with a record of the assumptions made during the AI extraction process.

### **2.5 Hypar Elements: A Schema for Generative Design**

**Hypar Elements** is a library (primarily C\# but with a schema relevant to Python) designed for creating building elements in a generative design context.16 While the user is working in Python/JS, the *schema* defined by Hypar is highly instructive for structuring the Pydantic models.

The Elements schema treats structural components like Beam or Column as first-class citizens inheriting from a GeometricElement base class, which possesses properties like Transform, Material, and Profile.17 Adopting this schema structure for the Pydantic models ensures that the data is organized in a way that is compatible with modern computational design workflows. It encourages a separation of concerns where the "Profile" (the 2D cross-section) is defined independently of the "Path" (the extrusion curve), a model that aligns perfectly with the IfcSweptDiskSolid logic in IfcOpenShell.

---

## **3\. The JavaScript Visualization Frontend: Rendering and Interactivity**

While the Python backend handles the heavy lifting of logic and schema generation, the user experience lives in the browser. The JavaScript ecosystem provides the tools necessary to render the complex 3D geometry of reinforced concrete, conduct lightweight geometric operations, and provide an interactive interface for model inspection.

### **3.1 Three.js: The Rendering Engine of Choice**

**Three.js** is universally cited in the research as the standard for WebGL-based 3D graphics.18 For modeling reinforced concrete, specific geometric classes and techniques within Three.js are particularly relevant.

#### **3.1.1 Modeling Rebar: The TubeGeometry Strategy**

The visualization of rebar cages involves rendering potentially hundreds or thousands of cylindrical shapes following specific paths. The TubeGeometry class in Three.js is the primary tool for this task. It constructs a tube that extrudes a circle along a 3D curve.21

* **Curve Definition:** The path of the rebar is defined using a CurvePath, which is a composite of multiple curves. For a longitudinal bar, this might be a simple LineCurve3. For a stirrup, however, the path is a closed loop consisting of four straight LineCurve3 segments connected by four QuadraticBezierCurve3 or ArcCurve segments representing the corners.  
* **The Bend Radius Challenge:** Just as in the backend, the frontend must accurately depict the bend radius. Three.js does not automatically round corners. The application must algorithmically calculate the control points for the Bezier curves to match the ACI minimum bend radius derived from the bar diameter. This ensures that the visual model looks "engineered" rather than schematic.22

#### **3.1.2 TubeGeometry vs. ExtrudeGeometry**

The research highlights a trade-off between TubeGeometry and ExtrudeGeometry.23

* **ExtrudeGeometry:** This class allows extruding an arbitrary 2D Shape along a path. This would theoretically allow for modeling the *ribs* or deformations of the rebar by using a non-circular profile. However, generating a ribbed profile along a complex 3D path introduces significant computational overhead and issues with "Frenet frame" rotation (the orientation of the profile as it moves along the curve).23  
* **TubeGeometry:** This class is optimized for circular cross-sections and handles frame rotation more robustly for standard structural shapes.  
* **Recommendation:** The analysis suggests utilizing TubeGeometry for the rebar geometry to maximize performance. The visual detail of ribs should be handled via a **Normal Map** or texture in the material shader, rather than geometric displacement, to keep the polygon count manageable.19

#### **3.1.3 Performance Optimization: The InstancedMesh**

A major technical hurdle identified in the research is the performance cost of rendering dense rebar cages. A single column might have 20 stirrups; a large foundation mat might have thousands of bars. Creating a unique THREE.Mesh object for every single bar will choke the browser's draw calls, leading to significant lag.

The solution is **InstancedMesh**.19 This Three.js class allows the application to define a single geometry (e.g., a unit cylinder or a single stirrup shape) and render it thousands of times in a single draw call. Each instance can have its own position, rotation, and scale matrix. For a wall with regularly spaced vertical bars, the application can instantiate one vertical bar geometry and use InstancedMesh to array it along the wall's length. This technique effectively decouples the visual complexity of the model from the rendering cost, enabling the smooth visualization of fully detailed RC structures.

### **3.2 Web-IFC (IFC.js): Client-Side BIM Authoring**

While the Python backend is capable of generating IFC files, the **Web-IFC** library (often part of the IFC.js ecosystem) provides a powerful capability: client-side BIM generation.24 Web-IFC is a WebAssembly (WASM) library that enables the reading and writing of IFC data directly in the browser at native speeds.

* **Writing IfcReinforcingBar:** Research confirms that Web-IFC supports writing IfcReinforcingBar entities.25 This opens up a flexible architectural option: the Python backend could send lightweight JSON data (the Pydantic schema) to the frontend, and the frontend could generate the downloadable IFC file locally using Web-IFC. This reduces server load and allows for immediate file generation without network latency.  
* **Geometry Loading:** If the Python backend *does* generate the IFC file, web-ifc-three is the standard loader for bringing that file into the Three.js scene.26 It handles the complex translation of IFC implicit geometry (like the IfcSweptDiskSolidPolygonal) into the explicit meshes required by Three.js. This ensures that the user sees exactly what is contained in the BIM file.

### **3.3 OpenJSCAD: Boolean Operations in the Browser**

For scenarios where the web app needs to perform geometric editing—such as punching a hole in a wall for a pipe or modifying a beam profile—**OpenJSCAD** (specifically the @jscad/modeling package) provides a robust Constructive Solid Geometry (CSG) kernel in JavaScript.28

* **Browser-Based Booleans:** Three.js does not have a native CSG engine. OpenJSCAD fills this gap, allowing for boolean operations (union, difference, intersection) to be performed on meshes directly in the browser. The resulting geometry can then be converted back to a Three.js buffer geometry for rendering. This capability enables a higher level of interactivity, allowing users to modify the extracted models "live" without a round-trip to the server.

### **3.4 D3.js: Data Visualization**

To support the user's request for "cross sections" and deeper insights, **D3.js** is identified as a powerful companion to Three.js.30 While Three.js handles the 3D spatial model, D3.js excels at 2D data visualization.

* **Interaction Diagrams:** The P-M interaction data generated by concreteproperties on the backend consists of arrays of data points. D3.js can render these as interactive SVG charts in the web interface.  
* **Cross-Section Views:** D3.js can also be used to draw precise, scalable vector graphics of the element cross-sections, complete with labels and dimensions, providing a "drawing-like" view that complements the 3D model.

---

## **4\. Interoperability and Data Transport: The Bridge**

The architecture of the proposed application relies on the seamless flow of data between the Python backend and the JavaScript frontend. **Speckle** emerges from the research as the most sophisticated middleware for managing this interoperability.32

### **4.1 Speckle: The Data Hub**

Speckle is an open-source data platform designed specifically for the AEC industry. It provides SDKs for both Python (specklepy) and JavaScript (@speckle/viewer, @speckle/objectloader), making it the ideal "glue" for this hybrid ecosystem.33

* **The Base Object:** Speckle uses a dynamic Base object class. The user's Pydantic models can be mapped to or serialized as Speckle Base objects.34 This allows for the structured transmission of complex object graphs (e.g., a Column object containing a list of Rebar objects, which in turn contain material properties).  
* **The Structural Kit:** Speckle defines a standard "Structural Object Kit" which includes classes for 1D elements (beams/columns) and 2D elements (walls/slabs).36 Leveraging this existing schema prevents the need to "reinvent the wheel" and ensures that the data structure is compatible with other Speckle-connected software (like Revit, Rhino, or ETABS).

### **4.2 The "Curve Transport" Strategy**

A critical technical nuance identified in the research is Speckle's handling of rebar. To optimize performance and reduce payload size, Speckle connectors typically transmit rebar as **curves** (lines) rather than heavy solid meshes.38

* **Architectural Implication:** This dictates a specific workflow for the web app. The Python backend should calculate the *centerline geometry* (curves) and *radius* of the rebar and send this lightweight data to the frontend. The JavaScript frontend, using the Speckle viewer or custom Three.js logic, is then responsible for "inflating" these curves into 3D tubes using TubeGeometry or line shaders.  
* **Efficiency:** This approach drastically reduces the data transfer overhead. Sending the mathematical definition of a spiral (center point, radius, pitch, height) is orders of magnitude smaller than sending a tessellated mesh of that spiral.

---

## **5\. Deep Dive: Implementing American Standards (ACI 318\)**

The requirement to focus on American standards imposes specific geometric and logical constraints that must be hard-coded into the application's logic layers.

### **5.1 Rebar Detailing Rules**

ACI 318 is prescriptive regarding the geometry of reinforcement.

* **Standard Hooks:** The geometry of a hook is not arbitrary. A 90-degree hook for a \#5 bar has a specific minimum bend diameter ($6d\_b$) and a required extension length ($12d\_b$) past the bend. The Python backend must implement a "Hook Geometry Generator" function that accepts a bar size and hook type and returns the compliant polyline geometry.40  
* **Concrete Cover:** The spatial relationship between the rebar and the concrete surface is governed by cover requirements (e.g., 1.5 inches for interior beams, 3 inches for earth-contact foundations). The application must define the "rebar cage" as a volume offset from the host element's boundary. The concreteproperties library can be used to verify if the extracted rebar position satisfies these cover minimums.10

### **5.2 Foundation Elements**

Foundation elements introduce specific complexity. Unlike a column which is typically cast against air, a footing is cast against earth. ACI 318 mandates a 3-inch cover for reinforcement cast against and permanently exposed to earth. The Pydantic schema must differentiate between "Beam" and "Grade Beam" or "Footing" to apply the correct cover rules. IfcOpenShell supports IfcFooting entities, and the logic for generating the rebar cage must account for the different placement vector (typically spread on the XY plane) compared to vertical columns.

### **5.3 Wall Elements and Boundary Zones**

RC walls often require "boundary elements"—concentrated zones of reinforcement at the wall edges to resist high compressive strains. Modeling these requires a shift from discrete bar placement to "zonal" definition. The application logic must identify the edge zones of the wall and populate them with tighter stirrup spacing and heavier longitudinal bars, utilizing InstancedMesh in Three.js to render the vertical bars efficiently without performance degradation.

---

## **6\. Advanced Topics: Topology and Optimization**

For users seeking to go beyond standard prismatic elements, the **COMPAS** framework provides a pathway to advanced computational design.41

### **6.1 Stress-Aligned Rebar**

Traditional rebar layouts are orthogonal (grids). However, research into digital fabrication and structural optimization promotes "stress-aligned" reinforcement, where bars follow the principal stress trajectories of the element.42 COMPAS provides the mesh data structures and topological algorithms required to generate these complex, non-linear flow paths.41 If the web app aims to support cutting-edge design methodologies, integrating COMPAS (specifically compas\_fea and compas\_ifc) would allow it to generate and model these optimized rebar layouts programmatically.43

---

## **7\. Comparative Analysis: Server-Side vs. Client-Side Generation**

A fundamental architectural decision for the web app is determining where the BIM file is generated.

### **7.1 Server-Side Generation (Python / IfcOpenShell)**

* **Pros:** Access to the full power of Python scientific libraries (numpy, scipy, concreteproperties). Robust handling of complex implicit geometry (IfcSweptDiskSolid). Mature, stable IFC writer.  
* **Cons:** Requires server round-trip. Latency. Computationally expensive for the host.  
* **Use Case:** Generating the final "Construction Record" or "Legal" BIM file. Performing detailed structural analysis.

### **7.2 Client-Side Generation (JavaScript / Web-IFC)**

* **Pros:** Instant feedback. No server costs for generation. Leverages user's hardware.  
* **Cons:** Limited access to heavy analysis libraries. JavaScript IFC writing is slightly less mature than IfcOpenShell for obscure entities.  
* **Use Case:** Quick export for visualization. Simple models. Interactive editing.

### **7.3 Recommendation**

The analysis suggests a **Hybrid Architecture**:

1. **Source of Truth:** The Pydantic model (JSON) is the single source of truth.  
2. **Validation:** Python (Server) validates the JSON against ACI 318 using concreteproperties.  
3. **Visualization:** JavaScript (Client) renders the model using Three.js and TubeGeometry derived from the JSON data.  
4. **Export:** The final IFC export is handled by **IfcOpenShell** on the server to ensure maximum compliance and data integrity, leveraging the robust IfcSweptDiskSolidPolygonal implementation.

---

## **8\. Conclusion**

The development of a web application for extracting and modeling reinforced concrete elements requires a sophisticated orchestration of diverse software libraries. It is not enough to simply "draw" the elements; the application must "engineer" them.

**IfcOpenShell** serves as the indispensable backend engine, providing the semantic rigor to create valid BIM files. Its ability to handle IfcReinforcingBar and IfcSweptDiskSolidPolygonal ensures that the generated models are constructible and code-compliant. **ConcreteProperties** transforms the application from a drafting tool into an analysis platform, validating the structural integrity of the extracted designs against ACI 318 standards.

On the frontend, **Three.js** provides the geometric primitives necessary to render complex rebar cages, while **Speckle** acts as the efficient transport layer, serializing complex engineering data into lightweight streams. **Web-IFC** offers a powerful alternative for client-side operations, and **D3.js** enriches the user experience with precise 2D data visualization.

By combining these tools, the application can successfully bridge the semantic gap, converting the probabilistic output of an LLM into the deterministic, high-fidelity data required by the construction industry. The result is a workflow that is not only automated but also transparent, compliant, and structurally sound.

---

## **9\. Detailed Library Reference Table**

| Library | Ecosystem | Primary Role | Key Classes / Entities | Critical ACI 318 Function |
| :---- | :---- | :---- | :---- | :---- |
| **IfcOpenShell** | Python | BIM Generation | IfcReinforcingBar, IfcSweptDiskSolidPolygonal, IfcColumn | Modeling compliant bend radii via FilletRadius. |
| **ConcreteProperties** | Python | Analysis | ConcreteSection, SteelStrand, AnalysisResults | P-M Interaction Diagrams, Strain Compatibility. |
| **Three.js** | JavaScript | Visualization | TubeGeometry, CurvePath, InstancedMesh | Rendering rebar paths; optimizing large cage performance. |
| **Speckle** | Py / JS | Data Transport | Base, Objects.Structural | Transporting rebar centerlines as curves. |
| **Web-IFC** | JavaScript | Client-Side BIM | IfcAPI, OpenModel, WriteModel | Browser-based IFC export/import. |
| **CadQuery** | Python | Solid Modeling | Workplane, Solid, exporters.export | Procedural generation of complex/custom host shapes. |
| **StructuralCodes** | Python | Code Compliance | Eurocodes (extensible to ACI) | Repository for design code formulas. |
| **Handcalcs** | Python | Reporting | handcalcs.render | Generating transparent calculation sheets. |
| **Compas** | Python | Advanced Topology | Network, Mesh, compas\_fea | Generating stress-aligned rebar layouts. |

#### **Works cited**

1. IfcOpenShell \- The open source IFC toolkit and geometry engine, accessed November 19, 2025, [https://ifcopenshell.org/](https://ifcopenshell.org/)  
2. 7.11.3.10 IfcReinforcingBar \- IFC 4.3.2 Documentation, accessed November 19, 2025, [https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcReinforcingBar.htm](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcReinforcingBar.htm)  
3. ifcopenshell.api.material, accessed November 19, 2025, [https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/material/index.html](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/material/index.html)  
4. Class Ifc4::IfcSweptDiskSolidPolygonal — IfcOpenShell documentation \- GitHub Pages, accessed November 19, 2025, [https://ifcopenshell.github.io/docs/rst\_files/class\_ifc4\_1\_1\_ifc\_swept\_disk\_solid\_polygonal.html](https://ifcopenshell.github.io/docs/rst_files/class_ifc4_1_1_ifc_swept_disk_solid_polygonal.html)  
5. \[IfcOpenShell\] IfcSweptDiskSolidPolygonal's "FilletRadius" not working? — OSArch, accessed November 19, 2025, [https://community.osarch.org/discussion/1060/ifcopenshell-ifcsweptdisksolidpolygonals-filletradius-not-working](https://community.osarch.org/discussion/1060/ifcopenshell-ifcsweptdisksolidpolygonals-filletradius-not-working)  
6. Downloads \- IfcOpenShell C++, Python, and utilities, accessed November 19, 2025, [https://ifcopenshell.org/downloads.html](https://ifcopenshell.org/downloads.html)  
7. 5 powerful Python libraries every Structural Engineer should know \- Viktor, accessed November 19, 2025, [https://www.viktor.ai/blog/177/5-powerful-python-libraries-every-structural-engineer-should-know](https://www.viktor.ai/blog/177/5-powerful-python-libraries-every-structural-engineer-should-know)  
8. robbievanleeuwen/concrete-properties: Calculate section properties for reinforced concrete sections. \- GitHub, accessed November 19, 2025, [https://github.com/robbievanleeuwen/concrete-properties](https://github.com/robbievanleeuwen/concrete-properties)  
9. Concreteproperties py: Analyse reinforced concrete cross-sections \- CalcTree, accessed November 19, 2025, [https://www.calctree.com/templates/concreteproperties](https://www.calctree.com/templates/concreteproperties)  
10. Reinforced Concrete Column Design to ACI 318-14 with Python and concreteproperties \- Engineering Skills, accessed November 19, 2025, [https://www.engineeringskills.com/posts/members/reinforced-concrete-column-design-to-aci-318-14-with-python-and-concreteproperties](https://www.engineeringskills.com/posts/members/reinforced-concrete-column-design-to-aci-318-14-with-python-and-concreteproperties)  
11. CadQuery/cadquery: A python parametric CAD scripting framework based on OCCT, accessed November 19, 2025, [https://github.com/CadQuery/cadquery](https://github.com/CadQuery/cadquery)  
12. structuralcodes \- PyPI, accessed November 19, 2025, [https://pypi.org/project/structuralcodes/](https://pypi.org/project/structuralcodes/)  
13. StructuralCodes documentation \- GitHub Pages, accessed November 19, 2025, [https://fib-international.github.io/structuralcodes/](https://fib-international.github.io/structuralcodes/)  
14. connorferster/handcalcs: Python library for converting Python calculations into rendered latex. \- GitHub, accessed November 19, 2025, [https://github.com/connorferster/handcalcs](https://github.com/connorferster/handcalcs)  
15. Introduction to handcalcs: Absolute Beginners Guide \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=ZNFhLCWqA\_g](https://www.youtube.com/watch?v=ZNFhLCWqA_g)  
16. What is Elements? | Hypar Docs, accessed November 19, 2025, [https://hypar-io.github.io/Elements/index.html](https://hypar-io.github.io/Elements/index.html)  
17. Element Types \- Hypar Documentation, accessed November 19, 2025, [https://docs.hypar.io/element-types-73ff02611bf746c297682868f7cba644](https://docs.hypar.io/element-types-73ff02611bf746c297682868f7cba644)  
18. Visualizing rebars in 3D within the structural components. \- SynnopTech CAD Solutions, accessed November 19, 2025, [https://www.synnoptechcad.com/blog/visualizing-rebars-in-3d-within-the-structural-components/](https://www.synnoptechcad.com/blog/visualizing-rebars-in-3d-within-the-structural-components/)  
19. Examples \- Three.js, accessed November 19, 2025, [https://threejs.org/examples/](https://threejs.org/examples/)  
20. Three.js Geometry Tutorial for Beginners \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=K\_CwmMlNmQo](https://www.youtube.com/watch?v=K_CwmMlNmQo)  
21. TubeGeometry – three.js docs, accessed November 19, 2025, [https://threejs.org/docs/\#api/en/geometries/TubeGeometry](https://threejs.org/docs/#api/en/geometries/TubeGeometry)  
22. How can I make good tube with three.js? for example railings \- Questions, accessed November 19, 2025, [https://discourse.threejs.org/t/how-can-i-make-good-tube-with-three-js-for-example-railings/79506](https://discourse.threejs.org/t/how-can-i-make-good-tube-with-three-js-for-example-railings/79506)  
23. ThreeJS \- ExtrudeGeometry depth gives different result than extrudePath \- Stack Overflow, accessed November 19, 2025, [https://stackoverflow.com/questions/25626171/threejs-extrudegeometry-depth-gives-different-result-than-extrudepath](https://stackoverflow.com/questions/25626171/threejs-extrudegeometry-depth-gives-different-result-than-extrudepath)  
24. That Open Engine | web-ifc \- GitHub Pages, accessed November 19, 2025, [https://thatopen.github.io/engine\_web-ifc/docs/](https://thatopen.github.io/engine_web-ifc/docs/)  
25. IfcReinforcingBar \- BimAnt, accessed November 19, 2025, [http://www.bimant.com/ifc/IFC4\_3/RC1/HTML/schema/ifcstructuralelementsdomain/lexical/ifcreinforcingbar.htm](http://www.bimant.com/ifc/IFC4_3/RC1/HTML/schema/ifcstructuralelementsdomain/lexical/ifcreinforcingbar.htm)  
26. BIM Software with IFC.js: Open Source BIM Solutions \- CheckToBuild, accessed November 19, 2025, [https://checktobuild.com/bim-software-with-ifc-js/](https://checktobuild.com/bim-software-with-ifc-js/)  
27. Build the Geometry | IFC.js \- Web Workers & Scene Saving \- GitBook, accessed November 19, 2025, [https://bimwhale.gitbook.io/ifc-js/developer-guide/step-by-step/build-the-geometry](https://bimwhale.gitbook.io/ifc-js/developer-guide/step-by-step/build-the-geometry)  
28. jscad/OpenJSCAD.org: JSCAD is an open source set of modular, browser and command line tools for creating parametric 2D and 3D designs with JavaScript code. It provides a quick, precise and reproducible method for generating 3D models, and is especially useful for creating ready-to-print 3D designs. \- GitHub, accessed November 19, 2025, [https://github.com/jscad/OpenJSCAD.org](https://github.com/jscad/OpenJSCAD.org)  
29. @jscad/modeling \- npm, accessed November 19, 2025, [https://www.npmjs.com/package/@jscad/modeling](https://www.npmjs.com/package/@jscad/modeling)  
30. D3 by Observable | The JavaScript library for bespoke data visualization, accessed November 19, 2025, [https://d3js.org/](https://d3js.org/)  
31. Debugging Cement Hydration Numerical Simulations using D3.js and a CAVE \- National Institute of Standards and Technology, accessed November 19, 2025, [https://www.nist.gov/system/files/documents/2017/05/09/d3rave\_poster.pdf](https://www.nist.gov/system/files/documents/2017/05/09/d3rave_poster.pdf)  
32. JavaScript client for the Speckle API \- GitHub, accessed November 19, 2025, [https://github.com/sasakiassociates/speckle](https://github.com/sasakiassociates/speckle)  
33. specklesystems/specklepy: Python SDK \- GitHub, accessed November 19, 2025, [https://github.com/specklesystems/specklepy](https://github.com/specklesystems/specklepy)  
34. Working with Speckle Objects, accessed November 19, 2025, [https://docs.speckle.systems/developers/sdks/python/guides/how-to-work-with-objects](https://docs.speckle.systems/developers/sdks/python/guides/how-to-work-with-objects)  
35. The Base Object \- Speckle Docs (Legacy), accessed November 19, 2025, [https://speckle.guide/dev/base.html](https://speckle.guide/dev/base.html)  
36. \-Structure of Speckle Kits. | Download Scientific Diagram \- ResearchGate, accessed November 19, 2025, [https://www.researchgate.net/figure/Structure-of-Speckle-Kits\_fig1\_376983963](https://www.researchgate.net/figure/Structure-of-Speckle-Kits_fig1_376983963)  
37. Introducing Structural Classes for Speckle\!, accessed November 19, 2025, [https://speckle.community/t/introducing-structural-classes-for-speckle/1824](https://speckle.community/t/introducing-structural-classes-for-speckle/1824)  
38. Speckle 2.12.2 \- Revit rebar in host elements, accessed November 19, 2025, [https://speckle.community/t/speckle-2-12-2-revit-rebar-in-host-elements/5045](https://speckle.community/t/speckle-2-12-2-revit-rebar-in-host-elements/5045)  
39. Revit Rebar not solid but as lines \- Developers \- Speckle Community, accessed November 19, 2025, [https://speckle.community/t/revit-rebar-not-solid-but-as-lines/13120](https://speckle.community/t/revit-rebar-not-solid-but-as-lines/13120)  
40. IfcReinforcingBar, accessed November 19, 2025, [https://iaiweb.lbl.gov/Resources/IFC\_Releases/R2x3\_final/ifcstructuralelementsdomain/lexical/ifcreinforcingbar.htm](https://iaiweb.lbl.gov/Resources/IFC_Releases/R2x3_final/ifcstructuralelementsdomain/lexical/ifcreinforcingbar.htm)  
41. Computing Rebar Layouts Aligned with the Principal Stress Directions \- CumInCAD, accessed November 19, 2025, [https://papers.cumincad.org/data/works/att/acadia23\_v2\_140.pdf](https://papers.cumincad.org/data/works/att/acadia23_v2_140.pdf)  
42. Computation of Principal Stress-Aligned Rebar Layouts | Request PDF \- ResearchGate, accessed November 19, 2025, [https://www.researchgate.net/publication/333798916\_Computation\_of\_Principal\_Stress-Aligned\_Rebar\_Layouts](https://www.researchgate.net/publication/333798916_Computation_of_Principal_Stress-Aligned_Rebar_Layouts)  
43. COMPAS packages \- Block Research Group, accessed November 19, 2025, [https://brg.ethz.ch/tools/packages](https://brg.ethz.ch/tools/packages)