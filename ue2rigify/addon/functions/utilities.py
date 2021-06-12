# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import re
from . import scene, templates
from mathutils import Vector, Quaternion

addon_key_maps = []
pie_menu_classes = []


def get_modes():
    """
    This function gets all the ue2rigify modes
    """
    properties = bpy.context.window_manager.ue2rigify
    return [
        properties.source_mode,
        properties.metarig_mode,
        properties.fk_to_source_mode,
        properties.source_to_deform_mode,
        properties.control_mode
    ]


def get_picker_object():
    """
    This function gets or creates a new picker object if needed.

    :return object: The blender picker object.
    """
    properties = bpy.context.window_manager.ue2rigify
    picker_object = bpy.data.objects.get(properties.picker_name)
    if not picker_object:
        picker_object = bpy.data.objects.new(properties.picker_name, None)
        picker_object.constraints.new('COPY_TRANSFORMS')

    return picker_object


def get_action_names(rig_object, all_actions=True):
    """
    This function gets a list of action names from the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param bool all_actions: Whether to get all action names, or just the un-muted actions.
    :return list: A list of action names.
    """
    action_names = []
    if rig_object.animation_data:
        for nla_track in rig_object.animation_data.nla_tracks:
            # get all the action names if the all flag is set
            if all_actions:
                for strip in nla_track.strips:
                    if strip.action:
                        action_names.append(strip.action.name)

            # otherwise get only the un-muted actions
            else:
                if not nla_track.mute:
                    for strip in nla_track.strips:
                        if strip.action:
                            action_names.append(strip.action.name)
    return action_names


def get_object_transforms(scene_object):
    """
    This function gets the transforms provided object.
    :param object scene_object: An object.
    :return dict: A dictionary of object transforms
    """
    if scene_object:
        return {
            'location': scene_object.location,
            'rotation_quaternion': scene_object.rotation_quaternion,
            'rotation_euler': scene_object.rotation_euler,
            'scale': scene_object.scale
        }


def get_actions(scene_object):
    """
    This function gets all actions on the given object.

    :param object scene_object: A blender object.
    :return list: A list of actions.
    """
    actions = []
    if scene_object:
        if scene_object.animation_data:
            if scene_object.animation_data.action:
                actions.append(scene_object.animation_data.action)

            for nla_track in scene_object.animation_data.nla_tracks:
                for strip in nla_track.strips:
                    if strip.action and strip.action not in actions:
                        actions.append(strip.action)

    return actions


def get_all_action_attributes(rig_object):
    """
    This function gets all the action attributes on the provided rig.

    :param object rig_object: A object of type armature with animation data.
    :return dict: The action attributes on the provided rig.
    """
    attributes = {}
    if rig_object.animation_data:
        for nla_track in rig_object.animation_data.nla_tracks:
            for strip in nla_track.strips:
                if strip.action:
                    attributes[strip.action.name] = {
                        'mute': nla_track.mute,
                        'is_solo': nla_track.is_solo,
                        'frame_start': strip.frame_start,
                        'frame_end': strip.frame_end
                    }
    return attributes


def get_action_transform_offset(action, bone_name=None):
    """
    This function gets the amount the first frame of the given action is offset from the applied
    transforms.

    :param object action: A action object.
    :param str bone_name: If getting a bones transform offset, then provide the bone name.
    :return dict: A dictionary of the transform offsets.
    """
    default_transforms = {
        'location': [0, 0, 0],
        'rotation_euler': [0, 0, 0],
        'rotation_quaternion': [0, 0, 0, 1],
        'scale': [1, 1, 1]
    }

    offset = default_transforms

    # get each transform value for each of the data paths
    for fcurve in action.fcurves:
        for data_path in offset.keys():
            if fcurve.data_path == data_path:
                for keyframe_point in fcurve.keyframe_points:
                    if keyframe_point.co[0] == action.frame_range[0]:
                        offset[data_path][fcurve.array_index] = keyframe_point.co[1]

    # zero out any transform that are still equal to their default value
    for data_path, transform in offset.items():
        if default_transforms[data_path] == [round(value, 5) for value in transform]:
            zero_transform = []
            for value in transform:
                zero_transform.append(0)

            offset[data_path] = zero_transform

    return offset


def get_matrix_data(matrix_object):
    """
    This function destructures a matrix object into a list of lists.

    :param object matrix_object:
    :return list: A list of lists that represents a matrix.
    """
    matrix_data = []
    for column in matrix_object.col:
        col_values = []
        for col_value in column:
            col_values.append(col_value)

        matrix_data.append(col_values)

    return matrix_data


def get_array_data(array_object):
    """
    This function destructures any of the array object data types into a list.

    :param object array_object: A object array such as Color, Euler, Quaternion, Vector.
    :return list: A list of values.
    """
    array_data = []
    for value in array_object:
        array_data.append(value)

    return array_data


