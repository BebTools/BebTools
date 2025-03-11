import bpy
import os
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from .bebtools_utils import SCRIPTS_DIR, update_info_text, open_or_reuse_text_editor, get_scripts

class BEBTOOLS_OT_MoveTo(Operator):
    bl_idname = "bebtools.move_to"
    bl_label = "Move"
    bl_description = "Move the selected script to another folder"
    bl_options = {'REGISTER', 'INTERNAL'}

    def get_move_options(self, context):
        wm = context.window_manager
        current_dir = wm.bebtools_current_dir if wm.bebtools_current_dir else SCRIPTS_DIR
        parent_dir = os.path.dirname(current_dir)
        options = []

        # Add subfolders of current directory
        for d in sorted(os.listdir(current_dir)):
            full_path = os.path.join(current_dir, d)
            if os.path.isdir(full_path):
                options.append((full_path, d, f"Move to {d} (current level)"))

        # Add parent directory (one level up), if not at root
        if current_dir != SCRIPTS_DIR:
            options.append((parent_dir, "Scripts" if parent_dir == SCRIPTS_DIR else os.path.basename(parent_dir), f"Move up to {os.path.basename(parent_dir)}"))

        return options if options else [(SCRIPTS_DIR, "Scripts", "Move to /scripts/")]

    destination: bpy.props.EnumProperty(
        name="Destination Folder",
        description="Choose a folder to move the script to",
        items=get_move_options
    )

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to move")
                return {'CANCELLED'}
            return wm.invoke_props_dialog(self)
        self.report({'WARNING'}, "No script selected")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "destination", text="Move To")

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to move")
                return {'CANCELLED'}

            src_py = script_item.path
            src_txt = os.path.splitext(src_py)[0] + ".txt"
            dest_dir = self.destination
            dest_py = os.path.join(dest_dir, os.path.basename(src_py))
            dest_txt = os.path.join(dest_dir, os.path.basename(src_txt))

            if os.path.exists(dest_py):
                self.report({'WARNING'}, f"'{script_item.name}.py' already exists in {dest_dir}")
                return {'CANCELLED'}

            try:
                os.rename(src_py, dest_py)
                if os.path.exists(src_txt):
                    os.rename(src_txt, dest_txt)
                self.report({'INFO'}, f"Moved '{script_item.name}' to {dest_dir}")
                bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=wm.bebtools_current_dir)
                wm.bebtools_active_index = -1
                update_info_text(context)
            except Exception as e:
                self.report({'ERROR'}, f"Error moving '{script_item.name}': {str(e)}")
                return {'CANCELLED'}
        return {'FINISHED'}

class BEBTOOLS_OT_EditScript(Operator):
    bl_idname = "bebtools.edit_script"
    bl_label = "Edit"
    bl_description = "Edit the selected script in the Text Editor"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to edit")
                return {'CANCELLED'}
            script_path = script_item.path
            script_name = script_item.name
            text_block = bpy.data.texts.get(script_name + ".py")
            if not text_block and os.path.exists(script_path):
                text_block = bpy.data.texts.new(script_name + ".py")
                with open(script_path, "r") as f:
                    text_block.from_string(f.read())
            elif not text_block:
                self.report({'WARNING'}, f"Script file {script_name}.py not found")
                return {'CANCELLED'}

            open_or_reuse_text_editor(context, text_block)
            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text == text_block:
                    area.spaces.active.top = 0
                    area.tag_redraw()
                    break
        return {'FINISHED'}


class BEBTOOLS_OT_SaveScript(Operator):
    bl_idname = "bebtools.save_script"
    bl_label = "Save"
    bl_description = "Save the current Text Editor contents to the selected script file"

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to save")
                return {'CANCELLED'}
            script_path = script_item.path
            script_name = script_item.name
            text_block = None
            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text:
                    text_block = area.spaces.active.text
                    break
            if text_block and text_block.name == f"{script_name}.py":
                try:
                    with open(script_path, "w") as f:
                        f.write(text_block.as_string())
                    self.report({'INFO'}, f"Saved changes to {script_name}.py")
                except Exception as e:
                    self.report({'ERROR'}, f"Error saving {script_name}.py: {str(e)}")
            else:
                self.report({'WARNING'}, "No matching script open in Text Editor")
        else:
            self.report({'WARNING'}, "No script selected")
        return {'FINISHED'}


