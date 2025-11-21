
# **Computational Implementation of ACI 318 Detailing Standards and Speckle-Based BIM Interoperability Workflows**

## **1\. Executive Summary**

The contemporary structural engineering landscape is undergoing a fundamental paradigm shift, transitioning from static, document-centric workflows to dynamic, data-driven ecosystems. This evolution demands a rigorous re-evaluation of how standard detailing codes, such as the American Concrete Institute (ACI) 318 Building Code Requirements for Structural Concrete, are integrated into digital tools. Historically, adherence to detailing provisions—specifically regarding reinforcement geometry, hook extensions, bend radii, and concrete cover—relied on manual lookup tables and the interpretative diligence of the detailer. However, in the era of algorithmic design and automated fabrication, these static rules must be transmuted into executable logic capable of validating data fidelity before it ever reaches a modeling environment.

This report presents a comprehensive analysis and technical roadmap for two critical components of this digital transformation. First, it rigorously examines the programmatic encapsulation of ACI 318-19 geometric detailing rules within custom Python data models. By leveraging the validation capabilities of modern libraries such as Pydantic, structural engineers can define classes that not only store data but actively enforce code compliance, automatically populating missing values with code-mandated defaults based on bar size, exposure class, and structural context. This shifts the burden of code compliance from downstream checking to upstream definition.

Second, the report articulates a sophisticated "headless" interoperability architecture using Speckle and Rhino.Inside.Revit (RiR). It addresses the industry-wide challenge of defining and visualizing structural "Types"—such as complex rebar shapes or parametric column profiles—in web-based environments without reliance on heavy, desktop-based geometry kernels. By synthesizing visualization geometry through lightweight algorithms and vector graphics (SVG), and transmitting strictly semantic data via Speckle, this workflow enables a seamless transition to native Building Information Modeling (BIM) elements. The analysis details the precise mechanisms for receiving this data in Grasshopper and instantiating native Revit elements, effectively bridging the gap between abstract web-based definition and concrete documentation.

## **2\. Computational Interpretation of Structural Codes**

The digitization of building codes is not merely a matter of digitizing text but of converting prescriptive prose and tabular data into conditional logic structures. ACI 318-19 represents a complex web of dependencies where geometric requirements for reinforcement are contingent upon material properties, member type, and environmental exposure. To build robust Python libraries, one must first deconstruct these requirements into their fundamental logical atoms.

### **2.1. The Mechanics of Anchorage and Detailing**

The geometric rules found in ACI 318 are not arbitrary; they are derived from the mechanics of bond stress transfer and the need to prevent brittle failure modes such as concrete splitting. Reinforcing bars rely on the mechanical interlock of their deformations (ribs) against the surrounding concrete to transfer tension. When sufficient length for a straight bar development is unavailable—a common scenario in beam-column joints or exterior footings—hooks are employed to provide mechanical anchorage.

The geometry of these hooks is critical. If a bend is too tight, the compressive stresses on the concrete inside the bend can crush the matrix, leading to slip. Conversely, if the tail extension is too short, the hook may pull out before developing the yield strength of the bar.1 This physical reality is encoded in ACI 318 through tables specifying minimum bend diameters and extension lengths.

#### **2.1.1. Standard Hook Geometry (ACI 318-19 Table 25.3.1)**

Table 25.3.1 of ACI 318-19 serves as the primary reference for standard hooks in tension. The code categorizes hooks generally by their bend angle—90 degrees versus 180 degrees—and scales the geometric requirements based on the bar diameter ($d\_b$).

For a **90-degree standard hook**, the code mandates a straight extension at the free end of the bar. This extension ($l\_{ext}$) acts to ensure the hook is fully engaged and to prevent it from straightening under high tensile loads. The requirement is essentially a scalar multiple of the bar diameter: $12d\_b$.2 This relationship is linear and easily programmable. However, the bend diameter ($D$) introduces nonlinearity into the logic. The minimum inside bend diameter changes step-wise as bar sizes increase, reflecting the increased difficulty in bending larger bars without fracturing the steel or crushing the concrete.

* **No. 3 through No. 8 bars:** The minimum diameter is $6d\_b$.  
* **No. 9 through No. 11 bars:** The minimum diameter increases to $8d\_b$.  
* **No. 14 and No. 18 bars:** The minimum diameter jumps to $10d\_b$.2

For a **180-degree standard hook**, the mechanics of anchorage differ slightly, allowing for a potentially shorter extension, but with a fixed minimum absolute length to ensure constructability. The logic dictates that the extension must be the greater of $4d\_b$ or $2.5$ inches ($65$ mm).2 This "max" function is a crucial algorithmic check that prevents the extension from becoming vanishingly small for very thin wires or bars, maintaining a practical minimum for fabrication.

