# Technical Standard Operating Procedure (SOP)
## Forensic Mechanical Failure Analysis - Bridge Truss Fracture Investigation

**Document Number:** SOP-FME-FA-001  
**Version:** 1.0  
**Effective Date:** December 2025  
**Author:** Peter Vocelka, Forensic Mechanical Engineer  
**Classification:** Technical Investigation Protocol

---

## 1. Purpose and Scope

This SOP establishes procedures for forensic post-processing of FEA simulations depicting progressive structural failure. The workflow enables investigators to:

- **Identify failure initiation** using temporal analysis
- **Visualize micro-cracks** before macro-failure through deformation amplification
- **Track debris trajectories** from fracture surfaces
- **Document yield exceedance** with precise timestep and node identification

### 1.1 Applicable Standards

- ASTM E1820: Standard Test Method for Measurement of Fracture Toughness
- ASTM E399: Linear-Elastic Plane-Strain Fracture Toughness
- ASME BPVC Section XI: Rules for Inservice Inspection

---

## 2. Input Data Requirements

### 2.1 Time Series Dataset

| File | Description |
|------|-------------|
| `bridge_truss_failure.pvd` | Structure time series (12 timesteps) |
| `debris_pathlines.pvd` | Debris particle time series |
| `truss_failure_XXXX.vtk` | Individual timestep files |
| `debris_particles_XXXX.vtk` | Particle files per timestep |

### 2.2 Material Reference Data

| Property | Value | Standard |
|----------|-------|----------|
| Material | Structural Steel A36 | ASTM A36 |
| Yield Strength (σy) | 250 MPa | Minimum |
| Ultimate Strength (σu) | 400 MPa | Minimum |
| Young's Modulus (E) | 200 GPa | Typical |
| Fracture Toughness (KIC) | 50 MPa√m | Typical |

### 2.3 Simulation Parameters

- **Grid Resolution:** 60 × 30 × 50 (90,000 nodes)
- **Timesteps:** 12 (t = 0.0 to 2.2 seconds)
- **Peak Load:** 420 kN (2.8× design capacity)
- **Failure Mode:** Fatigue crack propagation → unstable fracture

---

## 3. Procedure 1: Loading Time Series Data

### 3.1 Open PVD File

```
File > Open > bridge_truss_failure.pvd
```

### 3.2 Verify Time Steps

1. Check Animation toolbar shows correct range
2. Confirm timestep count: **12 steps**
3. Note time range: **0.0 - 2.2 seconds**

### 3.3 Load Debris Data

```
File > Open > debris_pathlines.pvd
```

Debris appears after timestep 6 (t > 1.2 s) when material begins ejecting.

---

## 4. Procedure 2: Warp By Vector (Deformation Amplification)

### 4.1 Objective
Amplify displacements to visualize micro-cracks and strain localization that would be invisible at 1:1 scale.

### 4.2 Steps

1. **Select the structure source** in Pipeline Browser

2. **Apply Warp By Vector:**
   ```
   Filters > Alphabetical > Warp By Vector
   ```

3. **Configure filter:**
   - Vectors: `Displacement`
   - Scale Factor: Start with **100**

4. **Click Apply**

### 4.3 Scale Factor Guidelines

| Scale Factor | Application |
|--------------|-------------|
| 10× | View overall deflection pattern |
| 50× | Identify strain concentration zones |
| 100× | **Recommended** - Visualize micro-cracks |
| 200× | Detailed crack tip investigation |
| 500× | Extreme amplification for subtle features |

### 4.4 Interpretation

- **Localized bulging:** Indicates stress concentration
- **Surface discontinuities:** Crack initiation sites
- **Asymmetric deformation:** Identifies failure plane orientation
- **Gap opening:** Crack mouth opening displacement (CMOD)

### 4.5 Time Animation

1. Set Scale Factor to 100×
2. Play animation (▶ button)
3. Watch for sudden deformation changes indicating crack growth
4. Note timestep where visible crack appears

---

## 5. Procedure 3: Temporal Particles To Pathlines (Debris Tracking)

### 5.1 Objective
Trace debris trajectories to understand failure energy release and fragment dispersion.

### 5.2 Steps

1. **Select debris particle source**

2. **Apply Temporal Particles To Pathlines:**
   ```
   Filters > Temporal > Temporal Particles To Pathlines
   ```

3. **Configure filter:**
   - Mask Points: **1** (use all particles)
   - Max Track Length: **100** (mm)
   - ID Channel Array: `ParticleID`

4. **Click Apply**

### 5.3 Visualization Settings

1. **Color by Velocity magnitude:**
   - Shows ejection energy
   - High velocity = high strain energy release

2. **Tube filter for visibility:**
   ```
   Filters > Tube
   Radius: 0.5 mm
   ```

3. **Enable time labels:**
   - Shows particle position at each timestep

### 5.4 Forensic Interpretation

| Observation | Significance |
|-------------|--------------|
| High initial velocity | Brittle fracture (rapid energy release) |
| Multiple origins | Multiple crack fronts |
| Directional ejection | Indicates crack propagation direction |
| Wide dispersion | High stored elastic energy |

---

