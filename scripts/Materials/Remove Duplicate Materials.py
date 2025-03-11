import bpy
import re

def deduplicate_materials_and_images():
    # Step 1: Deduplicate materials
    material_map = {}  # Maps primary material name to its datablock
    materials_to_delete = set()  # Tracks duplicate materials to remove
    
    # Build a map of primary materials and identify duplicates
    for mat in bpy.data.materials:
        if not mat or not mat.name:
            continue
        # Check if the material name ends with .XXX (e.g., .001, .893)
        match = re.match(r"^(.*?)\.\d{3}$", mat.name)
        if match:
            primary_name = match.group(1)
            if primary_name in bpy.data.materials:
                material_map.setdefault(primary_name, bpy.data.materials[primary_name])
                materials_to_delete.add(mat)
            else:
                # If primary doesn’t exist, treat this as primary
                material_map[mat.name] = mat
        else:
            material_map[mat.name] = mat
    
    # Reassign materials on objects
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or not obj.material_slots:
            continue
        for slot in obj.material_slots:
            if not slot.material:
                continue
            match = re.match(r"^(.*?)\.\d{3}$", slot.material.name)
            if match:
                primary_name = match.group(1)
                if primary_name in material_map:
                    print(f"Reassigning {obj.name} from {slot.material.name} to {primary_name}")
                    slot.material = material_map[primary_name]
    
    # Delete duplicate materials
    for mat in materials_to_delete:
        print(f"Deleting duplicate material: {mat.name}")
        bpy.data.materials.remove(mat)

    # Step 2: Deduplicate images in material node trees
    image_map = {}  # Maps primary image name to its datablock
    images_to_delete = set()  # Tracks duplicate images to remove
    
    # Build a map of primary images and identify duplicates
    for img in bpy.data.images:
        if not img or not img.name:
            continue
        # Check if the image name ends with .XXX (e.g., .001, .023)
        match = re.match(r"^(.*?)\.\d{3}$", img.name)
        if match:
            primary_name = match.group(1)
            if primary_name in bpy.data.images:
                image_map.setdefault(primary_name, bpy.data.images[primary_name])
                images_to_delete.add(img)
            else:
                # If primary doesn’t exist, treat this as primary
                image_map[img.name] = img
        else:
            image_map[img.name] = img
    
    # Reassign images in material node trees
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    match = re.match(r"^(.*?)\.\d{3}$", node.image.name)
                    if match:
                        primary_name = match.group(1)
                        if primary_name in image_map:
                            print(f"Reassigning image in {mat.name} from {node.image.name} to {primary_name}")
                            node.image = image_map[primary_name]
    
    # Delete duplicate images
    for img in images_to_delete:
        print(f"Deleting duplicate image: {img.name}")
        bpy.data.images.remove(img)

    print("Material and image deduplication complete!")

# Run the function
deduplicate_materials_and_images()