def get_property_collections_data(collections):
    """
    This function goes through each of the givens collections and return their data as a list of dictionaries.

    :param list collections: A list a property groups.
    :return list: A list of dictionaries that contains the given property group values.
    """
    collections_data = []
    for collection in collections:
        property_collection = {}
        for collection_attribute in dir(collection):
            collection_value = getattr(collection, collection_attribute)
            if collection_value is not None and not collection_attribute.startswith('__'):
                if type(collection_value) in [str, bool, int, float]:
                    property_collection[collection_attribute] = collection_value

                if type(collection_value) == bpy.types.Object:
                    property_collection[collection_attribute] = collection_value.name
        collections_data.append(property_collection)

    return collections_data


def set_action_transform_offsets(action, offset, operation, bone_name=None):
    """
    This function modifies each keyframe in the given action by applying the provided offset.

    :param object action: A action object.
    :param dict offset: A dictionary of the transform offsets.
    :param str operation: Which operator to use; 'ADD' or 'SUBTRACT'.
    :param str bone_name: If getting a bones transform offset, then provide the bone name.
    """
    data_paths = [
        'location',
        'rotation_euler',
        'rotation_quaternion',
        'scale'
    ]

    # if this is a bone format the data path for a bone
    if bone_name:
        data_paths = [f'pose.bones["{bone_name}"].{data_path}' for data_path in data_paths]

    # apply the offset to each fcurve point and handle
    for fcurve in action.fcurves:
        for data_path in data_paths:
            if fcurve.data_path == data_path:
                for keyframe_point in fcurve.keyframe_points:
                    transform_offset = offset[data_path.split('"].')[-1]][fcurve.array_index]
                    if operation == 'ADD':
                        keyframe_point.co[1] = keyframe_point.co[1] + transform_offset
                        keyframe_point.handle_left[1] = keyframe_point.handle_left[1] + transform_offset
                        keyframe_point.handle_right[1] = keyframe_point.handle_right[1] + transform_offset

                    if operation == 'SUBTRACT':
                        keyframe_point.co[1] = keyframe_point.co[1] - transform_offset
                        keyframe_point.handle_left[1] = keyframe_point.handle_left[1] - transform_offset
                        keyframe_point.handle_right[1] = keyframe_point.handle_right[1] - transform_offset


def set_object_transforms(scene_object, transform_values):
    """
    This function sets the transforms of the provided object.
    :param object scene_object: An object.
    :param dict transform_values: A dictionary of object transforms.
    """
    if scene_object and transform_values:
        scene_object.location = transform_values['location']
        scene_object.rotation_quaternion = transform_values['rotation_quaternion']
        scene_object.rotation_euler = transform_values['rotation_euler']
        scene_object.scale = transform_values['scale']


def set_solo_track_values(rig_object, value):
    """
    This function sets all is_solo attributes on the nla tracks of the provided object to the given value.

    :param object rig_object: A object of type armature with animation data.
    :param bool value: Whether the tracks should be solo or not.
    """
    if rig_object:
        if rig_object.animation_data:
            for nla_track in rig_object.animation_data.nla_tracks:
                if value:
                    nla_track.is_solo = value


def set_all_action_attributes(rig_object, attributes):
    """
    This function sets the action attributes to the provided values.

    :param object rig_object: A object of type armature with animation data.
    :param dict attributes: The values of the of the action attributes.
    """
    if rig_object.animation_data:
        for nla_track in rig_object.animation_data.nla_tracks:
            for strip in nla_track.strips:
                if strip.action:
                    action_attributes = attributes.get(strip.action.name)
                    if action_attributes:
                        nla_track.mute = action_attributes['mute']
                        strip.frame_start = action_attributes['frame_start']
                        strip.frame_end = action_attributes['frame_end']

                        # only set the solo value if it is true
                        if action_attributes['is_solo']:
                            nla_track.is_solo = action_attributes['is_solo']


def set_to_title(text):
    """
    This function takes text and converts it to titles.

    :param str text: The original text to convert to a title.
    :return str: The new title text.
    """
    return ' '.join([word.capitalize() for word in text.lower().split('_')])


def set_to_bl_idname(text):
    """
    This function takes text and converts it into a format that blender excepts as a bl_idname.

    :param str text: The original text to convert to a bl_idname.
    :return str: The new bl_idname text.
    """
    # remove non-alphanumeric characters
    class_name = re.sub(r'\W+', '', text)
    return f"{class_name}"


def set_active_properties_panel(tab):
    """
    This function set the provided properties tab to the active tab on the current screen.

    :param str tab: The tab identifier.
    """
    for area in bpy.context.screen.areas:
        if area.ui_type == 'PROPERTIES':
            for space in area.spaces:
                if space.type == 'PROPERTIES':
                    try:
                        space.context = tab
                    except TypeError:
                        pass


