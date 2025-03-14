import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty

class BEBTOOLS_OT_ImportAllGLTF(Operator):
    bl_idname = "bebtools.import_all_gltf"
    bl_label = "Import All GLTF Files"
    bl_description = "Import all .gltf files from a directory and its subfolders"

    # Property for the directory path
    directory: StringProperty(
        name="Directory",
        description="Path to the directory containing .gltf files",
        subtype='DIR_PATH',
        default=""
    )

    def execute(self, context):
        """Import all .gltf files from the selected directory and its subfolders."""
        if not self.directory:
            self.report({'ERROR'}, "No directory selected!")
            print("No directory selected!")
            return {'CANCELLED'}
        
        gltf_files = []
        # Recursively walk through directory and subfolders
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.lower().endswith('.gltf'):
                    gltf_files.append(os.path.join(root, file))
        
        if not gltf_files:
            self.report({'WARNING'}, f"No .gltf files found in {self.directory} or its subfolders!")
            print(f"No .gltf files found in {self.directory} or its subfolders!")
            return {'FINISHED'}
        
        # Import each .gltf file
        for gltf_file in gltf_files:
            print(f"Importing: {gltf_file}")
            try:
                bpy.ops.import_scene.gltf(filepath=gltf_file)
                print(f"Successfully imported: {gltf_file}")
            except Exception as e:
                print(f"Error importing {gltf_file}: {str(e)}")
        
        self.report({'INFO'}, f"Imported {len(gltf_files)} .gltf files from {self.directory}")
        print(f"Imported {len(gltf_files)} .gltf files from {self.directory} and subfolders!")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Open the file browser for directory selection."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Register the operator (runs when script is loaded by Beb.Tools)
bpy.utils.register_class(BEBTOOLS_OT_ImportAllGLTF)

# When called from Beb.Tools "Apply", this executes the operator
bpy.ops.bebtools.import_all_gltf('INVOKE_DEFAULT')