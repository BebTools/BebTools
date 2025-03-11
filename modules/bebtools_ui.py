import bpy
import os
import requests
import shutil
from urllib.parse import unquote
from bpy.types import Panel, UIList, Operator
from bpy.props import StringProperty, CollectionProperty
from .bebtools_utils import SCRIPTS_DIR, get_scripts, update_info_text

class BEBTOOLS_UL_ScriptList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=False)
        row.alignment = 'LEFT'
        wm = context.window_manager
        
        if wm.bebtools_search_active:
            op = row.operator("bebtools.script_context_menu", text=item.name, icon="FILE_SCRIPT", emboss=False)
            op.index = index
        else:
            if item.name == "Back":
                op = row.operator("bebtools.navigate_back", text="Back", icon="BACK", emboss=False)
                op.index = index
            elif item.is_folder:
                if wm.bebtools_folder_mode:
                    op = row.operator("bebtools.open_folder_contents", text=item.name, icon="FILE_FOLDER", emboss=False)
                    op.index = index
                else:
                    op = row.operator("bebtools.folder_context_menu", text=item.name, icon="FILE_FOLDER", emboss=False)
                    op.index = index
            else:
                op = row.operator("bebtools.script_context_menu", text=item.name, icon="FILE_SCRIPT", emboss=False)
                op.index = index

class BEBTOOLS_OT_ScriptContextMenu(Operator):
    bl_idname = "bebtools.script_context_menu"
    bl_label = "Script Context Menu"
    bl_description = "Show script options"
    index: bpy.props.IntProperty()

    def invoke(self, context, event):
        wm = context.window_manager
        wm.bebtools_active_index = self.index
        return wm.invoke_popup(self, width=200)

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.operator("bebtools.run", text="Run", icon="PLAY")
        layout.operator("bebtools.queue", text="Queue", icon="FORWARD")
        if wm.bebtools_edit_mode:
            layout.separator()
            layout.operator("bebtools.edit_script", text="Edit", icon="TEXT")
            layout.operator("bebtools.paste_edit", text="Edit-Paste-Save", icon="PASTEDOWN")
            layout.operator("bebtools.delete_script", text="Delete", icon="TRASH")
            layout.separator()
            layout.operator("bebtools.rename_script", text="Rename", icon="TEXT")
            layout.operator("bebtools.move_to", text="Move", icon="FOLDER_REDIRECT")

class BEBTOOLS_OT_OpenScriptsFolder(Operator):
    bl_idname = "bebtools.open_scripts_folder"
    bl_label = "Open Scripts Folder"
    bl_description = "Open the /scripts/ folder in the file explorer"

    def execute(self, context):
        from .bebtools_utils import SCRIPTS_DIR
        try:
            bpy.ops.wm.path_open(filepath=SCRIPTS_DIR)
            self.report({'INFO'}, f"Opened scripts folder: {SCRIPTS_DIR}")
        except Exception as e:
            self.report({'ERROR'}, f"Error opening scripts folder: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

class BEBTOOLS_OT_ImportScript(Operator):
    bl_idname = "bebtools.import_script"
    bl_label = "Import Script"
    bl_description = "Import Python scripts and their instructions into /scripts/"
    bl_options = {'REGISTER'}

    filter_glob: StringProperty(default="*.py;*.txt", options={'HIDDEN'})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement)
    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from .bebtools_utils import SCRIPTS_DIR
        wm = context.window_manager
        imported = 0
        skipped = 0
        py_files = {}
        txt_files = {}
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            filename, ext = os.path.splitext(file.name)
            if ext.lower() == '.py':
                py_files[filename] = filepath
            elif ext.lower() == '.txt':
                txt_files[filename] = filepath
            else:
                skipped += 1
                print(f"Skipped non-.py/.txt file: {file.name}")
        for py_name, py_path in py_files.items():
            dest_py = os.path.join(SCRIPTS_DIR, f"{py_name}.py")
            if os.path.exists(dest_py):
                self.report({'WARNING'}, f"Script '{py_name}.py' already exists in /scripts/—skipped")
                skipped += 1
                continue
            try:
                import shutil
                shutil.copy2(py_path, dest_py)
                imported += 1
                if py_name in txt_files:
                    dest_txt = os.path.join(SCRIPTS_DIR, f"{py_name}.txt")
                    shutil.copy2(txt_files[py_name], dest_txt)
                else:
                    with open(os.path.join(SCRIPTS_DIR, f"{py_name}.txt"), "w") as f:
                        f.write(f"Instructions for {py_name}\n")
            except Exception as e:
                self.report({'ERROR'}, f"Error importing '{py_name}.py': {str(e)}")
                return {'CANCELLED'}
        for txt_name in txt_files:
            if txt_name not in py_files:
                skipped += 1
                print(f"Skipped {txt_name}.txt—no matching .py file")
        bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=SCRIPTS_DIR)
        wm.bebtools_active_index = -1
        update_info_text(context)
        self.report({'INFO'}, f"Imported {imported} script(s), skipped {skipped} file(s)")
        return {'FINISHED'}