def set_relationship_lines_visibility(show_lines):
    """
    This function set the visibility of the object relationship lines in the viewport.

    :param bool show_lines: Whether or not to show the relationship lines.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_relationship_lines = show_lines


def set_rig_color(rig_object, theme, show):
    """
    This function get or creates a new bones group of all the rig bones of the provided rig object and sets the group
    to the provided theme.

    :param object rig_object: A blender object that contains armature data.
    :param str theme: The name of a bone group color theme.
    :param bool show: Whether or not to show the bone group colors.
    """
    # get or create a new bone group
    bone_group = rig_object.pose.bone_groups.get(rig_object.name)
    if not bone_group:
        bone_group = rig_object.pose.bone_groups.new(name=rig_object.name)

    # set the bone groups color theme
    bone_group.color_set = theme

    # set whether the bone group colors are visible
    bpy.context.object.data.show_group_colors = show

    # either add the rig object's bones to the group or remove the group
    if show:
        for bone in rig_object.pose.bones:
            bone.bone_group = bone_group
    else:
        rig_object.pose.bone_groups.remove(bone_group)


# TODO implement a bunch of functions so some of this logic can be reused
def set_viewport_settings(viewport_settings, properties):
    """
    This function sets the viewport settings and object settings to the values provided in the viewport_settings and
    saves a dictionary of the previous settings in the addon's properties.

    :param dict viewport_settings: A dictionary of viewport and object settings.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    if viewport_settings:
        # switch to object mode and deselect everything
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # apply the setting to each rig object in the editing settings and save its previous state
        for rig_object_name, rig_object_settings in viewport_settings.items():
            previous_settings = {}
            rig_object = bpy.data.objects.get(rig_object_name)

            if rig_object:
                # make the object the active object
                bpy.context.view_layer.objects.active = rig_object

                # set object selection
                previous_settings['selected'] = rig_object.select_get()
                rig_object.select_set(rig_object_settings['selected'])

                # set if object is hidden or not unless it is source mode
                previous_settings['hidden'] = rig_object.hide_get()
                if rig_object.name == properties.source_rig_name and properties.selected_mode == properties.source_mode:
                    rig_object.hide_set(False)
                else:
                    rig_object.hide_set(rig_object_settings['hidden'])

                # set the objects mode
                previous_settings['mode'] = bpy.context.mode
                if bpy.context.mode != rig_object_settings['mode']:
                    bpy.ops.object.mode_set(mode=rig_object_settings['mode'])
                if rig_object_settings['mode'] == 'POSE':
                    bpy.ops.pose.select_all(action='DESELECT')

                # set the objects pose position
                previous_settings['pose_position'] = bpy.context.object.data.pose_position
                bpy.context.object.data.pose_position = rig_object_settings['pose_position']

                # set objects display type i.e. 'WIRE', 'TEXTURED', etc.
                previous_settings['display_type'] = bpy.context.object.display_type
                bpy.context.object.display_type = rig_object_settings['display_type']

                # show names on the object and its bones
                previous_settings['show_names'] = bpy.context.object.data.show_names
                bpy.context.object.data.show_names = rig_object_settings['show_names']

                # show the object in front of other occluding objects
                previous_settings['show_in_front'] = bpy.context.object.show_in_front
                bpy.context.object.show_in_front = rig_object_settings['show_in_front']

                # mirror the bone positions on the x axis
                previous_settings['use_mirror_x'] = bpy.context.object.data.use_mirror_x
                bpy.context.object.data.use_mirror_x = rig_object_settings['use_mirror_x']

                # enable or disable snapping
                previous_settings['use_snap'] = bpy.context.scene.tool_settings.use_snap
                bpy.context.scene.tool_settings.use_snap = rig_object_settings['use_snap']

                # set the type of elements to snap to
                previous_settings['snap_elements'] = bpy.context.scene.tool_settings.snap_elements
                bpy.context.scene.tool_settings.snap_elements = rig_object_settings['snap_elements']

                # show or hidden relationship lines
                previous_settings['relationship_lines'] = True
                set_relationship_lines_visibility(rig_object_settings['relationship_lines'])

                # hide the rig objects child meshes
                previous_settings['hide_rig_mesh'] = False
                for child in rig_object.children:
                    child.hide_set(rig_object_settings['hide_rig_mesh'])

                # set a custom bone shape for all the bones
                previous_settings['custom_bone_shape'] = False
                if rig_object_settings['custom_bone_shape']:
                    # set a give the rig a custom color
                    set_rig_color(rig_object, 'THEME01', True)

                    display_object = get_picker_object()
                    for bone in rig_object.pose.bones:
                        display_object.empty_display_type = 'SPHERE'
                        bone.custom_shape = display_object
                        bone.custom_shape_scale = 0.1

                # remove custom bone shapes from all the bones
                if not rig_object_settings['custom_bone_shape']:
                    if rig_object.name != properties.control_rig_name:

                        # remove the custom rig color
                        set_rig_color(rig_object, 'THEME01', False)
                        for bone in rig_object.pose.bones:
                            bone.custom_shape = None
                            bone.custom_shape_scale = 1

                # set the visible bone layers
                if rig_object_settings.get('visible_bone_layers'):
                    visible_bone_layers = []
                    for index, layer in enumerate(bpy.context.object.data.layers):
                        visible_bone_layers.append(layer)
                        if index in rig_object_settings['visible_bone_layers']:
                            bpy.context.object.data.layers[index] = True
                        else:
                            bpy.context.object.data.layers[index] = False
                    previous_settings['visible_bone_layers'] = visible_bone_layers

                # store the previous viewport values in a dictionary in the tool properties
                bpy.context.window_manager.ue2rigify.previous_viewport_settings[rig_object_name] = previous_settings


