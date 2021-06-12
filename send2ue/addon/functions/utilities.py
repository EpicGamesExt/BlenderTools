# Copyright Epic Games, Inc. All Rights Reserved.

import os
import re
import bpy
import math
import shutil
import tempfile
from mathutils import Vector, Quaternion
from . import unreal


def get_action_name(action_name, properties):
    """
    This function gets the name of the action from either the control or source rig's action name.

    :param str action_name: A source rig's action name.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool source_name: Whether to get the source action names.
    :return str: A control rig's action name.
    """
    if properties.use_ue2rigify:
        ue2rigify_properties = bpy.context.window_manager.ue2rigify
        return action_name.replace(f'{ue2rigify_properties.source_mode}_', '')
    else:
        return action_name


def get_collections_as_path(scene_object, properties):
    """
    This function walks the collection hierarchy till it finds the given scene object.

    :param object scene_object: A object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The sub path to the given scene object.
    """
    parent_names = []
    if properties.use_collections_as_folders and len(scene_object.users_collection) > 0:
        parent_collection = scene_object.users_collection[0]
        parent_names.append(parent_collection.name)
        set_parent_collection_names(parent_collection, parent_names)
        parent_names.reverse()
        return '/'.join(parent_names).replace(f'{properties.mesh_collection_name}/', '')

    return ''


def get_import_path(scene_object, properties):
    """
    This function builds unreal import path.

    :param object scene_object: A object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The full import path for the given asset.
    """
    game_path = properties.unreal_mesh_folder_path
    sub_path = get_collections_as_path(scene_object, properties)
    if sub_path:
        game_path = f'{game_path}{sub_path}/'

    return game_path


def get_full_import_path(scene_object, properties, parent_collection=None):
    """
    This function builds unreal import path when using the immediate collection name as the asset name.

    :param object scene_object: A object.
    :param object parent_collection: A collection.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The full import path for the given asset.
    """
    mesh_collection = bpy.data.collections.get(properties.mesh_collection_name)
    parent_collection = get_parent_collection(scene_object, mesh_collection)
    import_path = get_import_path(scene_object, properties)

    # get the import path if the collection hierarchy sub folder path to the unreal asset
    if properties.use_immediate_parent_collection_name and parent_collection:
        if import_path:
            import_path = import_path.replace(f'{parent_collection.name}/', '')

    return import_path


def get_action_names(rig_object, all_actions=True):
    """
    This function gets a list of action names from the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param bool all_actions: Whether to get all action names, or just the un-muted actions.
    :return list: A list of action names.
    """
    action_names = []
    if rig_object:
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


def get_actions(rig_object, all_actions=True):
    """
    This function gets a list of action objects from the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param bool all_actions: Whether to get all action names, or just the un-muted actions.
    :return list: A list of action objects.
    """
    actions = []
    action_names = get_action_names(rig_object, all_actions)

    for action_name in action_names:
        action = bpy.data.actions.get(action_name)
        if action:
            actions.append(action)

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


def get_current_context():
    """
    This function gets the current context of the scene and its objects.

    :return dict: A dictionary of values that are the current context.
    """
    selected_objects = []
    for selected_object in bpy.context.selected_objects:
        active_action_name = ''
        # get the selected objects active animation
        if selected_object.animation_data:
            if selected_object.animation_data.action:
                active_action_name = selected_object.animation_data.action.name

        # save the selected object reference and its active animation
        selected_objects.append([selected_object.name, active_action_name])

    current_context = {
        'visible_objects': [visible_object.name for visible_object in bpy.context.visible_objects],
        'selected_objects': selected_objects,
        'mode': bpy.context.mode
    }

    # save the current action if there is one
    active_object = bpy.context.active_object
    if active_object:
        current_context['active_object'] = active_object.name
        if active_object.animation_data:
            if active_object.animation_data.action:
                current_context['active_animation'] = active_object.animation_data.action.name

    return current_context


