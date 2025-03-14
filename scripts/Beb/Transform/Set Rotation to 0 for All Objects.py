import bpy
import mathutils

# Reset rotation of all mesh objects to (0, 0, 0)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.rotation_euler = (0.0, 0.0, 0.0)  # Reset Euler rotation
        # If using quaternion rotation, uncomment the next line instead
        # obj.rotation_quaternion = mathutils.Quaternion((1.0, 0.0, 0.0, 0.0))

print("All mesh object rotations set to (0, 0, 0)!")