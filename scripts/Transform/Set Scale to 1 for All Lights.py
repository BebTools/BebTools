import bpy

# Set scale of all light objects to (1, 1, 1)
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        obj.scale = (1.0, 1.0, 1.0)

print("All light object scales set to (1, 1, 1)!")