def set_property_group_value(property_group, attribute, value):
    """
    This function sets the given attribute and value in a property group.

    :param object property_group: A group of properties.
    :param str attribute: The name of the attribute to set.
    :param value: Any value
    """
    try:
        # change the value from a string name to an object for the target parameter
        if attribute == 'target':
            value = bpy.data.objects.get(value)

        # set the constraint attribute to the saved value
        setattr(property_group, attribute, value)

    except AttributeError as error:
        if 'read-only' not in str(error):
            raise AttributeError(error)


def set_collection(collection, collections_data):
    """
    This function creates and sets the collection data on the given collection object.

    :param object collection: A collection object
    :param dict collections_data: A dictionary of collection attributes and values.
    """
    for index, collection_data in enumerate(collections_data):
        collection.new()
        for collection_attribute, collection_value in collection_data.items():
            set_property_group_value(
                collection[index],
                collection_attribute,
                collection_value
            )


def remove_nla_tracks(nla_tracks):
    """
    This function removes all nla tracks from the given nla_tracks.

    :param object nla_tracks: A object the contains nla data.
    """
    for nla_track in nla_tracks:
        nla_tracks.remove(nla_track)


def remove_picker_object():
    """
    This function removes the picker object.
    """
    properties = bpy.context.window_manager.ue2rigify
    picker_object = bpy.data.objects.get(properties.picker_name)
    if picker_object:
        bpy.data.objects.remove(picker_object)


def remove_pie_menu_hot_keys():
    """
    This function removes all the added the pie menu hot keys.
    """
    # unregister all the pie menu classes
    for pie_menu_class in pie_menu_classes:
        bpy.utils.unregister_class(pie_menu_class)

    # remove all the added key maps
    for key_map in addon_key_maps:
        # remove all the key map instances in each key map
        for key_map_instance in key_map.keymap_items:
            key_map.keymap_items.remove(key_map_instance)

        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(key_map)

    # clear the lists of references to the pie menu classes and key maps
    pie_menu_classes.clear()
    addon_key_maps.clear()


def create_pie_menu_hot_key(pie_menu_class, key, category, alt=True):
    """
    This function creates the pie menu hot keys and saves the keymap to be remove later.

    :param class pie_menu_class: A reference to the pie menu class.
    :param str key: The blender identifier for which key to use.
    :param str category: The category where the keymap will be created in preferences > keymaps
    :param bool alt: Whether or not to use the alt key.
    """
    if pie_menu_class not in pie_menu_classes:
        # register the new pie menu
        bpy.utils.register_class(pie_menu_class)

        # get an existing key map or create a new one
        key_maps = bpy.context.window_manager.keyconfigs.addon.keymaps
        key_map = key_maps.get(category)
        if not key_map:
            key_map = key_maps.new(name=category)

        # add a key map instance with a hot key that invokes a pie menu
        key_map_instance = key_map.keymap_items.new('wm.call_menu_pie', key, 'PRESS', alt=alt)

        # specify which pie menu to invoke
        key_map_instance.properties.name = pie_menu_class.bl_idname

        # save the references to pie menu class and key map so they can be deleted later
        pie_menu_classes.append(pie_menu_class)
        addon_key_maps.append(key_map)


def operator_on_object_in_mode(operator, operated_on_object, mode):
    """
    This a function that wraps operators by getting the current context, doing the operation on an object in a mode,
    then restores the context back to its previous state.

    :param lambda operator: A blender operator function reference.
    :param object operated_on_object: The blender object that to preform the operation on.
    :param str mode: The mode to to preform the action in.
    """
    # get the current context
    current_mode = bpy.context.mode.split('_')[0]

    current_active_object = bpy.context.view_layer.objects.active
    operated_on_object_hidden = operated_on_object.hide_get()
    operated_on_object_selected = operated_on_object.select_get()
    current_frame = bpy.context.scene.frame_current

    # set the context to selected in the right mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    operated_on_object.hide_set(False)
    operated_on_object.select_set(True)
    bpy.context.view_layer.objects.active = operated_on_object
    bpy.ops.object.mode_set(mode=mode)

    # run the operator
    operator()

    # restore the previous context
    bpy.ops.object.mode_set(mode=current_mode)
    operated_on_object.hide_set(operated_on_object_hidden)
    operated_on_object.select_set(operated_on_object_selected)

    bpy.context.view_layer.objects.active = current_active_object
    bpy.context.scene.frame_current = current_frame


def clean_nla_tracks(rig_object, action):
    """
    This function removes any nla tracks that have a action that matches the provided action. Also it removes
    any nla tracks that have actions in their strips that match other actions, or have no strips.

    :param object rig_object: A object of type armature with animation data.
    :param object action: A action object.
    """
    if rig_object.animation_data:
        for nla_track in rig_object.animation_data.nla_tracks:
            # remove any nla tracks that don't have strips
            if len(nla_track.strips) == 0:
                rig_object.animation_data.nla_tracks.remove(nla_track)
            else:
                for strip in nla_track.strips:
                    # remove nla strips if its action matches the active action duplicate actions
                    if strip.action == action:
                        rig_object.animation_data.nla_tracks.remove(nla_track)

                    # remove nla strips with duplicate actions
                    if strip.action:
                        action_names = get_action_names(rig_object)
                        if action_names.count(strip.action.name) > 1:
                            rig_object.animation_data.nla_tracks.remove(nla_track)


