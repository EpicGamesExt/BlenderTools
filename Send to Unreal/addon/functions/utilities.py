# Copyright Epic Games, Inc. All Rights Reserved.

import os
import bpy
import shutil


def get_action_name(action_name, properties):
    """
    This function gets the name of the action from either the control or source rig's action name.

    :param str action_name: A source rig's action name.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: A control rig's action name.
    """
    if properties.use_ue2rigify:
        ue2rigify_properties = bpy.context.window_manager.ue2rigify
        return action_name.replace(f'{ue2rigify_properties.source_mode}_', '')
    else:
        return action_name


def get_action_names(rig_object, properties, all_actions=True):
    """
    This function gets a list of action names from the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool all_actions: Whether to get all action names, or just the un-muted actions.
    :return list: A list of action names.
    """
    action_names = []
    for nla_track in rig_object.animation_data.nla_tracks:
        # get all the action names if the all flag is set
        if all_actions:
            for strip in nla_track.strips:
                action_names.append(strip.action.name)

        # otherwise get only the un-muted actions
        else:
            if not nla_track.mute:
                for strip in nla_track.strips:
                    action_names.append(get_action_name(strip.action.name, properties))
    return action_names


def get_current_context():
    """
    This function gets the current context of the scene and its objects.

    :return dict: A dictionary of values that are the current context.
    """
    active_object = bpy.context.active_object

    current_context = {
        'visible_objects': bpy.context.visible_objects,
        'selected_objects': bpy.context.selected_objects,
        'active_object': active_object,
        'mode': bpy.context.mode
    }

    # save the current action if there is one
    if active_object:
        if active_object.animation_data:
            current_context['active_animation'] = active_object.animation_data.action

    return current_context


def set_context(context):
    """
    This function sets the current context of the scene and its objects.

    :param dict context: A dictionary of values the the context should be set to.
    """
    active_object = context['active_object']

    # set the visible objects
    for scene_object in context['visible_objects']:
        scene_object.hide_set(False)

    # set the selected objects
    for scene_object in context['selected_objects']:
        scene_object.select_set(True)

    # set the active object
    bpy.context.view_layer.objects.active = active_object

    # set the active animation
    if active_object:
        if active_object.animation_data:
            active_object.animation_data.action = context.get('active_animation')

    # set the mode
    if bpy.context.mode != context['mode']:
        # Note:
        # When the mode context is read in edit mode it can be 'EDIT_ARMATURE' or 'EDIT_MESH', even though you
        # are only able to set the context to 'EDIT' mode. Thus, if 'EDIT' was read from the mode context, the mode
        # is set to edit.
        if 'EDIT' in context['mode']:
            context['mode'] = 'EDIT'

        bpy.ops.object.mode_set(mode=context['mode'])


def set_ue2rigify_state(properties):
    """
    This function sets a property on whether to use code from the ue2rigify addon or not.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: The value of the use_ue2rigify property.
    """
    if bpy.context.preferences.addons.get('ue2rigify'):
        ue2rigify_properties = bpy.context.window_manager.ue2rigify
        if ue2rigify_properties.selected_mode == ue2rigify_properties.control_mode:
            properties.use_ue2rigify = True
            return properties.use_ue2rigify

    properties.use_ue2rigify = False
    return properties.use_ue2rigify


def set_unit_scale(scale):
    """
    This function sets the scene unit scale.

    :param float scale: The unit scale of the scene.
    """
    # Set all the scene units
    for scene in bpy.data.scenes:
        scene.unit_settings.scale_length = scale


def set_grid_scale(scale):
    """
    This function sets all the 3D view port grid scales

    :param float scale: The viewport grid scale.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.grid_scale = scale


def set_viewport_clipping(clip_end):
    """
    This function sets all the 3D view port camera end clipping lengths.

    :param float clip_end: The viewport end clipping length
    """
    # Set all the 3D view port grid scales
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_end = clip_end


def set_frame_rate(frame_rate):
    """
    This function set the scene's frame rate.

    :param float frame_rate: The scene's frame rate.
    """
    for scene in bpy.data.scenes:
        scene.render.fps = frame_rate


def set_unreal_scene_scale(properties):
    """
    This function sets all the scene settings to the settings that work best with unreal.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # set the correct scene
    set_unit_scale(properties.unreal_unit_scale)
    set_grid_scale(properties.unreal_grid_scale)
    set_viewport_clipping(properties.unreal_viewport_clip_end)


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


