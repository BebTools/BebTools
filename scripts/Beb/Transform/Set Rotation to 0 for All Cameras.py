import bpy

# Reset rotation of all camera objects to (0, 0, 0)
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        obj.rotation_euler = (0.0, 0.0, 0.0)

print("All camera object rotations set to (0, 0, 0)!")