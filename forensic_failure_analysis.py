"""
Forensic Failure Analysis Script
ParaView Python Automation for Bridge Truss Fracture Investigation

Author: Peter Vocelka, Forensic Mechanical Engineer
Purpose: Automated failure analysis, yield detection, and debris tracking

Usage:
  pvpython forensic_failure_analysis.py
  OR in ParaView: Tools > Python Shell > Run Script
"""

try:
    from paraview.simple import *
except ImportError:
    print("ParaView modules not available - running standalone analysis")

import math
import os

# ============================================================================
# MATERIAL REFERENCE DATA
# ============================================================================

MATERIAL_A36 = {
    'name': 'Structural Steel A36',
    'yield_strength': 250,      # MPa
    'ultimate_strength': 400,   # MPa
    'E': 200000,                # MPa
    'fracture_toughness': 50,   # MPa√m
}

# Analysis thresholds
YIELD_THRESHOLD = MATERIAL_A36['yield_strength']
PLASTIC_THRESHOLD = 0.2  # % plastic strain indicating damage
TRIAXIALITY_CRITICAL = 0.33  # Critical triaxiality for void growth


def run_forensic_analysis_paraview():
    """
    Complete forensic failure analysis in ParaView.
    Implements all required workflows:
    1. Warp By Vector for micro-crack visualization
    2. Temporal Particles to Pathlines for debris tracking
    3. Annotate Selection for yield exceedance identification
    """
    
    print("="*65)
    print("FORENSIC MECHANICAL FAILURE ANALYSIS")
    print("Bridge Truss Progressive Fracture Investigation")
    print("="*65)
    
    # =========================================================================
    # LOAD TIME SERIES DATA
    # =========================================================================
    print("\n--- Loading Time Series Data ---")
    
    # Load structure time series
    structure_pvd = "bridge_truss_failure.pvd"
    if not os.path.exists(structure_pvd):
        structure_pvd = "../time-series-data/bridge_truss_failure.pvd"
    
    if not os.path.exists(structure_pvd):
        print(f"ERROR: Cannot find {structure_pvd}")
        print("Please ensure time series data is generated.")
        return
    
    structure = PVDReader(FileName=structure_pvd)
    RenameSource("Truss_Structure", structure)
    
    # Get time steps
    time_keeper = GetTimeKeeper()
    time_steps = structure.TimestepValues
    print(f"  Loaded structure data: {len(time_steps)} timesteps")
    print(f"  Time range: {time_steps[0]:.3f} to {time_steps[-1]:.3f} s")
    
    # Load debris particles
    debris_pvd = "debris_pathlines.pvd"
    if not os.path.exists(debris_pvd):
        debris_pvd = "../time-series-data/debris_pathlines.pvd"
    
    debris = PVDReader(FileName=debris_pvd)
    RenameSource("Debris_Particles", debris)
    print(f"  Loaded debris particle data")
    
    # =========================================================================
    # WORKFLOW 1: WARP BY VECTOR (Micro-Crack Visualization)
    # =========================================================================
    print("\n--- Workflow 1: Warp By Vector (Deformation Amplification) ---")
    
    # Apply warp filter with progressive scaling
    warp_scales = [10, 50, 100, 200]  # Different amplification factors
    
    for scale in warp_scales:
        warp = WarpByVector(Input=structure)
        warp.Vectors = ['POINTS', 'Displacement']
        warp.ScaleFactor = scale
        RenameSource(f"Warped_{scale}x", warp)
        UpdatePipeline(proxy=warp)
        
    print(f"  Created warped views: {warp_scales}")
    print("  Use 100-200x to visualize micro-cracks before macro-failure")
    
    # Create comparison layout
    print("  Setting up comparison layout...")
    
    # Split view
    layout = GetLayout()
    
    # =========================================================================
    # WORKFLOW 2: TEMPORAL PARTICLES TO PATHLINES (Debris Tracking)
    # =========================================================================
    print("\n--- Workflow 2: Temporal Particles To Pathlines ---")
    
    # Apply pathlines filter to debris
    pathlines = TemporalParticlesToPathlines(Input=debris)
    pathlines.MaskPoints = 1  # Sample rate
    pathlines.MaxTrackLength = 100  # Maximum path length
    pathlines.IdChannelArray = 'ParticleID'
    RenameSource("Debris_Pathlines", pathlines)
    UpdatePipeline(proxy=pathlines)
    
    print("  Created debris pathlines")
    print("  Color by 'Velocity' magnitude to show ejection speed")
    
    # Calculate pathline statistics
    pathline_data = servermanager.Fetch(pathlines)
    n_pathlines = pathline_data.GetNumberOfCells() if pathline_data else 0
    print(f"  Total pathlines generated: {n_pathlines}")
    
    # =========================================================================
    # WORKFLOW 3: FIND YIELD EXCEEDANCE (Selection + Annotation)
    # =========================================================================
    print("\n--- Workflow 3: Yield Strength Exceedance Detection ---")
    
    yield_results = {
        'first_timestep': None,
        'first_time': None,
        'first_node': None,
        'first_location': None,
        'first_stress': None,
        'total_yielded_nodes': {}
    }
    
    # Iterate through timesteps to find first yield exceedance
    for t_idx, t_val in enumerate(time_steps):
        # Set current time
        time_keeper.Time = t_val
        UpdatePipeline(proxy=structure)
        
        # Threshold for yield exceedance
        yield_threshold = Threshold(Input=structure)
        yield_threshold.Scalars = ['POINTS', 'yield_ratio']
        yield_threshold.LowerThreshold = 1.0
        yield_threshold.UpperThreshold = 100.0
        yield_threshold.ThresholdMethod = 'Between'
        
        UpdatePipeline(proxy=yield_threshold)
        
        # Get yielded points
        yielded_data = servermanager.Fetch(yield_threshold)
        n_yielded = yielded_data.GetNumberOfPoints() if yielded_data else 0
        
        yield_results['total_yielded_nodes'][t_val] = n_yielded
        
        if n_yielded > 0 and yield_results['first_timestep'] is None:
            yield_results['first_timestep'] = t_idx
            yield_results['first_time'] = t_val
            
            # Get first point data
            if yielded_data.GetNumberOfPoints() > 0:
                point = yielded_data.GetPoint(0)
                yield_results['first_location'] = point
                
                # Get stress at this point
                stress_array = yielded_data.GetPointData().GetArray('von_mises_stress')
                if stress_array:
                    yield_results['first_stress'] = stress_array.GetValue(0)
                
                # Get node ID
                yield_results['first_node'] = 0  # First yielded node
        
        Delete(yield_threshold)
    
    # Report findings
    print(f"\n  YIELD EXCEEDANCE REPORT:")
    print(f"  Material: {MATERIAL_A36['name']}")
    print(f"  Yield Strength: {MATERIAL_A36['yield_strength']} MPa")
    
    if yield_results['first_timestep'] is not None:
        print(f"\n  ⚠ FIRST YIELD DETECTED:")
        print(f"     Timestep: {yield_results['first_timestep']}")
        print(f"     Time: {yield_results['first_time']:.4f} s")
        if yield_results['first_location']:
            loc = yield_results['first_location']
            print(f"     Location: ({loc[0]:.2f}, {loc[1]:.2f}, {loc[2]:.2f}) mm")
        if yield_results['first_stress']:
            print(f"     Stress: {yield_results['first_stress']:.1f} MPa")
            print(f"     Overstress Ratio: {yield_results['first_stress']/YIELD_THRESHOLD:.2f}x")
    
    print(f"\n  Yielded nodes progression:")
    for t, n in sorted(yield_results['total_yielded_nodes'].items()):
        if n > 0:
            print(f"     t = {t:.3f} s: {n:,} nodes")
    
    # =========================================================================
    # CREATE SELECTION ANNOTATION
    # =========================================================================
    print("\n--- Creating Failure Location Annotation ---")
    
    # Go to failure timestep
    if yield_results['first_timestep'] is not None:
        time_keeper.Time = yield_results['first_time']
        UpdatePipeline(proxy=structure)
        
        # Create text annotation
        text = Text()
        text.Text = f"YIELD EXCEEDANCE DETECTED\n"
        text.Text += f"Time: {yield_results['first_time']:.3f} s\n"
        if yield_results['first_location']:
            loc = yield_results['first_location']
            text.Text += f"Location: ({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f}) mm\n"
        if yield_results['first_stress']:
            text.Text += f"Stress: {yield_results['first_stress']:.0f} MPa"
        
        RenameSource("Failure_Annotation", text)
        
        # Display annotation
        text_display = Show(text)
        text_display.FontSize = 14
        
        print("  Created failure location annotation")
    
    # =========================================================================
    # CRACK DAMAGE VISUALIZATION
    # =========================================================================
    print("\n--- Crack Damage Zone Analysis ---")
    
    # Go to final timestep
    time_keeper.Time = time_steps[-1]
    UpdatePipeline(proxy=structure)
    
    # Threshold for damaged material
    damage_threshold = Threshold(Input=structure)
    damage_threshold.Scalars = ['POINTS', 'crack_damage']
    damage_threshold.LowerThreshold = 0.1
    damage_threshold.UpperThreshold = 1.0
    damage_threshold.ThresholdMethod = 'Between'
    
    RenameSource("Crack_Damage_Zone", damage_threshold)
    UpdatePipeline(proxy=damage_threshold)
    
    damage_data = servermanager.Fetch(damage_threshold)
    n_damaged = damage_data.GetNumberOfPoints() if damage_data else 0
    print(f"  Damaged nodes at final timestep: {n_damaged:,}")
    
    # =========================================================================
    # PLASTIC STRAIN VISUALIZATION
    # =========================================================================
    print("\n--- Plastic Strain Analysis ---")
    
    plastic_threshold = Threshold(Input=structure)
    plastic_threshold.Scalars = ['POINTS', 'plastic_strain']
    plastic_threshold.LowerThreshold = PLASTIC_THRESHOLD
    plastic_threshold.UpperThreshold = 100.0
    plastic_threshold.ThresholdMethod = 'Between'
    
    RenameSource("Plastic_Zone", plastic_threshold)
    UpdatePipeline(proxy=plastic_threshold)
    
    plastic_data = servermanager.Fetch(plastic_threshold)
    n_plastic = plastic_data.GetNumberOfPoints() if plastic_data else 0
    print(f"  Plastically deformed nodes: {n_plastic:,}")
    
    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    print("\n" + "="*65)
    print("FORENSIC ANALYSIS SUMMARY")
    print("="*65)
    
    print("\n1. DEFORMATION VISUALIZATION:")
    print(f"   Warp filters created: {len(warp_scales)} scales")
    print("   Recommended: Use 100x warp to identify micro-cracks")
    
    print("\n2. DEBRIS TRAJECTORY:")
    print(f"   Pathlines generated: {n_pathlines}")
    print("   Track particle ejection from fracture surface")
    
    print("\n3. FAILURE INITIATION:")
    if yield_results['first_time']:
        print(f"   First yield at t = {yield_results['first_time']:.3f} s")
        print(f"   Critical location identified and annotated")
    
    print("\n4. DAMAGE EXTENT:")
    print(f"   Crack damage zone: {n_damaged:,} nodes")
    print(f"   Plastic deformation zone: {n_plastic:,} nodes")
    
    print("\nForensic investigation complete. Review visualizations for root cause.")


