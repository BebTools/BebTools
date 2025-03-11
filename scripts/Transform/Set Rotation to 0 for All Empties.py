import bpy

# Reset rotation of all empty objects to (0, 0, 0)
for obj in bpy.data.objects:
    if obj.type == 'EMPTY':
        obj.rotation_euler = (0.0, 0.0, 0.0)

print("All empty object rotations set to (0, 0, 0)!")