def resize_object(scale, center_override):
    """
    This function scales the active selection from a given global transform position.

    :param tuple scale: A tuple with x,y,z float values for the relative change in scale. Where 1 does not change
    the current scale value.
    :param tuple center_override: A tuple with x,y,z float values for the center of the transform.
    """
    # since this operator only works in the 3d view a custom context must be passed in
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.transform.resize(override, value=scale, center_override=center_override)
                break


def scale_all_objects_and_apply_transforms(scale):
    """
    This function scales all objects in the scene relative to the world center, and then applies the scale.

    :param float scale: A uniform scale value.
    """
    # get the current context
    context = get_current_context()

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # deselect everything
    bpy.ops.object.select_all(action='DESELECT')

    for scene_object in bpy.context.scene.objects:
        x_scale = scene_object.scale.x*scale
        y_scale = scene_object.scale.y*scale
        z_scale = scene_object.scale.z*scale

        # select the object and make it the active object
        scene_object.select_set(True)
        bpy.context.view_layer.objects.active = scene_object

        # scale the object up from the world origin
        resize_object(scale=(x_scale, y_scale, z_scale), center_override=(0.0, 0.0, 0.0))

        # apply the transform
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # deselect the object
        scene_object.select_set(False)

    # focus on all the objects
    bpy.ops.object.select_all(action='SELECT')
    focus_on_selected()
    bpy.ops.object.select_all(action='DESELECT')

    # restore the previous context
    set_context(context)


def set_default_project_settings():
    """
    This function sets all the scene settings to the blender default settings.
    """
    properties = bpy.context.window_manager.send2ue

    set_unit_scale(properties.default_unit_scale)
    set_grid_scale(properties.default_grid_scale)
    set_viewport_clipping(properties.default_viewport_clip_end)
    set_frame_rate(properties.default_frame_rate)