def get_pose(rig_object):
    """
    This function gets the transforms of the pose bones on the provided rig object.

    :param object rig_object: An armature object.
    :return dict: A dictionary of pose bone transforms
    """
    pose = {}

    if rig_object:
        for bone in rig_object.pose.bones:
            pose[bone.name] = {
                'location': bone.location,
                'rotation_quaternion': bone.rotation_quaternion,
                'rotation_euler': bone.rotation_euler,
                'scale': bone.scale
            }

    return pose


def get_from_collection(collection_name, object_type, properties):
    """
    This function fetches the objects inside each collection according to type and returns the
    the list of object references.

    :param str collection_name: The collection that you would like to retrieve objects from.
    :param str object_type: The object type you would like to get.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of objects
    """
    collection_objects = []

    # get the collection with the given name
    collection = bpy.data.collections.get(collection_name)
    if collection:

        # get all the objects in the collection
        for collection_object in collection.all_objects:
            # dont select an object if it has a parent and combine child meshes option is on
            if properties.combine_child_meshes:
                if collection_object.parent:
                    if collection_object.parent.type == 'MESH':
                        continue

            # if the object is the correct type
            if collection_object.type == object_type:

                # if the object is visible
                if collection_object.visible_get():
                    # add it to the group of objects
                    collection_objects.append(collection_object)

    return collection_objects


def get_meshes_using_armature_modifier(rig_object, properties):
    """
    This function get the objects using the given rig in an armature modifier.

    :param object rig_object: An object of type armature.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of objects using the given rig in an armature modifier.
    """
    mesh_objects = get_from_collection(properties.mesh_collection_name, 'MESH', properties)
    child_meshes = []
    for mesh_object in mesh_objects:
        if rig_object == get_armature_modifier_rig_object(mesh_object):
            child_meshes.append(mesh_object)
    return child_meshes


def get_unreal_asset_name(asset_name, properties):
    """
    This function takes a given asset name and removes the postfix _LOD and other non-alpha numeric characters
    that unreal won't except.

    :param str asset_name: The original name of the asset to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The formatted name of the asset to export.
    """
    if properties.use_ue2rigify:
        return get_action_name(re.sub(r"\W+", "_", re.sub(r'(_LOD\d)', '', asset_name)), properties)

    if properties.use_immediate_parent_collection_name:
        asset_object = bpy.data.objects.get(asset_name)
        mesh_collection = bpy.data.collections.get(properties.mesh_collection_name)
        if asset_object and mesh_collection:
            parent_collection = get_parent_collection(asset_object, mesh_collection)
            if parent_collection and parent_collection.name != properties.mesh_collection_name:
                return re.sub(r"\W+", "_", re.sub(r'(_LOD\d)', '', parent_collection.name))

    return re.sub(r"\W+", "_", re.sub(r'(_LOD\d)', '', asset_name))


def get_parent_collection(scene_object, collection):
    """
    This function walks the collection tree to find the collection parent of the given object.

    :param object scene_object: A object.
    :param object collection: A collection.
    :return str: The collection name.
    """
    for child_collection in collection.children:
        parent_collection = get_parent_collection(scene_object, child_collection)
        if parent_collection:
            return parent_collection

    if scene_object in collection.objects.values():
        return collection


def get_skeleton_game_path(rig_object, properties):
    """
    This function gets the game path to the skeleton.

    :param object rig_object: A object of type armature.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The game path to the unreal skeleton asset.
    """
    # if a skeleton path is provided
    if properties.unreal_skeleton_asset_path:
        return properties.unreal_skeleton_asset_path

    children = rig_object.children or get_meshes_using_armature_modifier(rig_object, properties)

    if children:
        # get all meshes from the mesh collection
        mesh_collection = bpy.data.collections.get(properties.mesh_collection_name)
        mesh_collection_objects = get_from_collection(properties.mesh_collection_name, 'MESH', properties)

        if properties.use_immediate_parent_collection_name and mesh_collection:
            # use the collection that is the parent of a child mesh to build the skeleton game path
            for child in children:
                parent_collection = get_parent_collection(child, mesh_collection)
                if parent_collection and parent_collection.name != properties.mesh_collection_name:
                    import_path = get_full_import_path(child, properties)
                    return f'{import_path}{parent_collection.name}_Skeleton'

        # use the child mesh that is in the mesh collection to build the skeleton game path
        for child in children:
            if child in mesh_collection_objects:
                asset_name = get_unreal_asset_name(child.name, properties)
                return f'{get_full_import_path(child, properties)}{asset_name}_Skeleton'

        # otherwise just use the first child mesh
        for child in children:
            if child in [mesh_object for mesh_object in bpy.data.objects if mesh_object.type == 'MESH']:
                asset_name = get_unreal_asset_name(child.name, properties)
                return f'{get_full_import_path(child, properties)}{asset_name}_Skeleton'

    report_error(
        f'"{rig_object.name}" needs its unreal skeleton asset path specified under the "Path" settings '
        f'so it can be imported correctly!'
    )