def stash_animation_data(rig_object):
    """
    This function stashes the active action on an object into its nla strips.

    :param object rig_object: A object of type armature with animation data.
    """
    if rig_object.animation_data:
        # if there is an active action on the rig object
        active_action = rig_object.animation_data.action

        attributes = get_all_action_attributes(rig_object)

        # remove any nla tracks that have the active action, have duplicate names, or no strips
        clean_nla_tracks(rig_object, active_action)

        if active_action:
            # create a new nla track
            nla_track = rig_object.animation_data.nla_tracks.new()
            nla_track.name = active_action.name

            # create a strip with the active action as the strip action
            nla_track.strips.new(
                name=active_action.name,
                start=1,
                action=rig_object.animation_data.action
            )

        set_all_action_attributes(rig_object, attributes)


def clear_object_transforms(scene_object):
    """
    This function clears the transforms of the provided object to zero.
    :param object scene_object: An object.
    """
    if scene_object:
        scene_object.location = Vector((0, 0, 0))
        scene_object.rotation_quaternion = Quaternion((0, 0, 0), 1)
        scene_object.rotation_euler = Vector((0, 0, 0))
        scene_object.scale = Vector((1, 1, 1))

        scene_object.select_set(True)
        bpy.ops.object.visual_transform_apply()


def clear_pose_location():
    """
    This function selects all pose pose bones and sets there zeros out there locations.
    """
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.loc_clear()


def validate_source_rig_object(properties):
    """
    This function checks to see if the selected source rig is an object with armature data.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True or False depending on whether the selected source rig is an object with armature data.
    """
    # check if rigify is enabled
    rigify = bpy.context.preferences.addons.get('rigify')
    if rigify:
        # check if the source rig is the right type
        source_rig_object = bpy.data.objects.get(properties.source_rig_name)
        is_armature = False

        if source_rig_object:
            if source_rig_object.type == 'ARMATURE':
                is_armature = True

        return is_armature
    else:
        return False


def restore_viewport_settings():
    """
    This function restores the previous viewport and object settings.
    """
    properties = bpy.context.window_manager.ue2rigify
    previous_viewport_settings = properties.previous_viewport_settings
    set_viewport_settings(previous_viewport_settings, properties)
    bpy.context.window_manager.ue2rigify.previous_viewport_settings.clear()


def collapse_collections_in_outliner():
    """
    This function collapses the collections in any outliner region on the current screen.
    """
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'OUTLINER':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        if hasattr(area, 'spaces'):
                            for space in area.spaces:
                                if hasattr(space, 'display_mode'):
                                    if space.display_mode == 'VIEW_LAYER':
                                        override = {'window': window, 'screen': screen, 'area': area, 'region': region}
                                        bpy.ops.outliner.expanded_toggle(override)
                                        bpy.ops.outliner.expanded_toggle(override)
                                        break


def focus_on_selected():
    """
    This function focuses any 3D view region on the current screen to the selected object.
    """
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {'window': window, 'screen': screen, 'area': area, 'region': region}
                        bpy.ops.view3d.view_selected(override)


def show_bone_setting(bone_name, tab):
    """
    This function shows the user what bone is causing the rigify type error.

    :param str bone_name: The name of the bone to show.
    :param str tab: The tab identifier.
    """
    properties = bpy.context.window_manager.ue2rigify

    # set tool mode to edit metarig mode
    properties.selected_mode = properties.metarig_mode

    # get the metarig
    metarig_object = bpy.data.objects.get(properties.meta_rig_name)

    if metarig_object:
        # switch to pose mode and deselect everything
        if bpy.context.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        bone = metarig_object.data.bones.get(bone_name)
        if bone:
            bone.select = True
            metarig_object.data.bones.active = bone

            focus_on_selected()

            set_active_properties_panel(tab)


def report_error(error_header, error_message, confirm_message=None, clean_up_action=None, width=500):
    """
    This function dynamically defines an operator class with a properties dialog to report error messages to the user.

    :param str error_header: The title of the error in the modal header.
    :param str error_message: The body text with the error message.
    :param str confirm_message: An optional confirm message if the user would like to let the clean up action fix the
    issue.
    :param lambda clean_up_action: An optional function to be run to fix the issue if the user confirms.
    :param int width: The width of the modal.
    """
    class_name = 'ReportError'
    error_class = object

    def execute(self, context):
        if clean_up_action:
            clean_up_action()
        bpy.utils.unregister_class(error_class)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=width)

    def draw(self, context):
        layout = self.layout
        for line in error_message.split('\n'):
            row = layout.row()
            row.label(text=line)

        # TODO
        layout.row()
        layout.row()
        layout.row()

        if confirm_message:
            for line in confirm_message.split('\n'):
                row = layout.row()
                row.label(text=line)

    error_class = type(
        class_name,
        (bpy.types.Operator,),
        {
            'bl_idname': 'wm.report_error',
            'bl_label': error_header,
            'execute': execute,
            'invoke': invoke,
            'draw': draw
        }
    )
    bpy.utils.register_class(error_class)
    bpy.ops.wm.report_error('INVOKE_DEFAULT')


