import bpy
import os
from bpy.props import StringProperty, IntProperty, CollectionProperty, BoolProperty, EnumProperty
from .bebtools_utils import update_info_text, get_scripts

def update_active_index(self, context):
    wm = context.window_manager
    if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
        script_item = wm.bebtools_scripts[wm.bebtools_active_index]
        update_info_text(context)

class BebToolsScriptItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Name")
    path: StringProperty(name="Full Path")
    is_folder: BoolProperty(name="Is Folder")

class BebToolsQueueItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Script Name")
    path: StringProperty(name="Full Path")

class BebToolsTextLine(bpy.types.PropertyGroup):
    name: StringProperty(name="Text Line")

classes = (
    BebToolsScriptItem,
    BebToolsQueueItem,
    BebToolsTextLine,
)

def get_queue_files(self, context):
    queues_dir = os.path.join(os.path.dirname(__file__), "..", "queues")
    os.makedirs(queues_dir, exist_ok=True)
    return [(os.path.join(queues_dir, f), f[:-4], "") for f in os.listdir(queues_dir) if f.endswith(".txt")]

def register_properties():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.WindowManager.bebtools_scripts = CollectionProperty(type=BebToolsScriptItem)
    bpy.types.WindowManager.bebtools_active_index = IntProperty(
        name="Active Script Index",
        default=-1,
        update=update_active_index
    )
    bpy.types.WindowManager.bebtools_queue = CollectionProperty(type=BebToolsQueueItem)
    bpy.types.WindowManager.bebtools_queue_index = IntProperty(
        name="Queue Index",
        default=-1
    )
    bpy.types.WindowManager.bebtools_info_lines = CollectionProperty(type=BebToolsTextLine)
    bpy.types.WindowManager.bebtools_info_lines_index = IntProperty(
        name="Info Lines Index",
        default=-1
    )
    bpy.types.WindowManager.bebtools_developer_mode = BoolProperty(
        name="Expand Developer Mode",
        default=False
    )
    bpy.types.WindowManager.bebtools_selected_queue = EnumProperty(
        name="Saved Queues",
        description="Select a saved queue to load",
        items=get_queue_files,
        default=None
    )
    bpy.types.WindowManager.bebtools_current_dir = StringProperty(
        name="Current Directory",
        default="",
        description="Current folder path in Beb.Tools"
    )
    bpy.types.WindowManager.bebtools_edit_mode = BoolProperty(
        name="Edit Mode",
        default=False,
        description="Toggle edit mode to show editing options",
    )
    # New folder mode toggle property, enabled by default
    bpy.types.WindowManager.bebtools_folder_mode = BoolProperty(
        name="Folder Mode",
        default=True,
        description="Toggle folder mode to open folders directly without popup",
    )
    bpy.types.WindowManager.bebtools_search_query = StringProperty(
        name="Search Scripts",
        default="",
        description="Search for scripts across all folders",
        update=lambda self, context: bpy.ops.bebtools.search_scripts('INVOKE_DEFAULT'),  # Trigger search on any change
        search=lambda self, context, edit_text: None  # Enables the "X" inside the field (no autocomplete needed)
    )
    bpy.types.WindowManager.bebtools_search_active = BoolProperty(
        name="Search Active",
        default=False,
        description="Indicates if the script list is showing search results"
    )

def unregister_properties():
    del bpy.types.WindowManager.bebtools_scripts
    del bpy.types.WindowManager.bebtools_active_index
    del bpy.types.WindowManager.bebtools_queue
    del bpy.types.WindowManager.bebtools_queue_index
    del bpy.types.WindowManager.bebtools_info_lines
    del bpy.types.WindowManager.bebtools_info_lines_index
    del bpy.types.WindowManager.bebtools_developer_mode
    del bpy.types.WindowManager.bebtools_selected_queue
    del bpy.types.WindowManager.bebtools_current_dir
    del bpy.types.WindowManager.bebtools_edit_mode
    del bpy.types.WindowManager.bebtools_folder_mode
    del bpy.types.WindowManager.bebtools_search_query
    del bpy.types.WindowManager.bebtools_search_active
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)