def set_parent_collection_names(collection, parent_names):
    """
    This function recursively adds the parent collection names to the given list until.

    :param object collection: A collection.
    :param list parent_names: A list of parent collection names.
    :return list: A list of parent collection names.
    """
    for parent_collection in bpy.data.collections:
        if collection.name in parent_collection.children.keys():
            parent_names.append(parent_collection.name)
            set_parent_collection_names(parent_collection, parent_names)
            return None


def set_selected_objects(scene_object_names):
    """
    This function selects only the give objects.

    :param list scene_object_names: A list of object names.
    """
    deselect_all_objects()
    for scene_object_name in scene_object_names:
        scene_object = bpy.data.objects.get(scene_object_name)
        if scene_object:
            scene_object.select_set(True)


def set_pose(rig_object, pose_values):
    """
    This function sets the transforms of the pose bones on the provided rig object.

    :param object rig_object: An armature object.
    :param dict pose_values: A dictionary of pose bone transforms.
    """
    if rig_object:
        for bone in rig_object.pose.bones:
            bone_values = pose_values.get(bone.name)
            if bone_values:
                bone.location = bone_values['location']
                bone.rotation_quaternion = bone_values['rotation_quaternion']
                bone.rotation_euler = bone_values['rotation_euler']
                bone.scale = bone_values['scale']


def set_context(context):
    """
    This function sets the current context of the scene and its objects.

    :param dict context: A dictionary of values the the context should be set to.
    """
    # set the visible objects
    for visible_object_name in context['visible_objects']:
        visible_object = bpy.data.objects.get(visible_object_name)
        if visible_object:
            visible_object.hide_set(False)

    # set the selected objects
    for scene_object_name, active_action_name in context['selected_objects']:
        scene_object = bpy.data.objects.get(scene_object_name)
        if scene_object:
            scene_object.select_set(True)

        # set the objects active animation
        active_action = bpy.data.actions.get(active_action_name)
        if active_action:
            scene_object.animation_data.action = active_action

    # set the active object
    active_object_name = context.get('active_object')
    if active_object_name:
        bpy.context.view_layer.objects.active = bpy.data.objects.get(active_object_name)

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


def get_transform_in_degrees(transform, decimals=2):
    """
    This function convert the given transform from radians to degrees.

    :param list transform: A list of radians.
    :param int decimals: The number of decimals to round the values to.
    :return list: A list of degrees.
    """
    return tuple([round(math.degrees(number), decimals) for number in transform])


def get_armature_modifier_rig_object(mesh_object):
    """
    This function gets the armature associated with a mesh via its armature modifier.

    :param object mesh_object: A object of type mesh.
    :return object: A object of type armature.
    """
    for modifier in mesh_object.modifiers:
        if modifier.type == 'ARMATURE':
            return modifier.object

    return None