class BEBTOOLS_OT_FolderContextMenu(Operator):
    bl_idname = "bebtools.folder_context_menu"
    bl_label = "Folder Context Menu"
    bl_description = "Show folder options"
    index: bpy.props.IntProperty()

    def invoke(self, context, event):
        wm = context.window_manager
        wm.bebtools_active_index = self.index
        return wm.invoke_popup(self, width=200)

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        op = layout.operator("bebtools.open_folder_contents", text="Open", icon="FILE_FOLDER")
        op.index = self.index
        layout.operator("bebtools.queue_folder", text="Queue Folder", icon="FORWARD")
        if wm.bebtools_edit_mode:
            layout.operator("bebtools.rename_folder", text="Rename", icon="TEXT")
            layout.operator("bebtools.move_folder", text="Move", icon="FOLDER_REDIRECT")
            op = layout.operator("bebtools.delete_folder", text="Delete", icon="TRASH")
            op.index = self.index

class BEBTOOLS_OT_NavigateBack(Operator):
    bl_idname = "bebtools.navigate_back"
    bl_label = "Navigate Back"
    bl_description = "Go back to the parent directory"
    index: bpy.props.IntProperty()

    def execute(self, context):
        wm = context.window_manager
        from .bebtools_utils import SCRIPTS_DIR
        if self.index >= 0 and self.index < len(wm.bebtools_scripts):
            script_item = wm.bebtools_scripts[self.index]
            if script_item.name == "Back":
                parent_path = script_item.path
                get_scripts(parent_path)
                if parent_path != SCRIPTS_DIR:
                    grandparent_path = os.path.dirname(parent_path)
                    back_item = wm.bebtools_scripts.add()
                    back_item.name = "Back"
                    back_item.path = grandparent_path
                    back_item.is_folder = True
                    wm.bebtools_scripts.move(len(wm.bebtools_scripts) - 1, 0)
                wm.bebtools_active_index = -1
                wm.bebtools_current_dir = parent_path
                update_info_text(context)
                self.report({'INFO'}, f"Navigated back to '{parent_path}'")
                return {'FINISHED'}
        self.report({'WARNING'}, "Invalid back navigation")
        return {'CANCELLED'}

class BEBTOOLS_OT_ToggleEditMode(Operator):
    bl_idname = "bebtools.toggle_edit_mode"
    bl_label = "Toggle Edit Mode"
    bl_description = "Enable or disable edit mode"

    def execute(self, context):
        wm = context.window_manager
        wm.bebtools_edit_mode = not wm.bebtools_edit_mode
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}

class BEBTOOLS_OT_ToggleFolderMode(Operator):
    bl_idname = "bebtools.toggle_folder_mode"
    bl_label = "Toggle Folder Mode"
    bl_description = "Enable or disable direct folder opening"

    def execute(self, context):
        wm = context.window_manager
        wm.bebtools_folder_mode = not wm.bebtools_folder_mode
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}

