import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from .bebtools_utils import SCRIPTS_DIR, update_info_text, get_scripts

class BEBTOOLS_OT_InitScripts(Operator):
    bl_idname = "bebtools.init_scripts"
    bl_label = "Initialize Script List"
    bl_description = "Populate the script list"
    directory: StringProperty(default=SCRIPTS_DIR)

    def execute(self, context):
        wm = context.window_manager
        load_dir = self.directory if self.directory else SCRIPTS_DIR
        print(f"Initializing with directory: {load_dir}")
        get_scripts(load_dir)
        wm.bebtools_active_index = -1
        wm.bebtools_current_dir = load_dir  # Set current dir on init
        update_info_text(context)
        return {'FINISHED'}

class BEBTOOLS_OT_Run(Operator):
    bl_idname = "bebtools.run"
    bl_label = "▶ Run"
    bl_description = "Run the selected script"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to run")
                return {'CANCELLED'}
            script_path = script_item.path
            try:
                with open(script_path, "r") as f:
                    exec(f.read(), globals())
                self.report({'INFO'}, f"Executed script: {script_item.name}")
            except Exception as e:
                self.report({'ERROR'}, f"Error running {script_item.name}: {str(e)}")
        else:
            self.report({'WARNING'}, "No script selected")
        return {'FINISHED'}


class BEBTOOLS_OT_MultiRun(Operator):
    bl_idname = "bebtools.multi_run"
    bl_label = "Run All"
    bl_description = "Run all queued scripts in order"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        if context.window_manager.bebtools_queue:
            return context.window_manager.invoke_confirm(self, event)
        else:
            self.report({'WARNING'}, "No scripts in the queue")
            return {'CANCELLED'}

    def execute(self, context):
        wm = context.window_manager
        for item in wm.bebtools_queue:
            script_path = item.path
            try:
                with open(script_path, "r") as f:
                    exec(f.read(), globals())
                self.report({'INFO'}, f"Executed script: {item.name}")
            except Exception as e:
                self.report({'ERROR'}, f"Error running {item.name}: {str(e)}")
        return {'FINISHED'}


classes = (
    BEBTOOLS_OT_InitScripts,
    BEBTOOLS_OT_Run,
    BEBTOOLS_OT_MultiRun,
)


def init_scripts_timer():
    bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT')
    return None