def get_unique_parent_mesh_objects(rig_objects, mesh_objects, properties):
    """
    This function get only meshes that have a unique same armature parent.

    :param list rig_objects: A list of rig objects.
    :param list mesh_objects: A list of mesh objects.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of mesh objects.
    """
    unique_parent_mesh_objects = []

    if properties.combine_child_meshes:
        for rig_object in rig_objects:
            parent_count = 0
            for mesh_object in mesh_objects:
                if mesh_object.parent == rig_object or rig_object == get_armature_modifier_rig_object(mesh_object):
                    if parent_count < 1:
                        unique_parent_mesh_objects.append(mesh_object)
                    parent_count += 1

    if not unique_parent_mesh_objects:
        unique_parent_mesh_objects = mesh_objects

    return unique_parent_mesh_objects


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


def remove_data(data):
    """
    This function removes the provided data.

    :param dict data: A dictionary of data names.
    """
    for scene_object_name in data.get('objects', []):
        scene_object = bpy.data.objects.get(scene_object_name)
        if scene_object:
            bpy.data.objects.remove(scene_object)

    for armature_name in data.get('armatures', []):
        armature = bpy.data.armatures.get(armature_name)
        if armature:
            bpy.data.armatures.remove(armature)


def remove_extra_data(data_blocks, original_data_blocks):
    """
    This function remove any data from the provided data block that does not match the original data blocks.

    :param object data_blocks: A blender data block object.
    :param original_data_blocks: A list of the original data blocks.
    """
    # remove all the duplicate meshes
    data_blocks_to_remove = [data_block for data_block in data_blocks if data_block not in original_data_blocks]
    for data_block_to_remove in data_blocks_to_remove:
        data_blocks.remove(data_block_to_remove)


def remove_object_scale_keyframes(actions):
    """
    This function removes all scale keyframes the exist a object in the provided actions.

    :param float scale: The scale to set the all the object scaled keyframes to.
    :param list actions: A list of action objects.
    """
    for action in actions:
        for fcurve in action.fcurves:
            if fcurve.data_path == 'scale':
                action.fcurves.remove(fcurve)


def remove_from_disk(path, directory=False):
    """
    This function removes the given path from disk.

    :param str path: An file path.
    :param bool directory: Whether or not the path is a directory.
    """
    try:
        original_umask = os.umask(0)
        if os.path.exists(path):
            os.chmod(path, 0o777)
            if directory:
                shutil.rmtree(path)
            else:
                os.remove(path)
    finally:
        os.umask(original_umask)


def remove_temp_folder():
    """
    This function removes the temp folder where send2ue caches FBX files for Unreal imports.
    """
    properties_window_manger = bpy.context.window_manager.send2ue
    temp_folder = os.path.join(
        tempfile.gettempdir(),
        properties_window_manger.module_name
    )
    remove_from_disk(temp_folder, directory=True)


def remove_unpacked_files(file_paths):
    """
    This function removes a list of files that were unpacked and re-packs them.

    :param list file_paths: A list of file paths
    """
    for file_path in file_paths:
        image = bpy.data.images.get(os.path.basename(file_path))
        image.pack()
        remove_from_disk(file_path)

        # remove the parent folder if it is empty
        folder = os.path.dirname(file_path)
        if not os.listdir(folder):
            remove_from_disk(folder, directory=True)


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


def join_collisions(collisions):
    """
    This function joins the given collisions into a single mesh.

    :param object collisions: Mesh objects.
    :return str: The name of the joined mesh.
    """
    joined_collision = None
    selected_objects = bpy.context.selected_objects.copy()
    active_object = bpy.context.active_object

    deselect_all_objects()

    # select just the collisions
    for collision in collisions:
        collision.select_set(True)

    # duplicate the collisions
    bpy.ops.object.duplicate()

    # set the duplicates as active objects
    for duplicate_object in bpy.context.selected_objects.copy():
        bpy.context.view_layer.objects.active = duplicate_object
        duplicate_object.select_set(True)

    # join all the selected collisions
    if len(bpy.context.selected_objects) > 1:
        bpy.ops.object.join()
        joined_collision = bpy.context.selected_objects[0]

    # restore the selected objects
    for selected_object in selected_objects:
        selected_object.select_set(True)

    # restore the active object
    bpy.context.view_layer.objects.active = active_object

    return joined_collision


