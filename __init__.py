import sys
import os

# Add the lib folder to sys.path for bundled dependencies (e.g., requests)
addon_dir = os.path.dirname(__file__)
lib_dir = os.path.join(addon_dir, "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

bl_info = {
    "name": "Beb.Tools",
    "author": "Beb",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Beb.Tools",
    "description": "The swiss army knife that lets you add and manage custom tools without needing to be a computer wizard.",
    "warning": "",
    "doc_url": "https://docs.beb.tools",
    "category": "Object",
}

import bpy
from .modules import bebtools_properties as props
from .modules import bebtools_ui as ui
from .modules import bebtools_core as core
from .modules import bebtools_queue as queue
from .modules import bebtools_script as script
from .modules import bebtools_instructions as instr


def script_context_menu(self, context):
    wm = context.window_manager
    layout = self.layout
    if hasattr(wm, "bebtools_active_index"):  # Check if we're in Beb.Tools context
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not script_item.is_folder:  # Only for scripts
                layout.menu("BEBTOOLS_MT_script_menu")

def register():
    props.register_properties()
    for cls in ui.classes:
        bpy.utils.register_class(cls)
    for cls in core.classes:
        bpy.utils.register_class(cls)
    for cls in queue.classes:
        bpy.utils.register_class(cls)
    for cls in script.classes:
        bpy.utils.register_class(cls)
    for cls in instr.classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(core.init_scripts_timer, first_interval=0.1)

def unregister():
    if bpy.app.timers.is_registered(core.init_scripts_timer):
        bpy.app.timers.unregister(core.init_scripts_timer)
    for cls in reversed(instr.classes):
        bpy.utils.unregister_class(cls)
    for cls in reversed(script.classes):
        bpy.utils.unregister_class(cls)
    for cls in reversed(queue.classes):
        bpy.utils.unregister_class(cls)
    for cls in reversed(core.classes):
        bpy.utils.unregister_class(cls)
    for cls in reversed(ui.classes):
        bpy.utils.unregister_class(cls)
    props.unregister_properties()

if __name__ == "__main__":
    register()