def report_rigify_error(error):
    """
    This function reports a rigify error to the user.

    :param str error: The error message.
    """
    # define the error message parameters
    error_header = 'Rigify Error:'
    error_message = error.replace('Error: RIGIFY ERROR: ', '')
    parsed_bone_name = error_message.replace("Bone '", '').split("'")
    confirm_message = None
    def show_error(): return None

    # if a bone name can be parsed from the rigify error message, assign the show error function and confirmation
    if len(parsed_bone_name) > 1:
        confirm_message = 'Click "OK" to see what is causing the issue.'
        def show_error(): return show_bone_setting(parsed_bone_name[0], 'BONE')

    report_error(error_header, error_message, confirm_message, show_error, width=600)


def report_missing_bone_error(link, socket_direction):
    """
    This function reports an error to the user if the scene is missing a bone that is listed in the node tree.

    :param dict link: A dictionary with link attributes.
    :param str socket_direction: A socket direction either 'from_socket' or 'to_socket'.
    :return:
    """
    properties = bpy.context.window_manager.ue2rigify

    # get the bone name and node name from the link
    bone_name = link.get(socket_direction)

    if socket_direction == 'from_socket':
        node_name = link.get('from_node')
    else:
        node_name = link.get('to_node')

    # get the rig name based on the current mode and socket type
    rig_name = ''
    if properties.selected_mode == properties.fk_to_source_mode:
        if socket_direction == 'from_socket':
            rig_name = properties.control_rig_name
        else:
            rig_name = properties.source_rig_name

    if properties.selected_mode == properties.source_to_deform_mode:
        if socket_direction == 'from_socket':
            rig_name = properties.source_rig_name
        else:
            rig_name = properties.control_rig_name

    # define the error message parameters
    error_header = 'MISSING BONE ERROR:'
    error_message = (
        f'You have a bone socket "{bone_name}" in your node "{node_name}", but your rig '
        f'"{rig_name}" does not have a bone named "{bone_name}".'
    )

    confirm_message = f'Click "OK" to remove the socket "{bone_name}" from node "{node_name}"'
    def remove_socket(): return scene.remove_missing_bone_socket(node_name, bone_name, properties)

    report_error(error_header, error_message, confirm_message, remove_socket, width=700)


def source_rig_picker_update(self=None, context=None):
    """
    This function is called every time the source rig picker value updates. It updates the available modes
    in the mode selection and sets the picker object to have a fake user so it won't get deleted when the
    file is closed.

    :param object self: This is a reference to the class this functions in appended to.
    :param object context: The context of the object this function is appended to.
    """
    scene.switch_modes()
    picker_object = get_picker_object()
    picker_object.use_fake_user = True


def save_control_mode_context(properties):
    """
    This function saves the current context of control mode to the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    control_mode_context = {}

    # get the control rig
    control_rig = bpy.data.objects.get(properties.control_rig_name)
    if control_rig:
        control_rig_context = {}

        # save the active action on the control rig
        if control_rig.animation_data:
            if control_rig.animation_data.action:
                control_rig_context['active_action'] = control_rig.animation_data.action.name

        # save the current property values on each bone
        for bone in control_rig.pose.bones:
            bone_context = {}

            # for each bone save their properties
            for key, value in bone.items():
                # only save the property if it is a float, integer, boolean or string
                if type(value) in [float, int, bool, str]:
                    bone_context[key] = value

            control_rig_context[bone.name] = bone_context

        # save the control rig context in the control mode context
        control_mode_context[properties.control_rig_name] = control_rig_context

    # save the control mode context in the context
    properties.context[properties.control_mode] = control_mode_context


def save_source_mode_context(properties):
    """
    This function saves the current context of source mode to the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    source_rig = bpy.data.objects.get(properties.source_rig_name)
    if source_rig:
        if not properties.context.get(properties.source_mode):
            properties.context[properties.source_mode] = {}
            properties.context[properties.source_mode][source_rig.name] = {}

        # if the object has actions then save their first frames transform offset values
        actions = get_actions(source_rig)
        if actions:
            properties.context[properties.source_mode][source_rig.name] = {}
            for action in actions:
                offset = get_action_transform_offset(action)
                if properties.context[properties.source_mode][source_rig.name].get('action_offsets'):
                    properties.context[properties.source_mode][source_rig.name]['action_offsets'][action.name] = offset
                else:
                    properties.context[properties.source_mode][source_rig.name]['action_offsets'] = {}

                # subtract the transform offsets of the first frame on the action
                set_action_transform_offsets(action, offset, 'SUBTRACT')

        # otherwise save the objects transform values
        else:
            properties.context[properties.source_mode][source_rig.name]['transforms'] = get_object_transforms(
                source_rig
            )
            # set the object transforms to their applied transforms
            clear_object_transforms(source_rig)