class BEBTOOLS_OT_PasteEdit(Operator):
    bl_idname = "bebtools.paste_edit"
    bl_label = "Edit-Paste-Save"
    bl_description = "Open the selected script, paste clipboard contents, and save"

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to edit-paste-save")
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
            
            text_block = bpy.data.texts.get(script_name + ".py")
            if not text_block and os.path.exists(script_path):
                text_block = bpy.data.texts.new(script_name + ".py")
                with open(script_path, "r") as f:
                    text_block.from_string(f.read())
            elif not text_block:
                self.report({'WARNING'}, f"Script file {script_name}.py not found")
                return {'CANCELLED'}
            open_or_reuse_text_editor(context, text_block)

            clipboard = context.window_manager.clipboard
            if clipboard:
                text_block.clear()
                text_block.from_string(clipboard)
            else:
                text_block.clear()
                self.report({'INFO'}, "Clipboard is empty; script cleared")

            for area in context.screen.areas:
                if area.type == 'TEXT_EDITOR' and area.spaces.active.text == text_block:
                    area.spaces.active.top = 0
                    area.tag_redraw()
                    break

            try:
                with open(script_path, "w") as f:
                    f.write(text_block.as_string())
                self.report({'INFO'}, f"Pasted clipboard and saved to {script_name}.py")
            except Exception as e:
                self.report({'ERROR'}, f"Error saving {script_name}.py: {str(e)}")
                return {'CANCELLED'}

        return {'FINISHED'}

