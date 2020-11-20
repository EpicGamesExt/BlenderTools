# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
import re
from . import scene

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
                    action_names.append(strip.action.name)

            # otherwise get only the un-muted actions
            else:
                if not nla_track.mute:
                    for strip in nla_track.strips:
                        action_names.append(strip.action.name)
    return action_names


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

                # set if object is hidden or not
                previous_settings['hidden'] = rig_object.hide_get()
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

        # remove any nla tracks that have the active action, have duplicate names, or no strips
        clean_nla_tracks(rig_object, active_action)

        if active_action:
            # create a new nla track
            rig_object_nla_track = rig_object.animation_data.nla_tracks.new()
            rig_object_nla_track.name = active_action.name

            # create a strip with the active action as the strip action
            rig_object_nla_track.strips.new(
                name=active_action.name,
                start=1,
                action=rig_object.animation_data.action
            )
            rig_object_nla_track.mute = False


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
    show_error = lambda: None

    # if a bone name can be parsed from the rigify error message, assign the show error function and confirmation
    if len(parsed_bone_name) > 1:
        confirm_message = 'Click "OK" to see what is causing the issue!'
        show_error = lambda: show_bone_setting(parsed_bone_name[0], 'BONE')

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
        f'"{rig_name}" does not have a bone named "{bone_name}"!'
    )

    confirm_message = f'Click "OK" to remove the socket "{bone_name}" from node "{node_name}"'
    remove_socket = lambda: scene.remove_missing_bone_socket(node_name, bone_name, properties)

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


def save_context(properties):
    """
    This function saves the current context of a particular mode to the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # save the previous mode's context
    if properties.previous_mode == properties.control_mode:
        control_mode_context = {}

        # get the control rig
        control_rig_object = bpy.data.objects.get(properties.control_rig_name)
        if control_rig_object:
            control_rig_context = {}

            # save the active action on the control rig
            if control_rig_object.animation_data:
                if control_rig_object.animation_data.action:
                    control_rig_context['active_action'] = control_rig_object.animation_data.action.name

            # save the current property values on each bone
            for bone in control_rig_object.pose.bones:
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


def load_context(properties):
    """
    This function loads the current context of a particular mode that was saved in the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    if properties.context:
        control_mode_context = properties.context.get(properties.control_mode)

        # if the selected mode is control mode and a saved control mode context
        if properties.selected_mode == properties.control_mode and control_mode_context:
            control_rig_context = control_mode_context.get(properties.control_rig_name)
            control_rig_object = bpy.data.objects.get(properties.control_rig_name)

            # if there is there is a control rig context and a control rig
            if control_mode_context and control_rig_object:

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
                        f'There was an error parsing the rigify {properties.rig_ui_file_name} file!. Check the rigify '
                        f'addon code to see if that code has changed how it generates the rig ui!'
                    )

                if output_bones and input_bones and ctrl_bones:
                    return f'bpy.ops.{operator}({output_bones}, {input_bones}, {ctrl_bones})'