def match_collision_name_to_mesh_name(properties):
    """
    This function matches the selected collison to the selected mesh.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The changed collision name.
    """
    collisions = get_from_collection(properties.collision_collection_name, 'MESH', properties)
    meshes = get_from_collection(properties.mesh_collection_name, 'MESH', properties)

    if collisions and meshes:
        selected_meshes = [mesh for mesh in meshes if mesh.select_get()]
        selected_collisions = [collision for collision in collisions if collision.select_get()]

        if selected_meshes and selected_collisions:
            selected_mesh = selected_meshes[0]
            selected_collision = join_collisions(collisions)
            if selected_collision:
                name = f'{selected_collision.name.split("_")[0]}_{selected_mesh.name}'
                selected_collision.name = name
                return name
    return ''


def clear_pose(rig_object):
    """
    This function sets the transforms of the pose bones on the provided rig object to the resting position.

    :param object rig_object: An armature object.
    """
    if rig_object:
        for bone in rig_object.pose.bones:
            bone.location = Vector((0, 0, 0))
            bone.rotation_quaternion = Quaternion((0, 0, 0), 1)
            bone.rotation_euler = Vector((0, 0, 0))
            bone.scale = Vector((1, 1, 1))


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
    This function is designed to be called once after the addon is activated. Since the scene context
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
    properties = bpy.context.window_manager.send2ue

    # remove the cached files
    remove_temp_folder()

    addon = bpy.context.preferences.addons.get(properties.module_name)
    if addon and addon.preferences.automatically_create_collections:
        create_groups(properties)

    from ..ui import header_menu
    header_menu.add_pipeline_menu()


def draw_error_message(self, context):
    """
    This function creates the layout for the error pop up

    :param object self: This refers the the Menu class definition that this function will
    be appended to.
    :param object context: This parameter will take the current blender context by default,
    or can be passed an explicit context.
    """
    self.layout.label(text=bpy.context.window_manager.send2ue.error_message)
    if bpy.context.window_manager.send2ue.error_message_details:
        self.layout.label(text=bpy.context.window_manager.send2ue.error_message_details)


def report_error(message, details=''):
    """
    This function reports a given error message to the screen.

    :param str message: The error message to display to the user.
    """
    if not os.environ.get('DEV'):
        # parse runtime error messages
        if 'RuntimeError: ' in message:
            message = message.split('RuntimeError: ')[-1][:-1]

        bpy.context.window_manager.send2ue.error_message = message
        bpy.context.window_manager.send2ue.error_message_details = details
        bpy.context.window_manager.popup_menu(draw_error_message, title="Error", icon='ERROR')
    else:
        raise RuntimeError(message + details)


def report_path_error_message(layout, send2ue_property, report_text):
    """
    This function displays an error message on a row if a property
    returns a False value.

    :param object layout: The ui layout.
    :param object send2ue_property: Registered property of the addon
    :param str report_text: The text to report in the row label
    """

    # only create the row if the value of the property is true and a string
    if send2ue_property and type(report_text) == str:
        row = layout.row()

        row.alert = True
        row.label(text=report_text)