#### **2.1.2. Seismic and Stirrup Hooks (ACI 318-19 Table 25.3.2)**

The requirements become more stringent when bars are used as transverse reinforcement (stirrups and ties), particularly in seismic applications. Here, the function of the hook is not just bar development, but the confinement of the concrete core and the longitudinal buckling restraint of vertical bars. If the cover concrete spalls during a seismic event, the hook must remain engaged in the core.

* **90-Degree Stirrup Hook:** For smaller bars (No. 3 through No. 5), an extension of $6d\_b$ is permitted, provided it is at least 3 inches. For larger bars (No. 6 through No. 8), this increases to $12d\_b$.2  
* **135-Degree Seismic Hook:** This is the gold standard for confinement. The hook must bend 135 degrees into the core. The extension logic requires $6d\_b$ but not less than 3 inches ($75$ mm). This ensures that the tail of the hook is deeply embedded in the confined region of the concrete section, preventing the stirrup from opening up even if the exterior cover spalls off.3

The following table synthesizes these rules into a structured format suitable for coding, identifying the specific breakpoints in bar size that trigger logic changes.

**Table 1: Synthesized ACI 318-19 Hook Geometry Logic**

| Hook Type | Bar Size Range | Min. Inside Bend Diameter (D) | Min. Straight Extension (lext​) | Governing Logic | Source |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **90° Standard** | \#3 – \#8 | $6d\_b$ | $12d\_b$ | Linear Scalar | 2 |
|  | \#9 – \#11 | $8d\_b$ | $12d\_b$ | Linear Scalar | 2 |
|  | \#14, \#18 | $10d\_b$ | $12d\_b$ | Linear Scalar | 2 |
| **180° Standard** | \#3 – \#8 | $6d\_b$ | Max($4d\_b$, 2.5") | Comparison | 2 |
|  | \#9 – \#11 | $8d\_b$ | Max($4d\_b$, 2.5") | Comparison | 2 |
|  | \#14, \#18 | $10d\_b$ | Max($4d\_b$, 2.5") | Comparison | 2 |
| **135° Seismic** | \#3 – \#5 | $4d\_b$ | Max($6d\_b$, 3.0") | Comparison | 3 |
|  | \#6 – \#8 | $6d\_b$ | Max($6d\_b$, 3.0") | Comparison | 3 |

### **2.2. Concrete Cover Requirements and Durability**

Concrete cover is the distance between the outer surface of the reinforcement and the nearest concrete surface. This layer serves multiple protective roles: it passivates the steel against corrosion (by maintaining high alkalinity), provides thermal insulation during fires to delay yield strength reduction, and ensures sufficient bond forces can develop without splitting the surface concrete.8

ACI 318-19 Table 20.6.1.3.1 provides the prescriptive requirements for specified concrete cover ($c\_c$). Programmatically, this is a function of two primary variables: the **Exposure Category** and the **Member Type** (or Bar Size).

* **Cast against and permanently in contact with ground:** This is the most severe condition, typically found in footings and grade beams. The code mandates a minimum of **3 inches (76 mm)**. This large value accounts for the irregularity of earth excavations and the high moisture presence.10  
* **Exposed to weather or in contact with ground:** This category covers elements like retaining walls or exterior columns. The requirement splits based on bar size:  
  * For No. 6 through No. 18 bars: **2 inches (51 mm)**.  
  * For No. 5 bars, W31/D31 wire, and smaller: **1.5 inches (38 mm)**.9  
* **Not exposed to weather or in contact with ground:** This applies to interior conditioned spaces.  
  * Beams, Columns, Pedestals, and Tension Ties: **1.5 inches (38 mm)**. Primary reinforcement needs substantial cover for bond and fire rating.  
  * Slabs, Walls, and Joists (No. 11 and smaller): **0.75 inches (19 mm)**. These distributed elements allow for thinner cover due to redundancy and lower bond demand per unit width.9

It is crucial to note that while epoxy-coated bars provide enhanced corrosion resistance, ACI 318 typically does not allow for a *reduction* in cover thickness solely due to their use, as cover also dictates splitting resistance.11 Therefore, the default logic should enforce the standard values unless specific waivers are programmatically enabled.

## **3\. Python Data Modeling Architecture**