def save_context(properties):
    """
    This function saves the current context of a particular mode to the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # -------- generic properties --------
    properties.context['frame_current'] = bpy.context.scene.frame_current

    # set the current frame to zero
    bpy.context.scene.frame_set(frame=0)

    # -------- mode specific properties --------
    if properties.previous_mode == properties.source_mode and properties.selected_mode == properties.control_mode:
        save_source_mode_context(properties)

    if properties.previous_mode == properties.control_mode:
        save_control_mode_context(properties)


@bpy.app.handlers.persistent
def save_properties(*args):
    """
    This function saves the window manger properties to the scene properties.

    :param args: This soaks up the extra arguments for the app handler.
    """
    # get both the scene and addon property groups
    window_manager_properties = bpy.context.window_manager.ue2rigify
    scene_properties = bpy.context.scene.ue2rigify

    # assign all the addon property values to the scene property values
    for attribute in dir(window_manager_properties):
        if not attribute.startswith(('__', 'bl_', 'rna_type', 'group', 'idp_array')):
            value = getattr(window_manager_properties, attribute)
            try:
                scene_properties[attribute] = value
            except TypeError:
                scene_properties[attribute] = str(value)


def load_source_mode_context(properties):
    """
    This function loads the current context of a source mode that was saved in the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    source_rig = bpy.data.objects.get(properties.source_rig_name)

    # restore the source rig object to its previous transform values
    if source_rig and properties.context.get(properties.source_mode):
        if properties.context[properties.source_mode].get(source_rig.name):
            if properties.context[properties.source_mode][source_rig.name].get('action_offsets'):
                # restore the actions to their original values
                for action_name, offset in properties.context[properties.source_mode][source_rig.name]['action_offsets'].items():
                    # add the offset to all the source rig actions
                    action = bpy.data.actions.get(action_name)
                    if action:
                        set_action_transform_offsets(action, offset, 'ADD')
                    action = bpy.data.actions.get(f'{properties.source_mode}_{action_name}')
                    if action:
                        set_action_transform_offsets(action, offset, 'ADD')

                # remove the saved offsets from the context
                bpy.context.window_manager.ue2rigify.context[properties.source_mode][source_rig.name]['action_offsets'] = {}

        else:
            source_rig_context = properties.context[properties.source_mode].get(source_rig.name)
            if source_rig_context:
                set_object_transforms(source_rig, source_rig_context.get('transforms'))


def load_control_mode_context(properties):
    """
    This function loads the current context of a control mode that was saved in the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get control rig object and context
    control_rig_object = bpy.data.objects.get(properties.control_rig_name)
    control_mode_context = properties.context.get(properties.control_mode)
    control_rig_context = None
    if control_mode_context:
        control_rig_context = control_mode_context.get(control_rig_object.name)

    # get source rig object and context
    source_rig_object = bpy.data.objects.get(properties.source_rig_name)
    source_mode_context = properties.context.get(properties.source_mode)
    source_rig_context = None
    if source_mode_context:
        source_rig_context = properties.context.get(source_rig_object.name)

    # move the control rig actions back to counter the offsets to the source rig actions
    if source_rig_context:
        if source_rig_context.get('action_offsets'):

            # get the link that maps the bone to the source rig object
            root_bone = None
            links_data = templates.get_saved_links_data(properties)
            for link_data in links_data:
                if link_data['from_socket'] == 'object':
                    root_bone = link_data['to_socket']

                if not root_bone:
                    if link_data['to_socket'] == 'object':
                        root_bone = link_data['from_socket']

            if root_bone:
                # restore the actions to their original values
                for action_name, offset in properties.context['source_rig']['action_offsets'].items():
                    action = bpy.data.actions.get(action_name.replace(f'{properties.source_mode}_', ''))
                    if action:
                        set_action_transform_offsets(action, offset, 'ADD', root_bone)

    # if there is there is a control rig context and a control rig
    if control_rig_object and control_rig_context:

        # set the active action on the control rig
        if control_rig_object.animation_data:
            active_action_name = control_rig_context.get('active_action', '')
            active_action = bpy.data.actions.get(active_action_name)
            if active_action:
                control_rig_object.animation_data.action = active_action

        # save the current property values on each bone
        for bone in control_rig_object.pose.bones:
            bone_context = control_rig_context.get(bone.name)

            # if there is a bone context, set the bone properties to the saved context
            if bone_context:
                for key, value in bone_context.items():
                    bone[key] = value


def load_context(properties):
    """
    This function loads the current context of a particular mode that was saved in the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    if properties.context:
        # -------- generic properties --------
        frame_current = properties.context.get('frame_current')
        if frame_current:
            bpy.context.scene.frame_set(frame=frame_current)

        # -------- mode specific properties --------
        if properties.selected_mode == properties.source_mode:
            load_source_mode_context(properties)

        if properties.selected_mode == properties.control_mode:
            load_control_mode_context(properties)


@bpy.app.handlers.persistent
def pre_file_load(*args):
    """
    This function executes before a file load.

    :param args: This soaks up the extra arguments for the app handler.
    """
    properties = bpy.context.window_manager.ue2rigify

    # make sure that the node tree is not checking for updates
    properties.check_node_tree_for_updates = False

    # make sure that the rig is frozen
    properties.freeze_rig = True


