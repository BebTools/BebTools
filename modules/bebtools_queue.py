import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty  # Added BoolProperty
from .bebtools_utils import SCRIPTS_DIR

class BEBTOOLS_OT_Queue(Operator):
    bl_idname = "bebtools.queue"
    bl_label = "Queue"
    bl_description = "Add the selected script to the queue"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to queue")
                return {'CANCELLED'}
            script_name = script_item.name
            if not any(item.name == script_name for item in wm.bebtools_queue):
                item = wm.bebtools_queue.add()
                item.name = script_name
                item.path = script_item.path
                wm.bebtools_queue_index = len(wm.bebtools_queue) - 1
                self.report({'INFO'}, f"Queued {script_name}")
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
            else:
                self.report({'WARNING'}, f"{script_name} is already in the queue")
        return {'FINISHED'}

class BEBTOOLS_OT_RemoveFromQueue(Operator):
    bl_idname = "bebtools.remove_from_queue"
    bl_label = "Remove"
    bl_description = "Remove the selected script from the queue"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_queue_index >= 0 and wm.bebtools_queue:
            script_name = wm.bebtools_queue[wm.bebtools_queue_index].name
            wm.bebtools_queue.remove(wm.bebtools_queue_index)
            wm.bebtools_queue_index = min(wm.bebtools_queue_index, len(wm.bebtools_queue) - 1)
            if not wm.bebtools_queue:
                wm.bebtools_queue_index = -1
            self.report({'INFO'}, f"Removed {script_name} from queue")
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    break
        return {'FINISHED'}

class BEBTOOLS_OT_MoveUp(Operator):
    bl_idname = "bebtools.move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected script up in the queue"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_queue_index > 0:
            wm.bebtools_queue.move(wm.bebtools_queue_index, wm.bebtools_queue_index - 1)
            wm.bebtools_queue_index -= 1
        return {'FINISHED'}

class BEBTOOLS_OT_MoveDown(Operator):
    bl_idname = "bebtools.move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected script down in the queue"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_queue_index >= 0 and wm.bebtools_queue_index < len(wm.bebtools_queue) - 1:
            wm.bebtools_queue.move(wm.bebtools_queue_index, wm.bebtools_queue_index + 1)
            wm.bebtools_queue_index += 1
        return {'FINISHED'}