To implement these structural rules effectively, we require a Python library that goes beyond simple data storage. It must be active, self-validating, and aware of the engineering context. While general-purpose structural libraries like concreteproperties 12 and calcbook 14 excel at cross-sectional analysis (calculating moment-curvature interaction diagrams or stress-strain profiles), they are not designed as detailing engines. They typically accept geometry as an input rather than generating compliant defaults from minimal inputs. Thus, defining custom classes using **Pydantic** is the optimal strategy.

### **3.1. Why Pydantic for Structural Schemas?**

Pydantic has emerged as the industry standard for data validation in Python, underpinning modern frameworks like FastAPI and LangChain. Its core value proposition for structural engineering lies in its strict type enforcement and its sophisticated validator system.15

Unlike standard Python dataclasses, which offer no runtime enforcement of types or values, Pydantic models parse and validate data upon initialization. This allows us to define "Validators"—functions decorated with @field\_validator or @model\_validator—that execute custom logic. In our context, these validators act as the "Code Checkers," inspecting user inputs (e.g., bar size) and automatically injecting missing data (e.g., hook length) according to ACI rules.16

The distinction between mode='before' and mode='after' validators is critical. A mode='before' validator runs on the raw input dictionary, allowing for data transformation before types are checked. A mode='after' validator runs on the fully instantiated model, ensuring that all fields are type-safe before complex inter-field logic (like comparing bar diameter to bend radius) is executed.18 For ACI rules, mode='after' is generally preferred as it ensures we are operating on valid BarSize enums rather than raw strings.

### **3.2. Implementation: The ACI Detailing Library**

The following Python implementation demonstrates a minimal, robust library for ACI 318 detailing. It utilizes Enum classes to restrict inputs to valid bar sizes and exposure categories, ensuring that invalid data (like a "No. 2.5 bar") is rejected immediately.

#### **3.2.1. Base Definitions and Enums**

We begin by defining the rigid vocabulary of the domain. The BarSize enum restricts inputs to ASTM standard sizes, and the ExposureClass enum captures the environmental conditions defined in Chapter 20\.

Python

from enum import Enum  
from typing import Optional, Literal  
from pydantic import BaseModel, Field, model\_validator, computed\_field

\# \--- Enums for Controlled Input \---

class BarSize(str, Enum):  
    NO\_3 \= "\#3"  
    NO\_4 \= "\#4"  
    NO\_5 \= "\#5"  
    NO\_6 \= "\#6"  
    NO\_7 \= "\#7"  
    NO\_8 \= "\#8"  
    NO\_9 \= "\#9"  
    NO\_10 \= "\#10"  
    NO\_11 \= "\#11"  
    NO\_14 \= "\#14"  
    NO\_18 \= "\#18"

class ExposureClass(str, Enum):  
    CAST\_AGAINST\_EARTH \= "cast\_against\_earth"  
    EXPOSED\_EARTH\_WEATHER \= "exposed\_earth\_weather"  
    INTERIOR\_BEAM\_COL \= "interior\_beam\_col"  
    INTERIOR\_SLAB\_WALL \= "interior\_slab\_wall"

\# \--- Helper Data (The "Database") \---  
\# Nominal diameters in inches per ASTM A615 / ACI 318 \[2\]  
BAR\_DIAMETERS \= {  
    BarSize.NO\_3: 0.375, BarSize.NO\_4: 0.500, BarSize.NO\_5: 0.625,  
    BarSize.NO\_6: 0.750, BarSize.NO\_7: 0.875, BarSize.NO\_8: 1.000,  
    BarSize.NO\_9: 1.128, BarSize.NO\_10: 1.270, BarSize.NO\_11: 1.410,  
    BarSize.NO\_14: 1.693, BarSize.NO\_18: 2.257  
} 

#### **3.2.2. The Structural Geometry Models**

The core logic is encapsulated in Pydantic models. The ACIGeometry base class uses a @computed\_field to derive the numerical diameter from the bar size automatically. This ensures the diameter is always synchronized with the bar size label.20

The StandardHook class implements the logic from Table 1\. The set\_aci\_defaults validator checks if the user provided a bend\_diameter. If it is None (missing), the validator queries the diameter, applies the conditional logic (e.g., if d\_b \<= 1.00), and populates the field. This pattern perfectly satisfies the requirement to "set defaults for missing values" while allowing manual overrides for special cases.

Python

\# \--- Pydantic Models \---

class ACIGeometry(BaseModel):  
    """  
    Base class for ACI 318 Geometric Rules.  
    Units are strictly in Inches for this implementation.  
    """  
    bar\_size: BarSize  
      
    @computed\_field  
    @property  
    def diameter(self) \-\> float:  
        """Automatically retrieves diameter from the lookup table based on bar\_size."""  
        return BAR\_DIAMETERS\[self.bar\_size\]

