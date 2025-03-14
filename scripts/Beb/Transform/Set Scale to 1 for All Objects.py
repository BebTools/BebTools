import bpy

# Set scale of all mesh objects to (1, 1, 1)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.scale = (1.0, 1.0, 1.0)

print("All mesh object scales set to (1, 1, 1)!")