def select_all_children(scene_object, object_type, properties):
    """
    This function selects all of an objects children.

    :param object scene_object: A object.
    :param str object_type: The type of object to select.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    children = scene_object.children or get_meshes_using_armature_modifier(scene_object, properties)
    for child_object in children:
        if child_object.type == object_type:
            child_object.select_set(True)
            if child_object.children:
                select_all_children(child_object, object_type, properties)


def combine_child_meshes(properties):
    """
    This function combines all an objects child meshes and all of its children.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    selected_object_names = [selected_object.name for selected_object in bpy.context.selected_objects]
    duplicate_data = {}

    if properties.combine_child_meshes:
        selected_objects = bpy.context.selected_objects.copy()

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # select all children
        for selected_object in selected_objects:
            select_all_children(selected_object, 'MESH', properties)

        # duplicate the selection
        bpy.ops.object.duplicate()

        duplicate_data['objects'] = [selected_object.name for selected_object in bpy.context.selected_objects]
        duplicate_data['armatures'] = []
        for selected_object in bpy.context.selected_objects:
            if selected_object.type == 'ARMATURE':
                duplicate_data['armatures'].append(selected_object.data.name)

        duplicate_objects = bpy.context.selected_objects.copy()

        # apply all modifiers on the duplicates
        for duplicate_object in duplicate_objects:
            apply_all_mesh_modifiers(duplicate_object)

        deselect_all_objects()

        # select all the duplicate objects that are meshes
        mesh_count = 0
        mesh_objects = bpy.data.collections[properties.mesh_collection_name].all_objects.values()
        for duplicate_object in duplicate_objects:
            if duplicate_object.type == 'MESH' and duplicate_object in mesh_objects:
                bpy.context.view_layer.objects.active = duplicate_object
                duplicate_object.select_set(True)
                mesh_count += 1

        # join all the selected mesh objects
        if mesh_count > 1:
            bpy.ops.object.join()

        # now select all the duplicate objects by their name
        for duplicate_object_name in duplicate_data['objects']:
            duplicate_object = bpy.data.objects.get(duplicate_object_name)
            if duplicate_object:
                duplicate_object.select_set(True)

        # match the collision name to the new joined mesh
        matched_collision_name = match_collision_name_to_mesh_name(properties)
        duplicate_data['objects'].append(matched_collision_name)

    return selected_object_names, duplicate_data


def apply_all_mesh_modifiers(scene_object):
    """
    This function applies all mesh modifiers on the given object.

    :param object scene_object: A object.
    """
    deselect_all_objects()

    # select the provided object
    bpy.context.view_layer.objects.active = scene_object
    scene_object.select_set(True)

    # apply all modifiers except the armature modifier
    for modifier in scene_object.modifiers:
        if modifier.type != 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=modifier.name)

    deselect_all_objects()


def deselect_all_objects():
    """
    This function deselects all object in the scene.
    """
    for scene_object in bpy.data.objects:
        scene_object.select_set(False)


# TODO add to Blender Integration library
def clean_nla_tracks(rig_object, action):
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
                    action_names = get_action_names(rig_object)
                    if action_names.count(strip.action.name) > 1:
                        rig_object.animation_data.nla_tracks.remove(nla_track)


# TODO add to Blender Integration library
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
    game_reference = game_reference.replace('\\', '/').replace(r'\\', '/').replace('//', '/')
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

    # Make sure the mesh path to unreal is correct as the engine will
    # hard crash if passed an incorrect path
    self.incorrect_unreal_mesh_folder_path = False
    if self.unreal_mesh_folder_path and not self.unreal_mesh_folder_path.lower().startswith("/game"):
        self.incorrect_unreal_mesh_folder_path = True


def auto_format_unreal_animation_folder_path(self, value):
    """
    This function is called every time the unreal animation folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    formatted_value = format_folder_path(self.unreal_animation_folder_path)
    if self.unreal_animation_folder_path != formatted_value:
        self.unreal_animation_folder_path = formatted_value

    # Make sure the animation path to unreal is correct as the engine will
    # hard crash if passed an incorrect path
    self.incorrect_unreal_animation_folder_path = False
    if self.unreal_animation_folder_path and not self.unreal_animation_folder_path.lower().startswith("/game"):
        self.incorrect_unreal_animation_folder_path = True


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

    # Make sure the skeleton path to unreal is correct as the engine will
    # hard crash if passed an incorrect path
    self.incorrect_unreal_skeleton_path = False
    if self.unreal_skeleton_asset_path and not unreal.asset_exists(self.unreal_skeleton_asset_path):
        self.incorrect_unreal_skeleton_path = True


def auto_format_disk_mesh_folder_path(self, value):
    """
    This function is called every time the disk mesh folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    is_relative = True
    self.incorrect_disk_mesh_folder_path = True

    self.mesh_folder_untitled_blend_file = False
    if self.disk_mesh_folder_path.startswith('//'):
        if not bpy.data.filepath:
            self.mesh_folder_untitled_blend_file = True
    else:
        is_relative = False

    # If the path is relative, prevent the UI from displaying it as a wrong
    # path. We expect the process that's going to use this path to resolve
    # the path and have an additional validation
    if is_relative:
        self.incorrect_disk_mesh_folder_path = False

    # os.path.isdir is very slow to check on every UI update. Lets only check if
    # we are not a relative path
    elif os.path.isdir(self.disk_mesh_folder_path):
        self.incorrect_disk_mesh_folder_path = False