class StandardHook(ACIGeometry):  
    """  
    Defines a standard hook per ACI 318-19 Table 25.3.1.  
    Automatically calculates geometry if not provided.  
    """  
    angle: Literal  
    bend\_diameter: Optional\[float\] \= None  
    extension\_length: Optional\[float\] \= None

    @model\_validator(mode='after')  
    def set\_aci\_defaults(self) \-\> 'StandardHook':  
        d\_b \= self.diameter  
          
        \# 1\. Calculate Minimum Bend Diameter per ACI 318-19 Table 25.3.1   
        if self.bend\_diameter is None:  
            if d\_b \<= 1.00: \# \#3 through \#8  
                self.bend\_diameter \= 6 \* d\_b  
            elif d\_b \<= 1.41: \# \#9 through \#11  
                self.bend\_diameter \= 8 \* d\_b  
            else: \# \#14, \#18  
                self.bend\_diameter \= 10 \* d\_b  
          
        \# 2\. Calculate Minimum Extension per ACI 318-19 Table 25.3.1   
        if self.extension\_length is None:  
            if self.angle \== 90:  
                self.extension\_length \= 12 \* d\_b  
            elif self.angle \== 180:  
                \# Logic: Greater of 4db or 2.5 inches  
                self.extension\_length \= max(4 \* d\_b, 2.5)  
                  
        return self

class ConcreteCover(ACIGeometry):  
    """  
    Defines minimum concrete cover per ACI 318-19 Table 20.6.1.3.1.  
    """  
    exposure: ExposureClass  
    min\_cover: Optional\[float\] \= None  
      
    @model\_validator(mode='after')  
    def set\_cover\_defaults(self) \-\> 'ConcreteCover':  
        if self.min\_cover is not None:  
            return self  
              
        \# Logic derived from ACI 318-19 Table 20.6.1.3.1   
        if self.exposure \== ExposureClass.CAST\_AGAINST\_EARTH:  
            self.min\_cover \= 3.0  
        elif self.exposure \== ExposureClass.EXPOSED\_EARTH\_WEATHER:  
            \# Breakpoint is \#6 bar (0.75 in diameter)  
            if self.diameter \>= 0.75:   
                self.min\_cover \= 2.0  
            else:  
                self.min\_cover \= 1.5  
        elif self.exposure \== ExposureClass.INTERIOR\_BEAM\_COL:  
            self.min\_cover \= 1.5  
        elif self.exposure \== ExposureClass.INTERIOR\_SLAB\_WALL:  
            if self.diameter \<= 1.41: \# \#11 and smaller  
                 self.min\_cover \= 0.75  
            \# Note: Code has specific logic for \#14/\#18 in slabs not covered by simplified list  
              
        return self

This implementation provides a "correct-by-construction" methodology. A user cannot instantiate a StandardHook that is incomplete; the model will always self-heal to code-compliant values. This is essential for automating downstream BIM creation, where a missing parameter could cause a geometry generation failure in Revit.

## **4\. The "Headless" BIM Workflow: Speckle Architecture**

The second phase of the workflow addresses the challenge of "Headless BIM"—the ability to define, visualize, and manage structural data in a web environment without requiring a continuously running desktop CAD application (like Revit or Rhino). This leverages **Speckle**, an open-source data platform that decouples building data from the proprietary file formats that typically imprison it.

### **4.1. Decoupling Data from Geometry: The "Type" Concept**

In traditional BIM workflows, a "Family" or "Type" is an asset stored inside a .rvt or .rfa file. To use it, one must open Revit. In a Speckle-based workflow, we invert this relationship. We define the "Type" as a lightweight data schema in the cloud (or Python), which can be visualized independently and only "instantiated" into Revit when necessary.

To achieve this, we define a custom Speckle Base object. In the Speckle ecosystem, Base is the parent class for all transfer objects. It supports dynamic property assignment and nested serialization.22 We create a StructuralType class that inherits from Base but acts as a *definition container* rather than a physical instance.

Python

from specklepy.objects import Base

class StructuralType(Base):  
    """  
    Represents a Revit Family Type definition, not an instance.  
    This object holds the 'recipe' for creating the element.  
    """  
    family\_name: str  
    type\_name: str  
    category: str  
    parameters: dict \= {}   
    \# displayValue will hold the visualization geometry  
    \# detaching ensures geometry is stored separately for efficiency \[24\]  
    detach: set \= {"displayValue"} 

### **4.2. Synthetic Visualization Without a Source Model**