def create_groups(properties):
    """
    This function creates the collections for the addon.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # Create groups from the group_names if they don't already exist
    for collection_name in properties.collection_names:
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)


def remove_temp_folder():
    """
    This function removes the temp folder where send2ue caches FBX files for Unreal imports.
    """
    properties_window_manger = bpy.context.window_manager.send2ue
    temp_folder = os.path.join(
        bpy.utils.user_resource('SCRIPTS', "addons"),
        properties_window_manger.module_name,
        'temp'
    )
    try:
        original_umask = os.umask(0)
        if os.path.exists(temp_folder):
            os.chmod(temp_folder, 0o777)
            shutil.rmtree(temp_folder)
    finally:
        os.umask(original_umask)


@bpy.app.handlers.persistent
def check_for_armature_objects(*args):
    """
    This function checks if an armature is in the rig collection, then
    :param args:
    :return:
    """
    if not bpy.context.preferences.addons.get('send2ue'):
        return None

    window_manager_properties = bpy.context.window_manager.send2ue
    addon_properties = bpy.context.preferences.addons[window_manager_properties.module_name].preferences

    # get all the armature objects previously put into the rig collection
    rig_collection_objects = window_manager_properties.get('rig_collection_objects', [])
    scene_scale = round(bpy.context.scene.unit_settings.scale_length, 6)

    if not addon_properties.do_not_show_again and scene_scale != 0.010000:
        # get the rig collection
        rig_collection = bpy.data.collections.get(window_manager_properties.rig_collection_name)
        if rig_collection:
            rig_objects = [rig_object for rig_object in rig_collection.all_objects if rig_object.type == 'ARMATURE']

            # get the name of the rigs with and without animation data
            rigs_without_animation = [rig_object.name for rig_object in rig_objects if not rig_object.animation_data]
            rigs_with_animation = [rig_object.name for rig_object in rig_objects if rig_object.animation_data]

            # get the names of all the rig object in the rig collection
            rig_object_names = rigs_without_animation + rigs_with_animation

            # check to see if the armature is already in the saved rig collection objects
            if rig_collection_objects != rig_object_names:
                # assign the current rig collection objects to the rig collection so the user wont be prompted
                # when them same armature is under the rig collection
                window_manager_properties['rig_collection_objects'] = rig_object_names

                if rigs_with_animation:
                    message = (
                        f'Your scene scale is {scene_scale}, and your rig has keyed animation! Set your scene scale'
                        f' to 0.01 and fix your rig!'
                    )
                    confirm_message = 'Click "OK" to read the Send to Unreal Documentation on scene scale'
                    bpy.ops.wm.set_scene_scale(
                        'INVOKE_DEFAULT',
                        message=message,
                        confirm_message=confirm_message,
                        fix=False
                    )

                if rigs_without_animation:
                    message = (
                        f'Your scene scale is {scene_scale}, this can cause bone scaling issues in Unreal. It is '
                        f'recommended that your scene scale is 0.01!'
                    )
                    confirm_message = 'Click "OK" to fix this automatically'
                    bpy.ops.wm.set_scene_scale(
                        'INVOKE_DEFAULT',
                        message=message,
                        confirm_message=confirm_message,
                        fix=True
                    )


@bpy.app.handlers.persistent
def save_properties(*args):
    """
    This function saves the current addon properties to the scene properties.

    :param args: This soaks up the extra arguments for the app handler.
    """
    module_name = bpy.context.window_manager.send2ue.module_name

    # get both the scene and addon property groups
    scene_properties = bpy.context.scene.send2ue
    addon_properties = bpy.context.preferences.addons[module_name].preferences

    # assign all the addon property values to the scene property values
    for attribute in dir(addon_properties):
        if not attribute.startswith(('__', 'bl_', 'rna_type')):
            value = getattr(addon_properties, attribute)
            try:
                scene_properties[attribute] = value
            except TypeError:
                scene_properties[attribute] = str(value)


@bpy.app.handlers.persistent
def load_properties(*args):
    """
    This function loads the saved scene properties into the current addon properties.

    :param args: This soaks up the extra arguments for the app handler.
    """
    module_name = bpy.context.window_manager.send2ue.module_name

    # get both the scene and addon property groups
    scene_properties = bpy.context.scene.send2ue
    addon_properties = bpy.context.preferences.addons[module_name].preferences

    # assign all the scene property values to the addon property values
    for attribute in scene_properties.keys():
        if hasattr(addon_properties, attribute):
            scene_value = scene_properties.get(attribute)
            addon_value = str(getattr(addon_properties, attribute))

            # if the scene and window manger value are not the same
            if addon_value != str(scene_value):
                setattr(addon_properties, attribute, scene_value)


def addon_enabled():
    """
    This function to designed to be called once after the addon is activated. Since the scene context
    is not accessible from inside a addon's register function, this function can be added to the event
    timer, then make function calls that use the scene context, and then is removed.
    """
    setup_project()
    # remove this function from the event timer so that it only fires once.
    bpy.app.timers.unregister(addon_enabled)
    return 1.0


@bpy.app.handlers.persistent
def setup_project(*args):
    """
    This is run when the integration launches, and sets up the appropriate scene settings and creates the collections
    for export assets.

    :param args: This soaks up the extra arguments for the app handler.
    """
    window_manager_properties = bpy.context.window_manager.send2ue
    addon_properties = bpy.context.preferences.addons[window_manager_properties.module_name].preferences

    # remove the cached files
    remove_temp_folder()

    create_groups(window_manager_properties)

    if addon_properties.always_use_unreal_scene_scale:
        set_unreal_scene_scale(addon_properties)


def draw_error_message(self, context):
    """
    This function creates the layout for the error pop up

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.label(text=bpy.context.window_manager.send2ue.error_message)