class BEBTOOLS_OT_ImportBlobZip(Operator):
    bl_idname = "bebtools.import_blob_zip"
    bl_label = "Import GitHub Files"
    bl_description = "Import .py and .txt files from GitHub raw URLs in the clipboard into /scripts/"

    def execute(self, context):
        wm = context.window_manager
        clipboard = wm.clipboard.strip()

        # Check if clipboard contains the expected GitHub raw URL prefix
        github_prefix = "https://raw.githubusercontent.com/"
        if not clipboard.startswith(github_prefix):
            # Silently do nothing if the prefix isn’t found
            return {'CANCELLED'}

        # Split the clipboard into individual URLs (assuming newline or space separation)
        urls = [url.strip() for url in clipboard.splitlines() if url.strip()]
        if not urls:
            self.report({'WARNING'}, "No valid URLs found in clipboard")
            return {'CANCELLED'}

        downloaded_files = []

        # Process each URL (expecting up to two: .py and .txt)
        for url in urls[:2]:  # Limit to 2 URLs to handle .py and .txt pair
            if not url.startswith(github_prefix):
                self.report({'WARNING'}, f"Skipping invalid URL: {url}")
                continue

            # Extract filename from URL and decode URL-encoded characters (e.g., %20 to space)
            filename = unquote(os.path.basename(url.split('?')[0]))  # Decode %20 to " "
            if not (filename.endswith('.py') or filename.endswith('.txt')):
                self.report({'WARNING'}, f"Skipping unsupported file type: {filename}")
                continue

            dest_path = os.path.join(SCRIPTS_DIR, filename)

            # Download the file
            try:
                self.report({'INFO'}, f"Downloading: {url}")
                response = requests.get(url, stream=True)
                response.raise_for_status()  # Raise an exception for bad status codes

                # Save the file, overwriting if it exists
                if os.path.exists(dest_path):
                    if os.path.isdir(dest_path):
                        shutil.rmtree(dest_path)
                    else:
                        os.remove(dest_path)

                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_files.append(filename)
            except requests.RequestException as e:
                self.report({'ERROR'}, f"Failed to download {filename}: {str(e)}")
                return {'CANCELLED'}
            except Exception as e:
                self.report({'ERROR'}, f"Error saving {filename}: {str(e)}")
                return {'CANCELLED'}

        if downloaded_files:
            # Refresh the script list
            bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=SCRIPTS_DIR)
            wm.bebtools_active_index = -1
            update_info_text(context)
            self.report({'INFO'}, f"Imported files: {', '.join(downloaded_files)}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No files were downloaded")
            return {'CANCELLED'}

class BEBTOOLS_PT_Panel(Panel):
    bl_label = "Beb.Tools"
    bl_idname = "BEBTOOLS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Beb.Tools"

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        if not wm.bebtools_scripts:
            layout.operator("bebtools.init_scripts", text="Load Scripts")
            wm.bebtools_current_dir = SCRIPTS_DIR
        else:
            parent_row = layout.row(align=True)
            
            left_row = parent_row.row(align=True)
            left_row.alignment = 'LEFT'
            left_row.operator("bebtools.toggle_folder_mode", text="", icon="RESTRICT_SELECT_OFF", depress=wm.bebtools_folder_mode)
            left_row.operator("bebtools.toggle_edit_mode", text="", icon="GREASEPENCIL", depress=wm.bebtools_edit_mode)
            
            center_row = parent_row.row(align=True)
            center_row.prop(wm, "bebtools_search_query", text="", icon="VIEWZOOM", emboss=True)
            
            right_row = parent_row.row(align=True)
            right_row.alignment = 'RIGHT'
            right_row.operator("bebtools.import_script", text="", icon="FILE_FOLDER")
            right_row.operator("bebtools.new_script", text="", icon="FILE_NEW")
            right_row.operator("bebtools.new_folder", text="", icon="NEWFOLDER")
            right_row.operator("bebtools.save_script", text="", icon="FILE_TICK")
            right_row.operator("bebtools.init_scripts", text="", icon="FILE_REFRESH")
            right_row.operator("bebtools.open_scripts_folder", text="", icon="FOLDER_REDIRECT")
            right_row.operator("bebtools.import_blob_zip", text="", icon="PASTEDOWN")

            layout.template_list(
                "BEBTOOLS_UL_ScriptList",
                "bebtools_script_list",
                wm,
                "bebtools_scripts",
                wm,
                "bebtools_active_index",
                rows=10
            )

class BEBTOOLS_UL_QueueList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        op = row.operator("bebtools.queue_context_menu", text=f"{index + 1}. {item.name}", emboss=False)
        op.index = index

class BEBTOOLS_OT_QueueContextMenu(Operator):
    bl_idname = "bebtools.queue_context_menu"
    bl_label = "Queue Context Menu"
    bl_description = "Show queue options"
    index: bpy.props.IntProperty()

    def invoke(self, context, event):
        wm = context.window_manager
        wm.bebtools_queue_index = self.index
        return wm.invoke_popup(self, width=150)

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("bebtools.run_selected", text="Run Selected", icon="PLAY")
        layout.operator("bebtools.multi_run", text="Run All", icon="FRAME_NEXT")
        layout.operator("bebtools.remove_from_queue", text="Remove", icon="REMOVE")
        layout.operator("bebtools.clear_queue", text="Clear", icon="TRASH")