def standalone_analysis():
    """
    Standalone analysis without ParaView.
    Parses VTK files to identify yield exceedance.
    """
    print("="*65)
    print("STANDALONE FORENSIC ANALYSIS")
    print("="*65)
    
    # Find VTK files
    vtk_dir = "."
    if not os.path.exists("truss_failure_0000.vtk"):
        vtk_dir = "../time-series-data"
    
    if not os.path.exists(os.path.join(vtk_dir, "truss_failure_0000.vtk")):
        print("VTK files not found. Generate time series data first.")
        return
    
    print(f"\nAnalyzing files in: {vtk_dir}")
    print(f"Material: Structural Steel A36")
    print(f"Yield Strength: {YIELD_THRESHOLD} MPa\n")
    
    first_yield_timestep = None
    first_yield_node = None
    first_yield_location = None
    first_yield_stress = None
    
    # Analyze each timestep
    for t_idx in range(12):  # 12 timesteps
        filename = os.path.join(vtk_dir, f"truss_failure_{t_idx:04d}.vtk")
        if not os.path.exists(filename):
            continue
        
        # Parse VTK file
        yield_ratios = []
        stresses = []
        coords = []
        
        reading_yield = False
        reading_stress = False
        reading_points = False
        point_count = 0
        
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                
                if "SCALARS yield_ratio" in line:
                    reading_yield = True
                    reading_stress = False
                    continue
                elif "SCALARS von_mises_stress" in line:
                    reading_stress = True
                    reading_yield = False
                    continue
                elif line.startswith("SCALARS") or line.startswith("VECTORS"):
                    reading_yield = False
                    reading_stress = False
                    continue
                elif line.startswith("LOOKUP_TABLE"):
                    continue
                
                try:
                    val = float(line)
                    if reading_yield:
                        yield_ratios.append(val)
                    elif reading_stress:
                        stresses.append(val)
                except ValueError:
                    pass
        
        # Count yielded nodes
        n_yielded = sum(1 for yr in yield_ratios if yr > 1.0)
        
        if n_yielded > 0:
            print(f"  Timestep {t_idx}: {n_yielded:,} nodes exceeded yield")
            
            if first_yield_timestep is None:
                first_yield_timestep = t_idx
                # Find first yielded node
                for i, yr in enumerate(yield_ratios):
                    if yr > 1.0:
                        first_yield_node = i
                        if i < len(stresses):
                            first_yield_stress = stresses[i]
                        break
    
    print(f"\n" + "-"*40)
    print("YIELD EXCEEDANCE SUMMARY")
    print("-"*40)
    
    if first_yield_timestep is not None:
        print(f"First yield exceeded at timestep: {first_yield_timestep}")
        print(f"Node index: {first_yield_node}")
        if first_yield_stress:
            print(f"Stress at failure initiation: {first_yield_stress:.1f} MPa")
            print(f"Overstress ratio: {first_yield_stress/YIELD_THRESHOLD:.2f}x yield")
    else:
        print("No yield exceedance detected in available data.")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        from paraview.simple import GetActiveSource
        run_forensic_analysis_paraview()
    except ImportError:
        standalone_analysis()
