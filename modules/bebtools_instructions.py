import bpy
import os
from bpy.types import Operator
from bpy.props import BoolProperty
from .bebtools_utils import update_info_text, open_or_reuse_text_editor


class BEBTOOLS_OT_EditInstructions(Operator):
    bl_idname = "bebtools.edit_instructions"
    bl_label = "Edit Instructions"
    bl_description = "Edit the selected script's instructions in the Text Editor"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to edit its instructions")
                return {'CANCELLED'}
            script_path = script_item.path
            script_name = script_item.name
            info_path = os.path.splitext(script_path)[0] + ".txt"
            text_block = bpy.data.texts.get(script_name + ".txt")
            if not text_block and os.path.exists(info_path):
                text_block = bpy.data.texts.new(script_name + ".txt")
                with open(info_path, "r") as f:
                    text_block.from_string(f.read())
            elif not text_block:
                text_block = bpy.data.texts.new(script_name + ".txt")
                text_block.from_string(f"Instructions for {script_name}")

            open_or_reuse_text_editor(context, text_block)
            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text == text_block:
                    area.spaces.active.top = 0
                    area.tag_redraw()
                    break
        return {'FINISHED'}


class BEBTOOLS_OT_SaveInstructions(Operator):
    bl_idname = "bebtools.save_instructions"
    bl_label = "Save Instructions"
    bl_description = "Save the current Text Editor contents to the selected script's instructions file"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to save its instructions")
                return {'CANCELLED'}
            script_path = script_item.path
            script_name = script_item.name
            info_path = os.path.splitext(script_path)[0] + ".txt"
            text_block = None
            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text:
                    text_block = area.spaces.active.text
                    break
            if text_block and text_block.name == f"{script_name}.txt":
                try:
                    with open(info_path, "w") as f:
                        f.write(text_block.as_string())
                    self.report({'INFO'}, f"Saved changes to {script_name}.txt")
                    update_info_text(context)
                except Exception as e:
                    self.report({'ERROR'}, f"Error saving {script_name}.txt: {str(e)}")
            else:
                self.report({'WARNING'}, "No matching instructions file open in Text Editor")
        else:
            self.report({'WARNING'}, "No script selected")
        return {'FINISHED'}


class BEBTOOLS_OT_PasteEditInstructions(Operator):
    bl_idname = "bebtools.paste_edit_instructions"
    bl_label = "Edit-Paste-Save Instructions"
    bl_description = "Open the selected script's instructions, paste clipboard contents, and save"

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to edit-paste-save its instructions")
                return {'CANCELLED'}
            return context.window_manager.invoke_confirm(self, event)
        else:
            self.report({'WARNING'}, "No script selected")
            return {'CANCELLED'}

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            script_path = script_item.path
            script_name = script_item.name
            info_path = os.path.splitext(script_path)[0] + ".txt"
            
            text_block = bpy.data.texts.get(script_name + ".txt")
            if not text_block and os.path.exists(info_path):
                text_block = bpy.data.texts.new(script_name + ".txt")
                with open(info_path, "r") as f:
                    text_block.from_string(f.read())
            elif not text_block:
                text_block = bpy.data.texts.new(script_name + ".txt")
                text_block.from_string(f"Instructions for {script_name}")
            open_or_reuse_text_editor(context, text_block)

            clipboard = context.window_manager.clipboard
            if clipboard:
                text_block.clear()
                text_block.from_string(clipboard)
            else:
                text_block.clear()
                self.report({'INFO'}, "Clipboard is empty; instructions cleared")

            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text == text_block:
                    area.spaces.active.top = 0
                    area.tag_redraw()
                    break

            try:
                with open(info_path, "w") as f:
                    f.write(text_block.as_string())
                self.report({'INFO'}, f"Pasted clipboard and saved to {script_name}.txt")
                update_info_text(context)
            except Exception as e:
                self.report({'ERROR'}, f"Error saving {script_name}.txt: {str(e)}")
                return {'CANCELLED'}

        return {'FINISHED'}


classes = (
    BEBTOOLS_OT_EditInstructions,
    BEBTOOLS_OT_SaveInstructions,
    BEBTOOLS_OT_PasteEditInstructions,
)