class BEBTOOLS_OT_NewScript(Operator):
    bl_idname = "bebtools.new_script"
    bl_label = "New Script"
    bl_description = "Create a new Python script"
    bl_options = {'REGISTER', 'INTERNAL'}

    name: StringProperty(name="Name", default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name", text="Name")

    def execute(self, context):
        wm = context.window_manager
        name = self.name.strip()
        if not name:
            self.report({'WARNING'}, "Please enter a name")
            return {'CANCELLED'}

        base_dir = wm.bebtools_current_dir if wm.bebtools_current_dir else SCRIPTS_DIR
        if name.endswith(".py"):
            name = name[:-3]
        script_path = os.path.join(base_dir, f"{name}.py")
        info_path = os.path.join(base_dir, f"{name}.txt")
        if os.path.exists(script_path):
            self.report({'WARNING'}, f"Script {name}.py already exists in this folder")
            return {'CANCELLED'}

        with open(script_path, "w") as f:
            f.write("# New script created by Beb.Tools\n")
        with open(info_path, "w") as f:
            f.write(f"Instructions for {name}\n")

        get_scripts(base_dir)
        if base_dir != SCRIPTS_DIR:
            back_item = wm.bebtools_scripts.add()
            back_item.name = "Back"
            back_item.path = os.path.dirname(base_dir)
            back_item.is_folder = True
            wm.bebtools_scripts.move(len(wm.bebtools_scripts) - 1, 0)
        wm.bebtools_active_index = -1
        text_block = bpy.data.texts.new(f"{name}.py")
        text_block.from_string("# New script created by Beb.Tools\n")
        open_or_reuse_text_editor(context, text_block)
        update_info_text(context)
        self.report({'INFO'}, f"Created and opened {name}.py")
        return {'FINISHED'}

class BEBTOOLS_OT_NewFolder(Operator):
    bl_idname = "bebtools.new_folder"
    bl_label = "New Folder"
    bl_description = "Create a new folder"
    bl_options = {'REGISTER', 'INTERNAL'}

    name: StringProperty(name="Name", default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name", text="Name")

    def execute(self, context):
        wm = context.window_manager
        name = self.name.strip()
        if not name:
            self.report({'WARNING'}, "Please enter a name")
            return {'CANCELLED'}

        base_dir = wm.bebtools_current_dir if wm.bebtools_current_dir else SCRIPTS_DIR
        folder_path = os.path.join(base_dir, name)
        if os.path.exists(folder_path):
            self.report({'WARNING'}, f"Folder '{name}' already exists in this folder")
            return {'CANCELLED'}

        try:
            os.makedirs(folder_path, exist_ok=True)
            get_scripts(base_dir)
            if base_dir != SCRIPTS_DIR:
                back_item = wm.bebtools_scripts.add()
                back_item.name = "Back"
                back_item.path = os.path.dirname(base_dir)
                back_item.is_folder = True
                wm.bebtools_scripts.move(len(wm.bebtools_scripts) - 1, 0)
            wm.bebtools_active_index = -1
            update_info_text(context)
            self.report({'INFO'}, f"Created folder '{name}'")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error creating folder: {str(e)}")
            return {'CANCELLED'}

class BEBTOOLS_OT_OpenFolderContents(Operator):
    bl_idname = "bebtools.open_folder_contents"
    bl_label = "Open Folder"
    bl_description = "Open the selected folder to view its contents"
    index: bpy.props.IntProperty()

    def execute(self, context):
        wm = context.window_manager
        if self.index >= 0 and self.index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[self.index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to open")
                return {'CANCELLED'}
            folder_path = folder_item.path
            parent_path = os.path.dirname(folder_path)
            print(f"Opening folder: {folder_path}, Parent: {parent_path}")  # Debug log
            wm.bebtools_active_index = -1  # Reset before navigation
            get_scripts(folder_path)
            # Add Back if there’s a parent directory
            if parent_path and parent_path != folder_path:  # Ensure parent exists and isn’t self
                back_item = wm.bebtools_scripts.add()
                back_item.name = "Back"
                back_item.path = parent_path
                back_item.is_folder = True
                wm.bebtools_scripts.move(len(wm.bebtools_scripts) - 1, 0)
            wm.bebtools_current_dir = folder_path
            update_info_text(context)
            self.report({'INFO'}, f"Opened folder '{folder_item.name}'")
            return {'FINISHED'}
        self.report({'WARNING'}, "Invalid folder index")
        return {'CANCELLED'}

class BEBTOOLS_OT_DeleteFolder(Operator):
    bl_idname = "bebtools.delete_folder"
    bl_label = "Delete Folder"
    bl_description = "Delete the selected folder and its contents"
    bl_options = {'REGISTER', 'INTERNAL'}
    index: bpy.props.IntProperty()

    def invoke(self, context, event):
        wm = context.window_manager
        if self.index >= 0 and self.index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[self.index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to delete")
                return {'CANCELLED'}
            return context.window_manager.invoke_confirm(self, event)
        self.report({'WARNING'}, "No folder selected")
        return {'CANCELLED'}

    def execute(self, context):
        wm = context.window_manager
        if self.index >= 0 and self.index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[self.index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to delete")
                return {'CANCELLED'}

            folder_path = folder_item.path
            folder_name = folder_item.name
            parent_dir = os.path.dirname(folder_path)  # Stay in parent after delete
            try:
                import shutil
                shutil.rmtree(folder_path)
                self.report({'INFO'}, f"Deleted folder '{folder_name}' and its contents")
                get_scripts(parent_dir)  # Reload parent dir, not root
                if parent_dir != SCRIPTS_DIR:  # Add Back if not at root
                    back_item = wm.bebtools_scripts.add()
                    back_item.name = "Back"
                    back_item.path = os.path.dirname(parent_dir)
                    back_item.is_folder = True
                    wm.bebtools_scripts.move(len(wm.bebtools_scripts) - 1, 0)
                wm.bebtools_active_index = -1
                wm.bebtools_current_dir = parent_dir  # Update current dir
                update_info_text(context)
                return {'FINISHED'}
            except Exception as e:
                self.report({'ERROR'}, f"Error deleting folder: {str(e)}")
                return {'CANCELLED'}
        self.report({'WARNING'}, "Invalid folder index")
        return {'CANCELLED'}

class BEBTOOLS_OT_DeleteScript(Operator):
    bl_idname = "bebtools.delete_script"
    bl_label = "Delete Script"
    bl_description = "Delete the selected script"
    bl_options = {'REGISTER', 'INTERNAL'}

    confirm: BoolProperty(name="Confirm", default=False)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to delete")
                return {'CANCELLED'}
            script_path = script_item.path
            info_path = os.path.splitext(script_path)[0] + ".txt"
            try:
                if os.path.exists(script_path):
                    os.remove(script_path)
                if os.path.exists(info_path):
                    os.remove(info_path)
                wm.bebtools_scripts.remove(wm.bebtools_active_index)
                wm.bebtools_active_index = min(wm.bebtools_active_index, len(wm.bebtools_scripts) - 1)
                if not wm.bebtools_queue:
                    wm.bebtools_active_index = -1
                update_info_text(context)
                self.report({'INFO'}, f"Deleted {script_item.name}.py and its info file")
            except Exception as e:
                self.report({'ERROR'}, f"Error deleting {script_item.name}: {str(e)}")
        return {'FINISHED'}

class BEBTOOLS_OT_RenameScript(Operator):
    bl_idname = "bebtools.rename_script"
    bl_label = "Rename"
    bl_description = "Rename the selected script"
    bl_options = {'REGISTER', 'INTERNAL'}

    new_name: StringProperty(name="New Name", default="")

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to rename")
                return {'CANCELLED'}
            self.new_name = script_item.name  # Pre-fill with current name
            return context.window_manager.invoke_props_dialog(self)
        self.report({'WARNING'}, "No script selected")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text="New Name")

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if script_item.is_folder:
                self.report({'WARNING'}, "Select a script to rename")
                return {'CANCELLED'}

            old_py = script_item.path
            old_txt = os.path.splitext(old_py)[0] + ".txt"
            new_name = self.new_name.strip()
            if not new_name:
                self.report({'WARNING'}, "Please enter a new name")
                return {'CANCELLED'}
            if new_name.endswith(".py"):
                new_name = new_name[:-3]  # Strip .py if user typed it
            new_py = os.path.join(os.path.dirname(old_py), f"{new_name}.py")
            new_txt = os.path.join(os.path.dirname(old_py), f"{new_name}.txt")

            if os.path.exists(new_py):
                self.report({'WARNING'}, f"Script '{new_name}.py' already exists")
                return {'CANCELLED'}

            try:
                os.rename(old_py, new_py)
                self.report({'INFO'}, f"Renamed script to '{new_name}.py'")
                if os.path.exists(old_txt):
                    os.rename(old_txt, new_txt)
                    self.report({'INFO'}, f"Renamed instructions to '{new_name}.txt'")
                else:
                    self.report({'INFO'}, f"No instructions file found for '{script_item.name}'")
                bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT')
                wm.bebtools_active_index = -1
                update_info_text(context)
            except Exception as e:
                self.report({'ERROR'}, f"Error renaming '{script_item.name}': {str(e)}")
                return {'CANCELLED'}
        return {'FINISHED'}

class BEBTOOLS_OT_RenameFolder(Operator):
    bl_idname = "bebtools.rename_folder"
    bl_label = "Rename Folder"
    bl_description = "Rename the selected folder"
    bl_options = {'REGISTER', 'INTERNAL'}

    new_name: StringProperty(name="New Name", default="")

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to rename")
                return {'CANCELLED'}
            self.new_name = folder_item.name
            return context.window_manager.invoke_props_dialog(self)
        self.report({'WARNING'}, "No folder selected")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text="New Name")

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to rename")
                return {'CANCELLED'}

            old_path = folder_item.path
            new_name = self.new_name.strip()
            if not new_name:
                self.report({'WARNING'}, "Please enter a new name")
                return {'CANCELLED'}
            new_path = os.path.join(os.path.dirname(old_path), new_name)

            if os.path.exists(new_path):
                self.report({'WARNING'}, f"Folder '{new_name}' already exists")
                return {'CANCELLED'}

            try:
                os.rename(old_path, new_path)
                self.report({'INFO'}, f"Renamed folder to '{new_name}'")
                bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT')
                wm.bebtools_active_index = -1
                update_info_text(context)
            except Exception as e:
                self.report({'ERROR'}, f"Error renaming folder: {str(e)}")
                return {'CANCELLED'}
        return {'FINISHED'}

class BEBTOOLS_OT_MoveFolder(Operator):
    bl_idname = "bebtools.move_folder"
    bl_label = "Move Folder"
    bl_description = "Move the selected folder to another location"
    bl_options = {'REGISTER', 'INTERNAL'}

    def get_move_options(self, context):
        wm = context.window_manager
        current_dir = wm.bebtools_current_dir if wm.bebtools_current_dir else SCRIPTS_DIR
        parent_dir = os.path.dirname(current_dir)
        options = []

        # Add subfolders of current directory
        for d in sorted(os.listdir(current_dir)):
            full_path = os.path.join(current_dir, d)
            if os.path.isdir(full_path):
                options.append((full_path, d, f"Move to {d} (current level)"))

        # Add parent directory (one level up), if not at root
        if current_dir != SCRIPTS_DIR:
            options.append((parent_dir, "Scripts" if parent_dir == SCRIPTS_DIR else os.path.basename(parent_dir), f"Move up to {os.path.basename(parent_dir)}"))

        return options if options else [(SCRIPTS_DIR, "Scripts", "Move to /scripts/")]

    destination: bpy.props.EnumProperty(
        name="Destination Folder",
        description="Choose a folder to move the folder to",
        items=get_move_options
    )

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to move")
                return {'CANCELLED'}
            return wm.invoke_props_dialog(self)
        self.report({'WARNING'}, "No folder selected")
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "destination", text="Move To")

    def execute(self, context):
        wm = context.window_manager
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            folder_item = wm.bebtools_scripts[wm.bebtools_active_index]
            if not folder_item.is_folder or folder_item.name == "Back":
                self.report({'WARNING'}, "Select a folder to move")
                return {'CANCELLED'}

            src_path = folder_item.path
            dest_dir = self.destination
            dest_path = os.path.join(dest_dir, os.path.basename(src_path))

            if os.path.exists(dest_path):
                self.report({'WARNING'}, f"Folder '{os.path.basename(src_path)}' already exists in {dest_dir}")
                return {'CANCELLED'}

            try:
                os.rename(src_path, dest_path)
                self.report({'INFO'}, f"Moved folder to {dest_dir}")
                bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=wm.bebtools_current_dir)
                wm.bebtools_active_index = -1
                update_info_text(context)
            except Exception as e:
                self.report({'ERROR'}, f"Error moving folder: {str(e)}")
                return {'CANCELLED'}
        return {'FINISHED'}

classes = (
    BEBTOOLS_OT_EditScript,
    BEBTOOLS_OT_SaveScript,
    BEBTOOLS_OT_PasteEdit,
    BEBTOOLS_OT_NewScript,
    BEBTOOLS_OT_NewFolder,
    BEBTOOLS_OT_DeleteScript,
    BEBTOOLS_OT_MoveTo,
    BEBTOOLS_OT_RenameScript,
    BEBTOOLS_OT_RenameFolder,
    BEBTOOLS_OT_MoveFolder,
    BEBTOOLS_OT_DeleteFolder,
    BEBTOOLS_OT_OpenFolderContents,
)