def auto_format_disk_animation_folder_path(self, value):
    """
    This function is called every time the disk animation folder path is updated.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object value: The value of the property group class this update function is assigned to.
    """
    is_relative = True
    self.incorrect_disk_animation_folder_path = True

    self.animation_folder_untitled_blend_file = False
    if self.disk_animation_folder_path.startswith('//'):
        if not bpy.data.filepath:
            self.animation_folder_untitled_blend_file = True
    else:
        is_relative = False

    # If the path is relative, prevent the UI from displaying it as a wrong
    # path. We expect the process that's going to use this path to resolve
    # the path and have an additional validation
    if is_relative:
        self.incorrect_disk_animation_folder_path = False

    # os.path.isdir is very slow to check on every UI update. Lets only check
    # if we are not a relative path
    elif os.path.isdir(self.disk_animation_folder_path):
        self.incorrect_disk_animation_folder_path = False


def round_keyframes(actions):
    """
    This function rounds all keyframes on the provided actions to the nearest integer.

    :param list actions: A list of action objects.
    """
    for action in actions:
        for fcurve in action.fcurves:
            for keyframe_point in fcurve.keyframe_points:
                keyframe_point.co[0] = round(keyframe_point.co[0])


def scale_object(scene_object, scale_factor):
    """
    This function scales the provided object by the given scale factor.

    :param object scene_object: The scene object to scale.
    :param float scale_factor: The amount to proportionally scale the object.
    """
    scene_object.scale.x = scene_object.scale.x * scale_factor
    scene_object.scale.y = scene_object.scale.y * scale_factor
    scene_object.scale.z = scene_object.scale.z * scale_factor


def scale_object_actions(unordered_objects, actions, scale_factor):
    """
    This function scales the provided action's location keyframe on the provided objects by the given scale factor.

    :param list unordered_objects: A list of objects.
    :param list actions: A list of action objects.
    :param float scale_factor: The value to scale the location fcurves by.
    """
    # get the list of objects that do not have parents
    no_parents = [unordered_object for unordered_object in unordered_objects if not unordered_object.parent]

    # get the list of objects that have parents
    parents = [unordered_object for unordered_object in unordered_objects if unordered_object.parent]

    # re-order the imported objects to have the top of the hierarchies iterated first
    ordered_objects = no_parents + parents

    for ordered_object in ordered_objects:
        # run the export iteration but with "scale" set to the scale of the object as it was imported
        scale = (
            ordered_object.scale[0] * scale_factor,
            ordered_object.scale[1] * scale_factor,
            ordered_object.scale[2] * scale_factor
        )

        # if the imported object is an armature
        if ordered_object.type == 'ARMATURE':
            # iterate over any imported actions first this time...
            for action in actions:
                # iterate through the location curves
                for fcurve in [fcurve for fcurve in action.fcurves if fcurve.data_path.endswith('location')]:
                    # don't scale the objects location keys
                    if fcurve.data_path == 'location':
                        continue

                    # and iterate through the keyframe values
                    for keyframe_point in fcurve.keyframe_points:
                        # multiply the location keyframes by the scale per channel
                        keyframe_point.co[1] = keyframe_point.co[1] * scale[fcurve.array_index]
                        keyframe_point.handle_left[1] = keyframe_point.handle_left[1] * scale[fcurve.array_index]
                        keyframe_point.handle_right[1] = keyframe_point.handle_right[1] * scale[fcurve.array_index]

            # apply the scale on the object
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def import_unreal_4_asset(file_path):
    """
    This function imports an unreal asset, fixes the armature scale factor, and rounds the keyframe to the nearest
    integer.

    :param str file_path: The full file path the file on disk.
    """
    # maybe get all the actions in the .blend so we can discern them from the ones that are about to be imported...
    existing_actions = [action for action in bpy.data.actions]

    # import the fbx file
    bpy.ops.import_scene.fbx(filepath=file_path)

    # the list of imported actions
    imported_actions = [action for action in bpy.data.actions if action not in existing_actions]

    # scale the keyframes in the actions
    scale_object_actions(bpy.context.selected_objects, imported_actions, 1)

    # remove the object scale keyframes
    remove_object_scale_keyframes(actions=imported_actions)

    # round keyframes
    round_keyframes(imported_actions)