The user query highlights a specific constraint: visualizing these 2D/3D types in a web app *without* a source 3D model. Typically, Speckle objects sent from Revit come with meshes pre-generated by the Revit graphics engine. Since we are originating data in Python, we must generate this visualization geometry synthetically.

#### **4.2.1. Algorithmic Mesh Generation**

To make a "Concrete Column Type" visible in the Speckle Web Viewer, we must populate the displayValue property of our StructuralType object with a list of Speckle.Core.Models.Geometry.Mesh objects.22

Since we lack a geometry kernel like RhinoCommon in a pure Python script, we use simple mathematical generation. A rectangular column is essentially a box defined by 8 vertices and 12 triangles (faces).

Python

from specklepy.objects.geometry import Mesh, Point

def create\_column\_mesh(width: float, depth: float, height: float \= 1.0) \-\> Mesh:  
    """  
    Creates a simple generic mesh box for visualization.  
    Height is arbitrary (e.g., 1 unit) just to show the profile in the viewer.  
    """  
    \# Define 8 vertices of a box centered at 0,0  
    w, d, h \= width / 2, depth / 2, height  
    vertices \=  
      
    \# Define faces using Speckle's flat list format: \[n, v0, v1, v2,...\]  
    \# n=3 for triangles, n=4 for quads.  
    \# Here we use quads (n=4) for simplicity if the viewer supports it,   
    \# otherwise split into triangles (n=3).  
    faces \=  
      
    mesh \= Mesh(vertices=vertices, faces=faces)  
    mesh.units \= "m"   
    return mesh

By assigning my\_column\_type.displayValue \= \[create\_column\_mesh(0.5, 0.5)\], the object becomes immediately renderable in the Speckle web interface.22 This allows stakeholders to visually verify the "Type" (e.g., seeing that it is square vs. rectangular) without needing Revit.

#### **4.2.2. 2D Visualization with SVG**

For detailed rebar shapes, a 3D mesh might be illegible or overly complex. A 2D "Shop Drawing" view is often more valuable. We can generate this using Scalable Vector Graphics (SVG) libraries like svgwrite 26 or drawsvg.28

The workflow involves calculating the 2D coordinates of the rebar shape (using the Pydantic classes from Section 3\) and drawing them as SVG paths.

1. **Calculate Coordinates:** Use the StandardHook logic to determine the start and end points of the hook extensions relative to the main bar leg.  
2. **Draw with SVG:** Create a canvas, add a polyline or path element with the calculated points.  
3. **Embed in Speckle:** The resulting SVG string can be stored in a string field on the Speckle object (e.g., drawing\_svg) or uploaded as a binary Blob attachment. A custom web application can then simply render this string inside an HTML \<div\>, providing a pristine 2D schematic alongside the 3D metadata.26

### **4.3. Transmission and Versioning**

Once hydrated with ACI parameters and synthetic geometry, the objects are sent to a Speckle Stream. This utilizes the ServerTransport and operations.send methods. Crucially, one should explicitly create a **Commit** object referencing the sent data hash. This creates a permanent, versioned snapshot of the project's "Type Library".29 This "Type Library" stream acts as the single source of truth, accessible by both the web visualizer and the downstream Revit automation.

## **5\. Algorithmic Instantiation: Rhino.Inside.Revit**

The final leg of the workflow is the materialization of these abstract definitions into concrete BIM elements. Grasshopper, running directly within the Revit memory space via Rhino.Inside.Revit (RiR), acts as the orchestration engine for this process.

### **5.1. Receiving and Deconstructing Data**

The workflow begins with the **Speckle Receiver** component in Grasshopper. It connects to the "Type Library" stream created in Section 4\.

* **Expansion:** The received Base objects are deconstructed to reveal their properties: family\_name, width, ACI\_hook\_length, bar\_size, etc..30  
* **Separation:** It is critical to separate the visualization data from the construction data. The synthetic meshes generated in Python (Section 4.2.1) are for web viewing only; they are discarded in Grasshopper. We strictly use the *parameters* to drive the creation of native Revit elements.

### **5.2. The Type vs. Instance Dichotomy**

A common pitfall in Revit automation is confusing *Types* (FamilySymbols) with *Instances* (FamilyInstances). You cannot place a column until its Type exists in the document.

1. **Query and Check:** Use the RiR Query Types component to check if a Type with the name specified in the Speckle object (e.g., "Col 500x500") already exists in the active project.31  
2. **Creation (if missing):** If the Type does not exist, use the Duplicate Type component. This takes an existing valid Type (a template) and clones it, renaming it to the new specification.  
3. **Parameter Injection:** Once the Type exists, use the Element Parameter component to inject the specific values received from Speckle (e.g., Width, Depth, Fire Rating). This ensures the Revit Type matches the Python definition exactly.31

