import bpy
from . import utilities

from pprint import pprint

undo_key_map_instance = None


def get_ue2rigify_history():
    history = bpy.context.window_manager.ue2rigify.get('history')
    if not history:
        history = []

    return history


def get_blender_history():
    history = []

    for operator in bpy.context.window_manager.operators:
        history.append(operator.name)

    return history


def get_history_before_mode_change(ue2rigify_history, blender_history):
    history = []
    for index, item in enumerate(blender_history):
        if ue2rigify_history[index] != item:
            break
        else:
            history.append(item)
    return history


def get_history_after_mode_change(pre_history, blender_history):
    return blender_history[len(pre_history)-1:]


def add_latest_history(ue2rigify_history, blender_history, properties):
    if properties.selected_mode == properties.source_mode:
        return blender_history
    else:
        pre_history = get_history_before_mode_change(ue2rigify_history, blender_history)
        post_history = get_history_after_mode_change(ue2rigify_history, blender_history)
        return pre_history + [properties.selected_mode] + post_history


def add_mode_change_to_history(properties):
    properties.freeze_history = True
    blender_history = [operator.name for operator in bpy.context.window_manager.operators]
    bpy.context.window_manager.ue2rigify['history'] = blender_history + [properties.selected_mode]
    properties.freeze_history = False


@bpy.app.handlers.persistent
def update_history(*args):
    properties = bpy.context.window_manager.ue2rigify

    if not properties.freeze_history:
        ue2rigify_history = get_ue2rigify_history()
        blender_history = get_blender_history()

        pprint(blender_history)
        ue2rigify_history = add_latest_history(ue2rigify_history, blender_history, properties)
        pprint(ue2rigify_history)

        bpy.context.window_manager.ue2rigify['history'] = ue2rigify_history


def undo(properties):
    pass


# bpy.context.window_manager.keyconfigs['blender'].keymaps['Screen'].keymap_items['ed.undo'].active


def create_undo_hot_key():
    """
    This function creates a temporary undo hot key for ue2rigify and saves the keymap to be remove later.
    """
    blender_undo = bpy.context.window_manager.keyconfigs['blender'].keymaps['Screen'].keymap_items['ed.undo']

    # get an existing key map or create a new one
    key_maps = bpy.context.window_manager.keyconfigs.addon.keymaps
    key_map = key_maps.get('Screen')
    if not key_map:
        key_map = key_maps.new(name='Screen')

    # add a key map instance with a hot key that invokes a pie menu
    undo_key_map_instance = key_map.keymap_items.new(
        'ue2rigify.undo',
        blender_undo.type,
        blender_undo.value,
        alt=blender_undo.alt
    )


def remove_undo_hot_key():
    if undo_key_map_instance:
        key_maps = bpy.context.window_manager.keyconfigs.addon.keymaps
        key_map = key_maps.get('Screen')
        if not key_map:
            key_map.keymap_items.remove(undo_key_map_instance)
            undo_key_map_instance = None