def import_asset(file_path, properties):
    """
    This function imports the selected asset appropriately according to which source application the file came from.

    :param str file_path: The full file path the file on disk.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    if properties.source_application == 'ue4':
        import_unreal_4_asset(file_path)

    clear_undo_history('Asset Import')


def recreate_lod_meshes(mesh_objects):
    """
    This function recreates the provided lod meshes by duplicating them and deleting there originals.

    :param list mesh_objects: A list of lod mesh objects.
    :return object: The new object.
    """
    new_mesh_objects = []
    # get the current selection and context
    context = get_current_context()

    for mesh_object in mesh_objects:
        if 'LOD' in mesh_object.name:
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            previous_object_name = mesh_object.name
            previous_mesh_name = mesh_object.data.name

            # deselect all objects
            deselect_all_objects()

            # select and duplicate the mesh object
            mesh_object.select_set(True)
            bpy.ops.object.duplicate()

            # remove the old object
            bpy.data.objects.remove(mesh_object)

            # remove the old mesh
            previous_mesh = bpy.data.meshes.get(previous_mesh_name)
            if previous_mesh:
                bpy.data.meshes.remove(previous_mesh)

            new_mesh_object = bpy.context.selected_objects[0]

            # rename the duplicated object to the old name
            new_mesh_object.name = previous_object_name
            # rename the duplicated mesh to the old name
            new_mesh_object.data.name = previous_mesh_name

        new_mesh_objects.append(new_mesh_object)

    # restore selection and context
    set_context(context)

    return new_mesh_objects


def clear_undo_history(message):
    """
    This function clears blenders undo history by doing a deselect all operation and repeatedly
    pushing that operation into the undo stack until all previous history is cleared from the undo
    history.

    :param str message: The message to display in the undo history.
    """
    # run this null operator
    bpy.ops.send2ue.null_operator()

    # repeatedly push the last operator into the undo stack till there are no more undo steps
    for item in range(0, bpy.context.preferences.edit.undo_steps + 1):
        bpy.ops.ed.undo_push(message=message)


def resolve_path(path):
    """
    This function checks if a given path is relative and returns the full
    path else returns the original path

    :param str path: The input path
    :return str: The expanded path
    """

    # Check for a relative path input. Relative paths are represented
    # by '//' eg. '//another/path/relative/to/blend_file'
    if path.startswith('//') or path.startswith('./'):
        # Build an absolute path resolving the relative path from the blend file
        path = bpy.path.abspath(path.replace("./", "//", 1))

    # Make sure the path has the correct OS separators
    path = bpy.path.native_pathsep(path)

    return path


def unpack_textures():
    """
    This function unpacks the textures from the .blend file if they dont exist on disk, so
    the images will be included in the fbx export.

    :return list: A list of file paths where the image was unpacked.
    """
    file_paths = []

    # go through each material
    for material in bpy.data.materials:
        if material.node_tree:
            # go through each node
            for node in material.node_tree.nodes:
                # check for packed textures
                if node.type == 'TEX_IMAGE':
                    image = node.image
                    if image:
                        if image.source == 'FILE':
                            if image.packed_file:
                                # if the unpacked image does not exist on disk
                                if not os.path.exists(image.filepath_from_user()):
                                    # unpack the image
                                    image.unpack()
                                    file_paths.append(image.filepath_from_user())

    return file_paths
