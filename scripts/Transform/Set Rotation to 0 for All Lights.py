import bpy

# Reset rotation of all light objects to (0, 0, 0)
for obj in bpy.data.objects:
    if obj.type == 'LIGHT':
        obj.rotation_euler = (0.0, 0.0, 0.0)

print("All light object rotations set to (0, 0, 0)!")