### **5.3. Advanced Rebar Instantiation**

Creating native rebar is significantly more complex than placing families due to the dependency on host elements and complex shape definitions.

* **The Add Rebar Component:** Newer versions of RiR (and community extensions) provide an Add Rebar component.32 This component typically requires:  
  * **Host:** The Revit element (Column/Beam) created in the previous step.  
  * **Curves:** The driving centerline curves for the rebar.  
  * **Type:** A reference to a RebarBarType (e.g., "\#6").  
  * **Shape:** A reference to a RebarShape (e.g., "M\_00").  
* **Curve Generation Strategy:** Instead of relying on Revit to figure out the geometry, we use the ACI rules from our Python definition to construct the exact driving curves in Grasshopper.  
  * We define a **Polyline** in Grasshopper that represents the bar's centerline.  
  * The vertices of this polyline are offset from the host element's faces by the **Cover** value (derived from our ConcreteCover class).  
  * The hooks are added as segments at the start/end of the polyline, with lengths determined by our StandardHook class logic ($12d\_b$, etc.).33  
* **Shape Mapping:** When this polyline is passed to the Add Rebar component, RiR attempts to match it to an existing Revit RebarShape. Providing a clean, code-compliant polyline ensures that Revit recognizes it as a standard shape (e.g., "Shape 11") rather than creating a messy "Rebar Shape 1" custom definition.34

### **5.4. Element Tracking and Idempotency**

A critical feature of Rhino.Inside.Revit is **Element Tracking**. When Grasshopper creates an element in Revit, it stores a persistent link (UUID) to that element. If the script is re-run (e.g., because the Speckle data was updated), RiR will *modify* the existing Revit element rather than creating a duplicate.36 This allows for an iterative workflow where the Python definitions can be updated, sent to Speckle, and the Revit model updates automatically upon re-running the Grasshopper definition, maintaining the integrity of the BIM database.

## **6\. Conclusion**

This report establishes a rigorous technical pathway for implementing "Headless BIM" workflows in structural engineering. By moving the **definition of logic** out of the proprietary BIM environment and into an agnostic Python/Pydantic environment, engineers gain the ability to enforce code compliance (ACI 318\) at the data level, ensuring that every piece of data created is valid by default.

The use of Pydantic validators effectively "bakes" expert engineering knowledge into the data structure itself, catching errors before they manifest in geometry. The Speckle architecture demonstrates that full 3D models are not required for rich communication; synthetic meshes and SVGs provide sufficient visual context for web-based collaboration. Finally, Rhino.Inside.Revit serves as the high-fidelity translator, converting these validated, open-format definitions into the specific, coordinated elements of a Revit project. This architecture not only reduces manual detailing errors but also lays the foundation for generative design and machine learning applications, where the generation of valid structural training data is a prerequisite for automation.

## **7\. Data Tables for Implementation**

**Table 2: Minimum Inside Bend Diameters (ACI 318-19 Table 25.3.2) for Implementation**

| Bar Size Range | Minimum Bend Diameter (D) | Application Context | Source |
| :---- | :---- | :---- | :---- |
| \#3 through \#5 | $4d\_b$ | Stirrups/Ties Only | 3 |
| \#3 through \#8 | $6d\_b$ | General (Non-Stirrup) | 2 |
| \#6 through \#8 | $6d\_b$ | Stirrups/Ties | 3 |
| \#9 through \#11 | $8d\_b$ | General | 2 |
| \#14, \#18 | $10d\_b$ | General | 2 |

**Table 3: Concrete Cover Defaults (ACI 318-19 Table 20.6.1.3.1) for Implementation**

| Exposure Condition | Member Type | Bar Size | Min. Cover | Source |
| :---- | :---- | :---- | :---- | :---- |
| Cast against earth | All | All | 3.0 in | 9 |
| Exposed to weather | All | \#6 \- \#18 | 2.0 in | 9 |
| Exposed to weather | All | \#3 \- \#5 | 1.5 in | 9 |
| Interior (Not exposed) | Beams/Columns | All | 1.5 in | 9 |
| Interior (Not exposed) | Slabs/Walls | \#11 and smaller | 0.75 in | 9 |

#### **Works cited**