## 6. Procedure 4: Yield Exceedance Detection (Selection + Annotation)

### 6.1 Objective
Identify the exact timestep and node where yield strength was first exceeded - critical for establishing failure sequence.

### 6.2 Method A: Threshold Filter Approach

1. **Select structure source**

2. **Apply Threshold:**
   ```
   Filters > Alphabetical > Threshold
   ```

3. **Configure:**
   - Scalars: `yield_ratio`
   - Lower Threshold: **1.0**
   - Upper Threshold: **100**
   - Method: Between

4. **Iterate through timesteps:**
   - Start at t = 0
   - Advance until threshold shows non-empty result
   - Record first timestep with yielded material

### 6.3 Method B: Python Script Approach

```python
# In ParaView Python Shell
source = GetActiveSource()
time_keeper = GetTimeKeeper()

for t in source.TimestepValues:
    time_keeper.Time = t
    UpdatePipeline()
    
    threshold = Threshold(Input=source)
    threshold.Scalars = ['POINTS', 'yield_ratio']
    threshold.LowerThreshold = 1.0
    threshold.UpperThreshold = 100
    
    UpdatePipeline(proxy=threshold)
    
    data = servermanager.Fetch(threshold)
    if data.GetNumberOfPoints() > 0:
        print(f"First yield at t = {t:.4f} s")
        print(f"Number of yielded nodes: {data.GetNumberOfPoints()}")
        break
    
    Delete(threshold)
```

### 6.4 Selection Display Inspector

1. **Open Selection Display Inspector:**
   ```
   View > Selection Display Inspector
   ```

2. **Enable point labels:**
   - Check "Point Labels"
   - Array: `von_mises_stress`
   - Format: `%.1f MPa`

3. **Select critical points:**
   - Use "Select Points On" tool (S key)
   - Click on highest stress region

4. **Record information:**
   - Node ID (from Selection Inspector)
   - Coordinates (from Information panel)
   - Stress value

### 6.5 Creating Annotation

1. **Add text annotation:**
   ```
   Sources > Text
   ```

2. **Enter failure details:**
   ```
   YIELD EXCEEDANCE DETECTED
   Time: [timestep value] s
   Location: (x, y, z) mm
   Stress: [value] MPa
   ```

3. **Position annotation** near failure location

---

## 7. Procedure 5: Cross-Sectional Failure Analysis

### 7.1 Objective
Examine internal stress state through the crack plane.

### 7.2 Creating Slice Through Crack

1. **Select warped structure (100×)**

2. **Apply Slice:**
   ```
   Filters > Slice
   ```

3. **Position slice at crack origin:**
   - Origin: (25, -15, 0) mm
   - Normal: (0, 0, 1) for XY plane

### 7.3 Stress Field Visualization

Color the slice by:
- `von_mises_stress`: Overall stress state
- `triaxiality`: Constraint indicator
- `plastic_strain`: Yielded zone extent

### 7.4 Stress Intensity Estimation

For through-crack:
```
K_I = σ × √(π × a) × Y
```

Where:
- σ = Remote stress (from model)
- a = Crack length (measure from warped view)
- Y = Geometry factor (≈1.12 for edge crack)

---

## 8. Procedure 6: Generating Forensic Report

### 8.1 Required Screenshots

| Image | Description |
|-------|-------------|
| 1 | Undeformed structure with stress contour |
| 2 | Warped view (100×) showing crack |
| 3 | Debris pathlines colored by velocity |
| 4 | Time sequence of crack growth (4-6 frames) |
| 5 | Cross-section through failure plane |
| 6 | Selection annotation at yield initiation |

### 8.2 Data Export

1. **Export statistics:**
   ```
   File > Save Data > CSV
   ```

2. **Include arrays:**
   - von_mises_stress
   - yield_ratio
   - plastic_strain
   - coordinates

### 8.3 Report Contents

1. Executive Summary
2. Material and Loading Description
3. Failure Sequence Timeline
4. Yield Initiation Analysis
5. Crack Growth Characterization
6. Debris Trajectory Analysis
7. Root Cause Determination
8. Recommendations

---

## 9. Quality Assurance

### 9.1 Verification Checklist

- [ ] Time series loads completely (12 timesteps)
- [ ] Debris particles appear after expected time
- [ ] Warp displacement direction is correct
- [ ] Yield threshold identifies correct nodes
- [ ] Pathlines trace from fracture surface
- [ ] Annotations are accurate

### 9.2 Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| No particles shown | Wrong time range | Advance to t > 1.2 s |
| Warp looks wrong | Wrong vector array | Verify `Displacement` selected |
| Threshold empty | Wrong scalar range | Check yield_ratio values |
| Pathlines fragmented | Missing particle IDs | Verify ParticleID array |

---

## 10. References

1. Anderson, T.L. (2017). Fracture Mechanics: Fundamentals and Applications
2. Paris, P.C. & Erdogan, F. (1963). J. Basic Engineering, 85:528
3. ParaView Documentation: https://docs.paraview.org/

---

**Document Control:**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | P. Vocelka | Initial release |

---

*© 2025 Peter Vocelka. Licensed under MIT License.*
