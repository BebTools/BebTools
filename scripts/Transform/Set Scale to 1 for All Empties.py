import bpy

# Set scale of all empty objects to (1, 1, 1)
for obj in bpy.data.objects:
    if obj.type == 'EMPTY':
        obj.scale = (1.0, 1.0, 1.0)

print("All empty object scales set to (1, 1, 1)!")