def report_error(message):
    """
    This function reports a given error message to the screen.

    :param str message: The error message to display to the user.
    """
    # parse runtime error messages
    if 'RuntimeError: ' in message:
        message = message.split('RuntimeError: ')[-1][:-1]

    bpy.context.window_manager.send2ue.error_message = message
    bpy.context.window_manager.popup_menu(draw_error_message, title="Error", icon='ERROR')


# TODO add to Blender Integration library
def deselect_all_objects():
    """
    This function deselects all object in the scene.
    """
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')


# TODO add to Blender Integration library
def clean_nla_tracks(rig_object, action, properties):
    """
    This function removes any nla tracks that have a action that matches the provided action. Also it removes
    any nla tracks that have actions in their strips that match other actions, or have no strips.

    :param object rig_object: A object of type armature with animation data.
    :param object action: A action object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
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
                    action_names = get_action_names(rig_object, properties)
                    if action_names.count(strip.action.name) > 1:
                        rig_object.animation_data.nla_tracks.remove(nla_track)


# TODO add to Blender Integration library
def stash_animation_data(rig_object, properties):
    """
    This function stashes the active action on an object into its nla strips.

    :param object rig_object: A object of type armature with animation data.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # if there is an active action on the rig object
    active_action = rig_object.animation_data.action

    # remove any nla tracks that have the active action, have duplicate names, or no strips
    clean_nla_tracks(rig_object, active_action, properties)

    if active_action:
        action_name = get_action_name(active_action.name, properties)
        # create a new nla track
        rig_object_nla_track = rig_object.animation_data.nla_tracks.new()
        rig_object_nla_track.name = action_name

        # create a strip with the active action as the strip action
        rig_object_nla_track.strips.new(
            name=action_name,
            start=1,
            action=rig_object.animation_data.action
        )
        rig_object_nla_track.mute = False


def format_asset_path(game_reference):
    """
    This function removes the extra characters if a game reference is pasted in.

    :param str game_reference: The game reference copied to the clipboard from the unreal asset.
    :return str: The formatted game folder path.
    """
    if game_reference[-1] == "'":
        return game_reference.split("'")[-2].split(".")[0]
    else:
        return game_reference


def format_folder_path(game_reference):
    """
    This function removes the asset name if a game reference is pasted in.

    :param str game_reference: The game reference copied to the clipboard from the unreal asset.
    :return str: The formatted game folder path.
    """
    if game_reference[-1] == "'":
        asset_name = format_asset_path(game_reference).split('/')[-1]
        return format_asset_path(game_reference).replace(asset_name, '')
    else:
        return game_reference


def auto_format_unreal_mesh_folder_path(self, value):
    """
    This function is called every time the unreal mesh folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    formatted_value = format_folder_path(self.unreal_mesh_folder_path)
    if self.unreal_mesh_folder_path != formatted_value:
        self.unreal_mesh_folder_path = formatted_value


def auto_format_unreal_animation_folder_path(self, value):
    """
    This function is called every time the unreal animation folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    formatted_value = format_folder_path(self.unreal_animation_folder_path)
    if self.unreal_animation_folder_path != formatted_value:
        self.unreal_animation_folder_path = formatted_value


def auto_format_unreal_skeleton_asset_path(self, value):
    """
    This function is called every time the unreal skeleton asset path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    if self.unreal_skeleton_asset_path:
        formatted_value = format_asset_path(self.unreal_skeleton_asset_path)
        if self.unreal_skeleton_asset_path != formatted_value:
            self.unreal_skeleton_asset_path = formatted_value


def auto_format_disk_mesh_folder_path(self, value):
    """
    This function is called every time the disk mesh folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    if os.path.isdir(self.disk_mesh_folder_path):
        self.incorrect_disk_mesh_folder_path = False
    else:
        self.incorrect_disk_mesh_folder_path = True


def auto_format_disk_animation_folder_path(self, value):
    """
    This function is called every time the disk animation folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    if os.path.isdir(self.disk_animation_folder_path):
        self.incorrect_disk_animation_folder_path = False
    else:
        self.incorrect_disk_animation_folder_path = True
