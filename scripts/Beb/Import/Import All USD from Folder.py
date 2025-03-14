import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty

class BEBTOOLS_OT_ImportAllUSD(Operator):
    bl_idname = "bebtools.import_all_usd"
    bl_label = "Import All USD Files"
    bl_description = "Import all .usd files from a directory and its subfolders"

    # Property for the directory path
    directory: StringProperty(
        name="Directory",
        description="Path to the directory containing .usd files",
        subtype='DIR_PATH',
        default=""
    )

    def execute(self, context):
        """Import all .usd files from the selected directory and its subfolders."""
        if not self.directory:
            self.report({'ERROR'}, "No directory selected!")
            print("No directory selected!")
            return {'CANCELLED'}
        
        usd_files = []
        # Recursively walk through directory and subfolders
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.lower().endswith('.usd'):
                    usd_files.append(os.path.join(root, file))
        
        if not usd_files:
            self.report({'WARNING'}, f"No .usd files found in {self.directory} or its subfolders!")
            print(f"No .usd files found in {self.directory} or its subfolders!")
            return {'FINISHED'}
        
        # Import each .usd file
        for usd_file in usd_files:
            print(f"Importing: {usd_file}")
            try:
                bpy.ops.wm.usd_import(filepath=usd_file)  # Blender's USD importer
                print(f"Successfully imported: {usd_file}")
            except Exception as e:
                print(f"Error importing {usd_file}: {str(e)}")
        
        self.report({'INFO'}, f"Imported {len(usd_files)} .usd files from {self.directory}")
        print(f"Imported {len(usd_files)} .usd files from {self.directory} and subfolders!")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Open the file browser for directory selection."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Register the operator
bpy.utils.register_class(BEBTOOLS_OT_ImportAllUSD)

# Execute with file browser
bpy.ops.bebtools.import_all_usd('INVOKE_DEFAULT')