class BEBTOOLS_PT_QueuePanel(Panel):
    bl_label = "Queue"
    bl_idname = "BEBTOOLS_PT_queue_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Beb.Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="FORWARD")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        row = layout.row(align=True)
        row.operator("bebtools.load_queue", text="", icon="FILE_FOLDER")
        row.operator("bebtools.save_queue", text="", icon="FILE_TICK")
        row.prop(wm, "bebtools_selected_queue", text="")
        row.operator("bebtools.load_selected_queue", text="", icon="TRIA_DOWN")
        row.operator("bebtools.delete_queue", text="", icon="TRASH")
        
        box = layout.box()
        box.template_list(
            "BEBTOOLS_UL_QueueList",
            "bebtools_queue_list",
            wm,
            "bebtools_queue",
            wm,
            "bebtools_queue_index",
            rows=5
        )
        row = layout.row(align=True)
        row.operator("bebtools.move_up", text="", icon="TRIA_UP_BAR")
        row.operator("bebtools.move_down", text="", icon="TRIA_DOWN_BAR")
        row.operator("bebtools.multi_run", text="Run All", icon="PLAY")
        row.operator("bebtools.clear_queue", text="", icon="X")

class BEBTOOLS_OT_SearchScripts(Operator):
    bl_idname = "bebtools.search_scripts"
    bl_label = "Search Scripts"
    bl_description = "Search for scripts across all folders and subfolders"

    def execute(self, context):
        wm = context.window_manager
        query = wm.bebtools_search_query.strip().lower()
        
        # If query is empty, restore the current directory
        if not query:
            if wm.bebtools_search_active:
                bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=wm.bebtools_current_dir)
                wm.bebtools_search_active = False
                self.report({'INFO'}, "Returned to folder browsing")
            return {'FINISHED'}

        # Perform recursive search
        wm.bebtools_scripts.clear()
        matches = []
        for root, _, files in os.walk(SCRIPTS_DIR):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    script_name = file[:-3]  # Just the name without .py
                    if query in script_name.lower():
                        full_path = os.path.join(root, file)
                        matches.append((script_name, full_path, False))  # Use script_name only

        # Sort matches alphabetically
        matches.sort(key=lambda x: x[0])

        # Populate script list with results
        for name, path, is_folder in matches:
            item = wm.bebtools_scripts.add()
            item.name = name  # Only the script name, no path
            item.path = path  # Full path still stored for operations
            item.is_folder = is_folder

        wm.bebtools_search_active = True
        wm.bebtools_active_index = -1
        update_info_text(context)
        self.report({'INFO'}, f"Found {len(matches)} script(s) matching '{query}'")
        
        # Redraw the UI
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}

class BEBTOOLS_OT_ClearSearch(Operator):
    bl_idname = "bebtools.clear_search"
    bl_label = "Clear Search"
    bl_description = "Clear the search query and return to folder browsing"

    def execute(self, context):
        wm = context.window_manager
        wm.bebtools_search_query = ""  # Clear the search field
        if wm.bebtools_search_active:
            bpy.ops.bebtools.init_scripts('INVOKE_DEFAULT', directory=wm.bebtools_current_dir)
            wm.bebtools_search_active = False
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return {'FINISHED'}

class BEBTOOLS_PT_InfoPanel(Panel):
    bl_label = ""
    bl_idname = "BEBTOOLS_PT_info_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Beb.Tools"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return wm.bebtools_scripts and wm.bebtools_active_index >= 0

    def draw_header(self, context):
        wm = context.window_manager
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="", icon="QUESTION")
        if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
            script_name = wm.bebtools_scripts[wm.bebtools_active_index].name
            row.label(text=script_name.capitalize())

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.operator("bebtools.edit_instructions", text="", icon="TEXT")
        row.operator("bebtools.save_instructions", text="", icon="FILE_TICK")
        row.operator("bebtools.paste_edit_instructions", text="", icon="PASTEDOWN")
        
        box = layout.box()
        box.template_list(
            "BEBTOOLS_UL_InfoText",
            "bebtools_info_lines",
            wm,
            "bebtools_info_lines",
            wm,
            "bebtools_info_lines_index",
            rows=10
        )

class BEBTOOLS_UL_InfoText(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

classes = (
    BEBTOOLS_UL_ScriptList,
    BEBTOOLS_UL_QueueList,
    BEBTOOLS_UL_InfoText,
    BEBTOOLS_PT_Panel,
    BEBTOOLS_PT_InfoPanel,
    BEBTOOLS_PT_QueuePanel,
    BEBTOOLS_OT_ScriptContextMenu,
    BEBTOOLS_OT_QueueContextMenu,
    BEBTOOLS_OT_NavigateBack,
    BEBTOOLS_OT_FolderContextMenu,
    BEBTOOLS_OT_OpenScriptsFolder,
    BEBTOOLS_OT_ImportScript,
    BEBTOOLS_OT_ToggleEditMode,
    BEBTOOLS_OT_ToggleFolderMode,
    BEBTOOLS_OT_SearchScripts,
    BEBTOOLS_OT_ClearSearch,
    BEBTOOLS_OT_ImportBlobZip,
)