class BEBTOOLS_OT_SaveQueue(Operator):
    bl_idname = "bebtools.save_queue"
    bl_label = "Save Queue"
    bl_description = "Save the current queue to a file"
    bl_options = {'REGISTER', 'INTERNAL'}

    queue_name: StringProperty(name="Queue Name", default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "queue_name", text="Name")

    def execute(self, context):
        wm = context.window_manager
        if not wm.bebtools_queue:
            self.report({'WARNING'}, "Queue is empty, nothing to save")
            return {'CANCELLED'}
        
        name = self.queue_name.strip()
        if not name:
            self.report({'WARNING'}, "Please enter a queue name")
            return {'CANCELLED'}
        if name.endswith(".txt"):
            name = name[:-4]
        
        queues_dir = os.path.join(os.path.dirname(__file__), "..", "queues")
        os.makedirs(queues_dir, exist_ok=True)
        
        queue_path = os.path.join(queues_dir, f"{name}.txt")
        if os.path.exists(queue_path):
            self.report({'WARNING'}, f"Queue '{name}.txt' already exists")
            return {'CANCELLED'}

        try:
            with open(queue_path, "w") as f:
                for item in wm.bebtools_queue:
                    f.write(f"{item.name}\n")
            self.report({'INFO'}, f"Saved queue to {name}.txt")
        except Exception as e:
            self.report({'ERROR'}, f"Error saving queue: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class BEBTOOLS_OT_LoadQueue(Operator):
    bl_idname = "bebtools.load_queue"
    bl_label = "Load Queue"
    bl_description = "Load a saved queue from a file"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.txt", options={'HIDDEN'})

    def invoke(self, context, event):
        queues_dir = os.path.join(os.path.dirname(__file__), "..", "queues")
        os.makedirs(queues_dir, exist_ok=True)
        self.filepath = queues_dir
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        wm = context.window_manager
        if not os.path.exists(self.filepath):
            self.report({'WARNING'}, "Selected file does not exist")
            return {'CANCELLED'}

        script_names = []
        try:
            with open(self.filepath, "r") as f:
                script_names = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            self.report({'ERROR'}, f"Error reading queue file: {str(e)}")
            return {'CANCELLED'}

        if not script_names:
            self.report({'WARNING'}, "Queue file is empty")
            return {'CANCELLED'}

        scripts_dir = SCRIPTS_DIR
        script_paths = {}
        for root, _, files in os.walk(scripts_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    script_name = file[:-3]
                    script_paths[script_name] = os.path.join(root, file)

        wm.bebtools_queue.clear()
        missing_scripts = []
        for name in script_names:
            if name in script_paths:
                item = wm.bebtools_queue.add()
                item.name = name
                item.path = script_paths[name]
            else:
                missing_scripts.append(name)

        if wm.bebtools_queue:
            wm.bebtools_queue_index = 0
            self.report({'INFO'}, f"Loaded queue from {os.path.basename(self.filepath)}")
            if missing_scripts:
                self.report({'WARNING'}, f"Could not find scripts: {', '.join(missing_scripts)}")
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        else:
            self.report({'WARNING'}, "No matching scripts found in /scripts/")
            return {'CANCELLED'}

        return {'FINISHED'}

class BEBTOOLS_OT_RunSelected(Operator):
    bl_idname = "bebtools.run_selected"
    bl_label = "Run Selected"
    bl_description = "Run the selected script from the queue"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_queue_index >= 0 and wm.bebtools_queue_index < len(wm.bebtools_queue):
            script_item = wm.bebtools_queue[wm.bebtools_queue_index]
            script_path = script_item.path
            try:
                with open(script_path, "r") as f:
                    exec(f.read(), globals())
                self.report({'INFO'}, f"Executed script: {script_item.name}")
            except Exception as e:
                self.report({'ERROR'}, f"Error running {script_item.name}: {str(e)}")
        else:
            self.report({'WARNING'}, "No script selected in queue")
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
                break
        return {'FINISHED'}

class BEBTOOLS_OT_LoadSelectedQueue(Operator):
    bl_idname = "bebtools.load_selected_queue"
    bl_label = "Load"
    bl_description = "Load the selected queue from the dropdown"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_selected_queue:
            bpy.ops.bebtools.load_queue(filepath=wm.bebtools_selected_queue)
            self.report({'INFO'}, f"Loaded queue: {os.path.basename(wm.bebtools_selected_queue)[:-4]}")
        else:
            self.report({'WARNING'}, "No queue selected")
        return {'FINISHED'}

class BEBTOOLS_OT_ClearQueue(Operator):
    bl_idname = "bebtools.clear_queue"
    bl_label = "Clear"
    bl_description = "Remove all scripts from the queue"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_queue:
            wm.bebtools_queue.clear()
            wm.bebtools_queue_index = -1
            self.report({'INFO'}, "Queue cleared")
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
                    break
        else:
            self.report({'INFO'}, "Queue is already empty")
        return {'FINISHED'}

class BEBTOOLS_OT_DeleteQueue(Operator):
    bl_idname = "bebtools.delete_queue"
    bl_label = "Delete Queue"
    bl_description = "Delete the selected saved queue file"

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_selected_queue:
            return context.window_manager.invoke_confirm(self, event)
        self.report({'WARNING'}, "No queue selected to delete")
        return {'CANCELLED'}

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_selected_queue:
            queue_path = wm.bebtools_selected_queue
            try:
                os.remove(queue_path)
                self.report({'INFO'}, f"Deleted queue: {os.path.basename(queue_path)[:-4]}")
                if wm.bebtools_queue and wm.bebtools_queue[0].path.startswith(os.path.dirname(queue_path)):
                    wm.bebtools_queue.clear()
                    wm.bebtools_queue_index = -1
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                        break
            except Exception as e:
                self.report({'ERROR'}, f"Error deleting queue: {str(e)}")
                return {'CANCELLED'}
        return {'FINISHED'}

# New operator to queue all scripts in a folder
class BEBTOOLS_OT_QueueFolder(Operator):
    bl_idname = "bebtools.queue_folder"
    bl_label = "Queue Folder"
    bl_description = "Add all scripts in the selected folder to the queue"
    bl_options = {'REGISTER', 'INTERNAL'}

    recursive: BoolProperty(
        name="Include Subfolders",
        default=True,
        description="Queue scripts from subfolders as well"
    )

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not script_item.is_folder or script_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to queue")
                return {'CANCELLED'}
            return context.window_manager.invoke_props_dialog(self)
        self.report({'WARNING'}, "No folder selected")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "recursive")

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to queue")
                return {'CANCELLED'}
            folder_path = folder_item.path
            # Use os.walk for recursive, os.listdir for non-recursive
            if self.recursive:
                for root, _, files in os.walk(folder_path):
                    for file in sorted(files):  # Sort for consistent order
                        if file.endswith(".py") and not file.startswith("__"):
                            script_name = file[:-3]
                            script_path = os.path.join(root, file)
                            if not any(item.name == script_name for item in wm.bebtools_queue):
                                item = wm.bebtools_queue.add()
                                item.name = script_name
                                item.path = script_path
            else:
                for file in sorted(os.listdir(folder_path)):
                    full_path = os.path.join(folder_path, file)
                    if os.path.isfile(full_path) and file.endswith(".py") and not file.startswith("__"):
                        script_name = file[:-3]
                        if not any(item.name == script_name for item in wm.bebtools_queue):
                            item = wm.bebtools_queue.add()
                            item.name = script_name
                            item.path = full_path
            wm.bebtools_queue_index = len(wm.bebtools_queue) - 1
            self.report({'INFO'}, f"Queued all scripts from '{folder_item.name}'{' and subfolders' if self.recursive else ''}")
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}

classes = (
    BEBTOOLS_OT_Queue,
    BEBTOOLS_OT_RemoveFromQueue,
    BEBTOOLS_OT_MoveUp,
    BEBTOOLS_OT_MoveDown,
    BEBTOOLS_OT_ClearQueue,
    BEBTOOLS_OT_SaveQueue,
    BEBTOOLS_OT_LoadQueue,
    BEBTOOLS_OT_RunSelected,
    BEBTOOLS_OT_LoadSelectedQueue,
    BEBTOOLS_OT_DeleteQueue,
    BEBTOOLS_OT_QueueFolder,  # Register new operator
)