1. DEVELOPMENT OF LARGE HIGH-STRENGTH REINFORCING BARS WITH STANDARD HOOKS AND HEADS \- ACI Foundation, accessed November 19, 2025, [https://www.acifoundation.org/portals/12/Files/PDFs/CRC-09\_LargeHighStrengthReinforcingBars.pdf](https://www.acifoundation.org/portals/12/Files/PDFs/CRC-09_LargeHighStrengthReinforcingBars.pdf)  
2. Standard Hook Details: in Accordance With ACI 318 Building Code | PDF \- Scribd, accessed November 19, 2025, [https://www.scribd.com/document/559763907/CRSI-Rebar-Information](https://www.scribd.com/document/559763907/CRSI-Rebar-Information)  
3. Standard Hooks, Seismic Hooks, Crossties, and Minimum Inside Bend Diameters per ACI 318-19 with ideCAD, accessed November 19, 2025, [https://help.idecad.com/ideCAD/standard-hooks-seismic-hooks-crossties-and-minimum](https://help.idecad.com/ideCAD/standard-hooks-seismic-hooks-crossties-and-minimum)  
4. ACI Quick Reference \- The Structural Toolbox, accessed November 19, 2025, [https://www.thestructuraltoolbox.com/concrete/aci\_reference](https://www.thestructuraltoolbox.com/concrete/aci_reference)  
5. Building Code Requirements for Structural Concrete (ACI 318-19) Commentary on Building Code Requirements for Structural Concre, accessed November 19, 2025, [https://mattia.ir/wp-content/uploads/2020/10/ACI-318R-19.pdf](https://mattia.ir/wp-content/uploads/2020/10/ACI-318R-19.pdf)  
6. Rebar Development Length Calculator to ACI 318 \- Structural Calc, accessed November 19, 2025, [https://structuralcalc.com/rebar-development-length-calculator-to-aci-318/](https://structuralcalc.com/rebar-development-length-calculator-to-aci-318/)  
7. standard hooks \- Connect NCDOT, accessed November 19, 2025, [https://connect.ncdot.gov/projects/construction/ConstManRefDocs/SECTION%20425%20BAR%20SUPPORTS.pdf](https://connect.ncdot.gov/projects/construction/ConstManRefDocs/SECTION%20425%20BAR%20SUPPORTS.pdf)  
8. Concrete cover \- Grokipedia, accessed November 19, 2025, [https://grokipedia.com/page/Concrete\_cover](https://grokipedia.com/page/Concrete_cover)  
9. Table 20.6.1.3.1-Specified concrete cover for | Chegg.com, accessed November 19, 2025, [https://www.chegg.com/homework-help/questions-and-answers/table-206131-specified-concrete-cover-cast-place-nonprestressed-concrete-members-specified-q35490742](https://www.chegg.com/homework-help/questions-and-answers/table-206131-specified-concrete-cover-cast-place-nonprestressed-concrete-members-specified-q35490742)  
10. US Concrete Cover Specifications \- iRebar, accessed November 19, 2025, [https://www.irebar.com/USConcreteCoverSpecifications.html](https://www.irebar.com/USConcreteCoverSpecifications.html)  
11. Epoxy-coated reinforcement and cover depth against ground \- American Concrete Institute, accessed November 19, 2025, [https://www.concrete.org/frequentlyaskedquestions.aspx?faqid=903](https://www.concrete.org/frequentlyaskedquestions.aspx?faqid=903)  
12. robbievanleeuwen/concrete-properties: Calculate section properties for reinforced concrete sections. \- GitHub, accessed November 19, 2025, [https://github.com/robbievanleeuwen/concrete-properties](https://github.com/robbievanleeuwen/concrete-properties)  
13. concreteproperties documentation, accessed November 19, 2025, [https://concrete-properties.readthedocs.io/](https://concrete-properties.readthedocs.io/)  
14. Does anybody have experience with a good python package for the design of concrete beams and columns to ACI 318? : r/StructuralEngineering \- Reddit, accessed November 19, 2025, [https://www.reddit.com/r/StructuralEngineering/comments/1ai9ocs/does\_anybody\_have\_experience\_with\_a\_good\_python/](https://www.reddit.com/r/StructuralEngineering/comments/1ai9ocs/does_anybody_have_experience_with_a_good_python/)  
15. Welcome to Pydantic \- Pydantic Validation, accessed November 19, 2025, [https://docs.pydantic.dev/latest/](https://docs.pydantic.dev/latest/)  
16. Pydantic and FastAPI Overview, accessed November 19, 2025, [https://medium.com/@toimrank/pydantic-and-fastapi-overview-9ac76bb82e42](https://medium.com/@toimrank/pydantic-and-fastapi-overview-9ac76bb82e42)  
17. Fields \- Pydantic Validation, accessed November 19, 2025, [https://docs.pydantic.dev/latest/concepts/fields/](https://docs.pydantic.dev/latest/concepts/fields/)  
18. Validators \- Pydantic Validation, accessed November 19, 2025, [https://docs.pydantic.dev/latest/concepts/validators/](https://docs.pydantic.dev/latest/concepts/validators/)  
19. Validators \- Pydantic, accessed November 19, 2025, [https://docs.pydantic.dev/2.7/concepts/validators/](https://docs.pydantic.dev/2.7/concepts/validators/)  
20. Fields \- Pydantic Validation, accessed November 19, 2025, [https://docs.pydantic.dev/latest/api/fields/](https://docs.pydantic.dev/latest/api/fields/)  
21. Pydantic: 10 Overlooked Features You Should Be Using | by Kasper Junge \- Medium, accessed November 19, 2025, [https://medium.com/@kasperjuunge/pydantic-10-overlooked-features-you-should-be-using-8f0bac05c60c](https://medium.com/@kasperjuunge/pydantic-10-overlooked-features-you-should-be-using-8f0bac05c60c)  
22. Working with Speckle Objects, accessed November 19, 2025, [https://docs.speckle.systems/developers/sdks/python/guides/how-to-work-with-objects](https://docs.speckle.systems/developers/sdks/python/guides/how-to-work-with-objects)  
23. Custom Kits (Obsolete) | Speckle Docs (Legacy), accessed November 19, 2025, [https://speckle.guide/dev/kits-dev.html](https://speckle.guide/dev/kits-dev.html)  
24. Generating a Surface from Scratch, specklePy \- Developers \- Speckle Community, accessed November 19, 2025, [https://speckle.community/t/generating-a-surface-from-scratch-specklepy/16225](https://speckle.community/t/generating-a-surface-from-scratch-specklepy/16225)  
25. SVG Vector Graphics in Python \- Jeff McBride, accessed November 19, 2025, [https://jeffmcbride.net/svg-vector-graphics-in-python/](https://jeffmcbride.net/svg-vector-graphics-in-python/)  
26. svgwrite \- PyPI, accessed November 19, 2025, [https://pypi.org/project/svgwrite/](https://pypi.org/project/svgwrite/)  
27. drawsvg · PyPI, accessed November 19, 2025, [https://pypi.org/project/drawsvg/](https://pypi.org/project/drawsvg/)  
28. Send Data to specific branch using specklepy \- Help (Legacy V2) \- Speckle Community, accessed November 19, 2025, [https://speckle.community/t/send-data-to-specific-branch-using-specklepy/3341](https://speckle.community/t/send-data-to-specific-branch-using-specklepy/3341)  
29. Complete guide to using Speckle in Grasshopper, accessed November 19, 2025, [https://speckle.systems/tutorials/complete-guide-to-using-speckle-in-grasshopper/](https://speckle.systems/tutorials/complete-guide-to-using-speckle-in-grasshopper/)  
30. Revit: Types & Families \- Rhino.Inside®.Revit, accessed November 19, 2025, [https://www.rhino3d.com/inside/revit/1.0/guides/revit-types](https://www.rhino3d.com/inside/revit/1.0/guides/revit-types)  
31. Automate Rebars In Revit with Rhino.Iniside.Revit \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=XddiE9RxTi4](https://www.youtube.com/watch?v=XddiE9RxTi4)  
32. Download the New Add Rebar Component for Rhino.Inside.Revit \- McNeel Forum, accessed November 19, 2025, [https://discourse.mcneel.com/t/download-the-new-add-rebar-component-for-rhino-inside-revit/208890](https://discourse.mcneel.com/t/download-the-new-add-rebar-component-for-rhino-inside-revit/208890)  
33. Rebars In Revit with Rhino.Inside.Revit | Solve Common Issue \- YouTube, accessed November 19, 2025, [https://www.youtube.com/watch?v=HzGs31-lB60](https://www.youtube.com/watch?v=HzGs31-lB60)  
34. Automated 3D rebar shop drawing generation utilizing Revit: a method to achieve double the work efficiency. \- Autodesk, accessed November 19, 2025, [https://static.au-uw2-prd.autodesk.com/CES2752\_Handout\_1727738434850001VctO.pdf](https://static.au-uw2-prd.autodesk.com/CES2752_Handout_1727738434850001VctO.pdf)  
35. Grasshopper in Revit \- Rhino.Inside®.Revit, accessed November 19, 2025, [https://www.rhino3d.com/inside/revit/1.0/guides/rir-grasshopper](https://www.rhino3d.com/inside/revit/1.0/guides/rir-grasshopper)