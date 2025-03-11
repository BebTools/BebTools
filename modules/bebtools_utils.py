import bpy
import os

MODULES_DIR = os.path.join(os.path.dirname(__file__), "..", "modules")
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")

def get_scripts(directory=SCRIPTS_DIR, expand=False):
    wm = bpy.context.window_manager
    if not expand:
        wm.bebtools_scripts.clear()
    items = []
    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if os.path.isdir(full_path):
            item = wm.bebtools_scripts.add()
            item.name = filename
            item.path = full_path
            item.is_folder = True
            items.append(item)
        elif filename.endswith(".py") and not filename.startswith("__"):
            item = wm.bebtools_scripts.add()
            item.name = filename[:-3]
            item.path = full_path
            item.is_folder = False
            items.append(item)
    folders = sorted(
        [(item.name, item.path, item.is_folder) for item in wm.bebtools_scripts if item.is_folder and item.name != "Back"],
        key=lambda x: x[0]
    )
    scripts = sorted(
        [(item.name, item.path, item.is_folder) for item in wm.bebtools_scripts if not item.is_folder],
        key=lambda x: x[0]
    )
    wm.bebtools_scripts.clear()
    for item in items:
        if item.name == "Back":
            new_item = wm.bebtools_scripts.add()
            new_item.name = item.name
            new_item.path = item.path
            new_item.is_folder = item.is_folder
    for name, path, is_folder in folders:
        new_item = wm.bebtools_scripts.add()
        new_item.name = name
        new_item.path = path
        new_item.is_folder = is_folder
    for name, path, is_folder in scripts:
        new_item = wm.bebtools_scripts.add()
        new_item.name = name
        new_item.path = path
        new_item.is_folder = is_folder
    print(f"Loaded directory: {directory}, List: {[item.name for item in wm.bebtools_scripts]}")
    return items

def update_info_text(context):
    wm = context.window_manager
    if wm.bebtools_active_index >= 0 and wm.bebtools_active_index < len(wm.bebtools_scripts):
        script_item = wm.bebtools_scripts[wm.bebtools_active_index]
        wm.bebtools_info_lines.clear()
        if script_item.name == "Back":
            item = wm.bebtools_info_lines.add()
            item.name = "Navigate back to parent directory"
        elif script_item.is_folder:
            item = wm.bebtools_info_lines.add()
            item.name = f"Folder: {script_item.name}"
        else:
            script_path = script_item.path
            info_file = os.path.splitext(script_path)[0] + ".txt"
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    for line in f.read().split('\n'):
                        item = wm.bebtools_info_lines.add()
                        item.name = line
            else:
                item = wm.bebtools_info_lines.add()
                item.name = f"No instructions found for '{script_item.name}'."
    else:
        wm.bebtools_info_lines.clear()

def open_or_reuse_text_editor(context, text_block):
    for area in context.screen.areas:
        if area.type == 'TEXT_EDITOR':
            area.spaces.active.text = text_block
            text_block.cursor_set(line=0, character=0)
            area.tag_redraw()
            return
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            with bpy.context.temp_override(area=area):
                bpy.ops.screen.area_split(direction='VERTICAL', factor=0.3)
                new_area = context.screen.areas[-1]
                new_area.type = 'TEXT_EDITOR'
                new_area.spaces.active.text = text_block
                text_block.cursor_set(line=0, character=0)
            break

classes = ()