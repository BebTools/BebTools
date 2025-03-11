import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty

class BEBTOOLS_OT_RenderCollections(Operator):
    bl_idname = "bebtools.render_collections"
    bl_label = "Render Collections"
    bl_description = "Render each collection individually with the active camera"

    # Properties for file browser
    directory: StringProperty(
        name="Output Directory",
        description="Directory to save rendered images",
        subtype='DIR_PATH',
        default=""
    )
    transparent: BoolProperty(
        name="Transparent Background",
        description="Render with a transparent background",
        default=False
    )
    file_format: EnumProperty(
        name="File Format",
        description="Format for rendered images",
        items=[
            ('PNG', "PNG", "Portable Network Graphics"),
            ('JPEG', "JPEG", "Joint Photographic Experts Group"),
            ('BMP', "BMP", "Bitmap"),
            ('TIFF', "TIFF", "Tagged Image File Format"),
        ],
        default='PNG'
    )

    def execute(self, context):
        if not self.directory:
            self.report({'ERROR'}, "No output directory selected!")
            print("No output directory selected!")
            return {'CANCELLED'}
        
        # Get the active camera
        camera = context.scene.camera
        if not camera:
            self.report({'ERROR'}, "No active camera found in the scene!")
            print("No active camera found in the scene!")
            return {'CANCELLED'}
        
        # Get all collections (exclude Scene Collection)
        collections = [coll for coll in bpy.data.collections if coll != context.scene.collection]
        if not collections:
            self.report({'WARNING'}, "No collections found to render!")
            print("No collections found to render!")
            return {'FINISHED'}
        
        # Store original visibility states
        original_visibility = {coll: not coll.hide_render for coll in collections}
        
        # Set render settings
        render = context.scene.render
        original_transparent = render.film_transparent
        original_format = render.image_settings.file_format
        render.film_transparent = self.transparent
        render.image_settings.file_format = self.file_format
        
        # Hide all collections initially
        for coll in collections:
            coll.hide_render = True
        
        # Render each collection
        for coll in collections:
            print(f"Rendering collection: {coll.name}")
            coll.hide_render = False  # Unhide the current collection
            
            # Set output path with collection name
            output_path = os.path.join(self.directory, f"{coll.name}")
            render.filepath = output_path
            
            # Render the scene
            try:
                bpy.ops.render.render(write_still=True)
                print(f"Rendered {coll.name} to {output_path}.{self.file_format.lower()}")
            except Exception as e:
                print(f"Error rendering {coll.name}: {str(e)}")
            
            # Hide it again
            coll.hide_render = True
        
        # Restore original visibility and settings
        for coll, visible in original_visibility.items():
            coll.hide_render = not visible
        render.film_transparent = original_transparent
        render.image_settings.file_format = original_format
        
        self.report({'INFO'}, f"Rendered {len(collections)} collections to {self.directory}")
        print(f"Rendered {len(collections)} collections to {self.directory}")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Open the file browser with options."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        """Customize the file browser popup."""
        layout = self.layout
        layout.prop(self, "transparent")
        layout.prop(self, "file_format")

# Register and run for Beb.Tools compatibility
bpy.utils.register_class(BEBTOOLS_OT_RenderCollections)
bpy.ops.bebtools.render_collections('INVOKE_DEFAULT')