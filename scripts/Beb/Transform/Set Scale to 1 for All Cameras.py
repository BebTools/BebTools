import bpy

# Set scale of all camera objects to (1, 1, 1)
for obj in bpy.data.objects:
    if obj.type == 'CAMERA':
        obj.scale = (1.0, 1.0, 1.0)

print("All camera object scales set to (1, 1, 1)!")