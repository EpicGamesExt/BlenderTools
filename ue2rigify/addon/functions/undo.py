import bpy
from . import utilities

from pprint import pprint


def get_ue2rigify_history():
    history = bpy.context.window_manager.ue2rigify.history.get('ue2rigify_history')
    if not history:
        history = []

    return history


def get_blender_history():
    history = []

    for operator in bpy.context.window_manager.operators:
        history.append(operator.name)

    return history


def get_key_map(key_maps, category, operator):
    key_map = key_maps.get(category)
    if not key_map:
        return None

    return key_map.keymap_items.get(operator)


def get_history_before_mode_change(ue2rigify_history, blender_history):
    history = []
    for index, item in enumerate(blender_history):
        if ue2rigify_history[index] != item:
            break
        else:
            history.append(item)
    return history


def get_history_after_mode_change(pre_history, blender_history):
    return blender_history[len(pre_history) - 1:]


def set_undo_key_values(key_maps):
    undo_key = get_key_map(key_maps, 'Screen', 'ed.undo')
    properties = bpy.context.window_manager.ue2rigify

    if undo_key:
        properties.undo_key_values['type'] = undo_key.type
        properties.undo_key_values['value'] = undo_key.value
        properties.undo_key_values['any'] = undo_key.any
        properties.undo_key_values['shift'] = undo_key.shift
        properties.undo_key_values['ctrl'] = undo_key.ctrl
        properties.undo_key_values['alt'] = undo_key.alt
        properties.undo_key_values['oskey'] = undo_key.oskey
        properties.undo_key_values['key_modifier'] = undo_key.key_modifier
        properties.undo_key_values['repeat'] = undo_key.repeat


def add_latest_history(ue2rigify_history, blender_history, properties):
    # if properties.selected_mode == properties.source_mode:
    #     return blender_history
    # else:
    #     pre_history = get_history_before_mode_change(ue2rigify_history, blender_history)
    #     post_history = get_history_after_mode_change(ue2rigify_history, blender_history)
    #     if len(post_history) > 1:
    #         return pre_history + [properties.selected_mode] + post_history
    #     else:
    #         return ue2rigify_history

    # bpy.context.preferences.edit.undo_steps
    history = bpy.context.window_manager.ue2rigify['history']


def add_mode_change_to_history(properties):
    blender_history = [operator.name for operator in bpy.context.window_manager.operators]
    # bpy.context.window_manager.ue2rigify['history'] = blender_history + [properties.selected_mode]
    ue2rigify_history = bpy.context.window_manager.ue2rigify.history.get('ue2rigify_history')
    if ue2rigify_history:
        bpy.context.window_manager.ue2rigify.history['ue2rigify_history'] = ue2rigify_history + [properties.selected_mode]


@bpy.app.handlers.persistent
def update_history(*args):
    properties = bpy.context.window_manager.ue2rigify

    if not properties.freeze_history:
        previous_history = bpy.context.window_manager.ue2rigify.history.get('previous_history')
        ue2rigify_history = get_ue2rigify_history()
        blender_history = get_blender_history()

        if blender_history and previous_history != blender_history:
            ue2rigify_history = ue2rigify_history + [blender_history[-1]]
            print(blender_history)
            print(ue2rigify_history)

            bpy.context.window_manager.ue2rigify.history['ue2rigify_history'] = ue2rigify_history
            bpy.context.window_manager.ue2rigify.history['previous_history'] = blender_history


@bpy.app.handlers.persistent
def undo(*args):
    ue2rigify_history = bpy.context.window_manager.ue2rigify.history['ue2rigify_history']
    top_item = ue2rigify_history.pop()
    next_item = ue2rigify_history.pop()
    print(item)
    print(ue2rigify_history)
    if next_item not in utilities.get_modes():
        bpy.ops.ed.undo()
        bpy.context.window_manager.ue2rigify.history['ue2rigify_history'] = ue2rigify_history


def create_undo_hot_key(key_maps, id_name, properties):
    """
    This function creates a temporary undo hot key for ue2rigify and saves the keymap to be remove later.
    """
    # get an existing key map or create a new one
    key_map = key_maps.get('Screen')
    if not key_map:
        key_map = key_maps.new(name='Screen')

    if not key_map.keymap_items.get(id_name):
        key_map.keymap_items.new(
            id_name,
            type=properties.undo_key_values['type'],
            value=properties.undo_key_values['value'],
            any=properties.undo_key_values['any'],
            shift=properties.undo_key_values['shift'],
            ctrl=properties.undo_key_values['ctrl'],
            alt=properties.undo_key_values['alt'],
            oskey=properties.undo_key_values['oskey'],
            key_modifier=properties.undo_key_values['key_modifier'],
            repeat=properties.undo_key_values['repeat']
        )


def remove_undo_hot_key(key_maps, id_name):
    key_map = key_maps.get('Screen')
    if key_map:
        undo_key_map_instance = key_map.keymap_items.get(id_name)
        if undo_key_map_instance:
            key_map.keymap_items.remove(undo_key_map_instance)


def modify_undo_key(properties):
    blender_key_maps = bpy.context.window_manager.keyconfigs['blender'].keymaps
    addon_key_maps = bpy.context.window_manager.keyconfigs.addon.keymaps

    set_undo_key_values(blender_key_maps)

    if properties.selected_mode == properties.source_mode:
        remove_undo_hot_key(addon_key_maps, 'ue2rigify.undo')
        create_undo_hot_key(blender_key_maps, 'ed.undo', properties)
    else:
        remove_undo_hot_key(blender_key_maps, 'ed.undo')
        create_undo_hot_key(addon_key_maps, 'ue2rigify.undo', properties)
