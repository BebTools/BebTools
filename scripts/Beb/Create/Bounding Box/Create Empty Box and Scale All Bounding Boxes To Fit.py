import bpy
import mathutils

def scale_empty_cubes_to_bbox():
    # Step 1: Add or find BBox_Scaler empty cube
    bbox_scaler = None
    for obj in bpy.data.objects:
        if obj.name == "BBox_Scaler" and obj.type == 'EMPTY' and obj.empty_display_type == 'CUBE':
            bbox_scaler = obj
            print(f"Found existing BBox_Scaler: {bbox_scaler.name}")
            break
    
    if not bbox_scaler:
        bpy.ops.object.empty_add(type='CUBE', location=(0, 0, 0))
        bbox_scaler = bpy.context.object
        bbox_scaler.name = "BBox_Scaler"
        print(f"Created new BBox_Scaler: {bbox_scaler.name}")
    
    # Step 2: Find all other empty cubes and scale them
    empty_cubes = [obj for obj in bpy.data.objects 
                   if obj.type == 'EMPTY' and obj.empty_display_type == 'CUBE' and obj != bbox_scaler]
    
    if not empty_cubes:
        print("No other empty cubes found to scale!")
        return
    
    # Get BBox_Scaler’s scale (reference bounds)
    bbox_scale = mathutils.Vector(bbox_scaler.scale)
    print(f"BBox_Scaler scale: {bbox_scale}")
    
    # Scale each empty cube to fit within BBox_Scaler
    for cube in empty_cubes:
        original_scale = mathutils.Vector(cube.scale)
        print(f"Processing {cube.name} with original scale: {original_scale}")
        
        # Calculate scaling factors for each axis to fit within BBox_Scaler
        scale_factors = [
            bbox_scale.x / original_scale.x if original_scale.x != 0 else float('inf'),
            bbox_scale.y / original_scale.y if original_scale.y != 0 else float('inf'),
            bbox_scale.z / original_scale.z if original_scale.z != 0 else float('inf')
        ]
        
        # Use the smallest factor to maintain aspect ratio and fit inside
        scale_factor = min(scale_factors)
        if scale_factor == float('inf'):
            print(f"Skipping {cube.name}: zero scale detected!")
            continue
        
        # Apply the uniform scale
        cube.scale = original_scale * scale_factor
        print(f"Scaled {cube.name} to: {cube.scale}")
    
    # Step 3: Parent all scaled empty cubes to BBox_Scaler
    for cube in empty_cubes:
        if cube.scale != (0, 0, 0):  # Only parent if it was scaled (non-zero)
            cube.parent = bbox_scaler
            print(f"Parented {cube.name} to BBox_Scaler")
    
    print("All empty cubes scaled and parented to BBox_Scaler!")

# Run the function
scale_empty_cubes_to_bbox()