@bpy.app.handlers.persistent
def load_properties(*args):
    """
    This function loads the saved scene properties into the window manger properties.

    :param args: This soaks up the extra arguments for the app handler.
    """
    # get both the scene and addon property groups
    window_manager_properties = bpy.context.window_manager.ue2rigify
    scene_properties = bpy.context.scene.ue2rigify

    # make sure that the node tree is not checking for updates
    window_manager_properties.check_node_tree_for_updates = False

    # make sure that the rig is frozen
    window_manager_properties.freeze_rig = True

    # remove the selected rig template from the values to be set and set it first
    selected_rig_template = scene_properties.pop('selected_rig_template', None)
    if selected_rig_template:
        setattr(window_manager_properties, 'selected_rig_template', selected_rig_template)
    else:
        setattr(window_manager_properties, 'selected_rig_template', window_manager_properties.default_template)

    # assign all the scene property values to the addon property values
    for attribute in scene_properties.keys():
        if hasattr(window_manager_properties, attribute):
            if attribute not in ['freeze_rig', 'check_node_tree_for_updates']:
                scene_value = scene_properties.get(attribute)
                window_manger_value = str(getattr(window_manager_properties, attribute))

                # if the scene and window manger value are not the same
                if window_manger_value != str(scene_value):
                    setattr(window_manager_properties, attribute, scene_value)

    # get the updated window manager properties
    properties = bpy.context.window_manager.ue2rigify
    if properties.selected_mode in [properties.fk_to_source_mode, properties.source_to_deform_mode]:
        properties.check_node_tree_for_updates = True


def clear_undo_history():
    """
    This function clears blenders undo history by calling a null operator and repeatedly
    pushing that operation into the undo stack until all previous history is cleared from the undo
    history.
    """
    # run this null operator
    bpy.ops.ue2rigify.null_operator()

    # repeatedly push the last operator into the undo stack till there are no more undo steps
    for item in range(0, bpy.context.preferences.edit.undo_steps+1):
        bpy.ops.ed.undo_push(message='UE to Rigify Mode Change')


def match_rotation_modes(properties):
    """
    This function matches the rotation mode on the source rig object and it corresponding bone.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    control_rig = bpy.data.objects.get(properties.control_rig_name)
    source_rig = bpy.data.objects.get(properties.source_rig_name)

    # get the source to deform links
    templates.set_template_files(properties, mode_override=properties.source_to_deform_mode)
    links_data = templates.get_saved_links_data(properties)

    # match the rotation mode to the objects rotation mode
    for link_data in links_data:
        if link_data['from_socket'] == 'object':
            bone = control_rig.pose.bones.get(link_data['to_socket'])
            if bone:
                bone.rotation_mode = source_rig.rotation_mode


def get_formatted_operator_parameter(parameter_name, regex, code_line):
    """
    This function re-formats the given code into keyword argument parameters.

    :param str parameter_name: The name of the operator keyword argument.
    :param str regex: The regex expression to remove from the code line.
    :param str code_line: The line of code to parse.
    :return str: The formatted operator key word arguments.
    """
    return f'{parameter_name}="{re.sub(regex, "", code_line).split(",")}"'.replace("'", r'\"')


def get_rigify_bone_operator(un_hashed_operator_name, bone_name, properties):
    """
    This function parses the ui code the rigify generates to get the lines that have the listed bones names
    that an operator is for and the fully populated operator with it kwargs.

    :param str un_hashed_operator_name: The name of the operator before the ending hash value.
    :param str bone_name: The name of the bone that the operation is done on.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of parsed values that are either bone lists or string constructed operator calls.
    """
    # get the rig ui file from the text blocks that was generated by rigify
    rig_ui_object = bpy.data.texts.get(properties.rig_ui_file_name)

    if rig_ui_object:
        # convert the lines of code into a list
        rig_ui_lines = rig_ui_object.as_string().split('\n')

        # this regex expresion contains all the patterns that will be removed from the code lines
        regex = (
            r"(props|.input_bones|.output_bones|.ctrl_bones|.operator|group\d|=|\"|\[|\]| |\}|\{|\'|\)|\(|\:)"
        )

        # go through each line of code
        for index, line in enumerate(rig_ui_lines):

            # parse out the full operator call with the correctly populated kwargs
            if bone_name in line and un_hashed_operator_name in rig_ui_lines[index - 3]:
                operator = re.sub(regex, '', rig_ui_lines[index - 3]).split(',')[0]
                output_bones = None
                input_bones = None
                ctrl_bones = None

                if 'output_bones' in rig_ui_lines[index-2]:
                    output_bones = get_formatted_operator_parameter('output_bones', regex, rig_ui_lines[index - 2])

                if 'input_bones' in rig_ui_lines[index-1]:
                    input_bones = get_formatted_operator_parameter('input_bones', regex, rig_ui_lines[index - 1])

                if 'ctrl_bones' in rig_ui_lines[index]:
                    ctrl_bones = get_formatted_operator_parameter('ctrl_bones', regex, rig_ui_lines[index])
                else:
                    raise RuntimeError(
                        f'There was an error parsing the rigify {properties.rig_ui_file_name} file. Check the rigify '
                        f'addon code to see if that code has changed how it generates the rig ui.'
                    )

                if output_bones and input_bones and ctrl_bones:
                    return f'bpy.ops.{operator}({output_bones}, {input_bones}, {ctrl_bones})'
