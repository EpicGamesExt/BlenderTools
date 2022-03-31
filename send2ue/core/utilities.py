# Copyright Epic Games, Inc. All Rights Reserved.

import os
import re
import sys
import bpy
import math
import shutil
import inspect
import importlib
import tempfile
from . import settings
from . import extension
from ..ui import header_menu
from ..dependencies import unreal
from ..constants import AssetTypes, ToolInfo, PreFixToken, Extensions
from mathutils import Vector, Quaternion, Matrix


def get_asset_name_from_file_name(file_path):
    """
    Get a asset name from a file path.

    :param str file_path: A file path.
    :return str: A asset name.
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def track_progress(message=None, param=None):
    """
    A decorator that makes its wrapped function a queued job.

    :param str message: A the progress message.
    :param str param: A the name of the parameter value to inject in the message.
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            description = function.__name__
            if message:
                arg_names = inspect.getfullargspec(function).args
                if param is not None:
                    value = kwargs.get(param)
                    if value is None:
                        index = arg_names.index(param)
                        value = args[index]
                    description = message.format(param=get_asset_name_from_file_name(value))
            bpy.app.driver_namespace[ToolInfo.EXECUTION_QUEUE.value].put((function, args, kwargs, description))
        return wrapper
    return decorator


def get_operator_class_by_bl_idname(bl_idname):
    """
    Gets a operator class from its bl_idname.

    :return class: The operator class.
    """
    context, name = bl_idname.split('.')
    return getattr(bpy.types, f'{context.upper()}_OT_{name}', None)


def get_lod0_name(asset_name, properties):
    """
    Gets the correct name for lod0.

    :param str asset_name: The name of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :return str: The full name for lod0.
    """
    result = re.search(rf"({properties.lod_regex})", asset_name)
    if result:
        lod = result.groups()[-1]
        return asset_name.replace(lod, f'{lod[:-1]}0')
    return asset_name


def get_lod_index(asset_name, properties):
    """
    Gets the lod index from the given asset name.

    :param str asset_name: The name of the asset.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :return int: The lod index
    """
    result = re.search(rf"({properties.lod_regex})", asset_name)
    if result:
        lod = result.groups()[-1]
        return int(lod[-1])
    return 0


def get_collections_as_path(scene_object, properties):
    """
    Walks the collection hierarchy till it finds the given scene object.

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
        return '/'.join(parent_names).replace(f'{ToolInfo.EXPORT_COLLECTION.value}/', '')

    return ''


def get_temp_folder():
    """
    Gets the full path to the temp folder on disk.

    :return str: A folder path.
    """
    return os.path.join(
        tempfile.gettempdir(),
        'blender',
        'send2ue',
        'data'
    )


def get_import_path(scene_object, properties, asset_type):
    """
    Gets the unreal import path.

    :param object scene_object: A object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str asset_type: The type of asset.
    :return str: The full import path for the given asset.
    """
    if asset_type == AssetTypes.ANIMATION:
        game_path = properties.unreal_animation_folder_path

    else:
        game_path = properties.unreal_mesh_folder_path

    sub_path = get_collections_as_path(scene_object, properties)
    if sub_path:
        game_path = f'{game_path}{sub_path}/'

    return game_path


def get_full_import_path(scene_object, properties, asset_type):
    """
    Gets the unreal import path when using the immediate collection name as the asset name.

    :param object scene_object: A object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str asset_type: The type of asset.
    :return str: The full import path for the given asset.
    """
    export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
    parent_collection = get_parent_collection(scene_object, export_collection)
    import_path = get_import_path(scene_object, properties, asset_type)

    if properties.use_immediate_parent_collection_name and parent_collection:
        if import_path:
            import_path = import_path.replace(f'{parent_collection.name}/', '')

    return import_path


def get_custom_property_fcurve_data(action_name):
    """
    Gets the names and key frame points of object custom property values from the fcurves.

    :param str action_name: The name of the action to export.
    :return dict: A dictionary of custom property fcurve names and points.
    """
    data = {}
    action = bpy.data.actions.get(action_name)
    frame_rate = bpy.context.scene.render.fps
    if action:
        for fcurve in action.fcurves:
            if fcurve.data_path.startswith('["') and fcurve.data_path.endswith('"]'):
                name = fcurve.data_path.strip('["').strip('"]')
                data[name] = [[(point.co[0]-1)/frame_rate, point.co[1]] for point in fcurve.keyframe_points]
    return data


def get_action_names(rig_object, all_actions=True):
    """
    Gets a list of action names from the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param bool all_actions: Whether to get all action names, or just the un-muted actions.
    :return list: A list of action names.
    """
    action_names = []
    if rig_object:
        if rig_object.animation_data:
            for nla_track in rig_object.animation_data.nla_tracks:
                # if solo only return the actions in that track
                if nla_track.is_solo and not all_actions:
                    action_names = []
                    for strip in nla_track.strips:
                        if strip.action:
                            return [strip.action.name]

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
    Gets a list of action objects from the provided rig objects animation data.

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


def get_all_action_attributes(scene_object):
    """
    Gets all the action attributes on the provided rig.

    :param object scene_object: A object of type armature with animation data.
    :return dict: The action attributes on the provided rig.
    """
    attributes = {}
    if scene_object.animation_data:
        for nla_track in scene_object.animation_data.nla_tracks:
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
    Gets the current context of the scene and its objects.

    :return dict: A dictionary of values that are the current context.
    """
    object_contexts = {}
    for scene_object in bpy.data.objects:
        active_action_name = ''
        if scene_object.animation_data and scene_object.animation_data.action:
                active_action_name = scene_object.animation_data.action.name

        object_contexts[scene_object.name] = {
            'hide': scene_object.hide_get(),
            'select': scene_object.select_get(),
            'active_action': active_action_name,
            'actions': get_all_action_attributes(scene_object)
        }

    active_object = None
    if bpy.context.active_object:
        active_object = bpy.context.active_object.name

    return {
        'mode': getattr(bpy.context, 'mode', 'OBJECT'),
        'objects': object_contexts,
        'active_object': active_object
    }


def get_pose(rig_object):
    """
    Gets the transforms of the pose bones on the provided rig object.

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


def get_from_collection(object_type, properties):
    """
    This function fetches the objects inside each collection according to type and returns the
    the list of object references.

    :param str object_type: The object type you would like to get.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of objects
    """
    collection_objects = []

    # get the collection with the given name
    export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
    if export_collection:
        # get all the objects in the collection
        for collection_object in export_collection.all_objects:
            # dont select an object if it has a parent and combine child meshes option is on
            if properties.combine_child_meshes:
                if collection_object.parent:
                    if collection_object.parent.type == AssetTypes.MESH:
                        continue

            # if the object is the correct type
            if collection_object.type == object_type:

                # if the object is visible
                if collection_object.visible_get():
                    # ensure the object doesn't end with one of the post fix tokens
                    if not any(collection_object.name.startswith(f'{token.value}_') for token in PreFixToken):
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
    mesh_objects = get_from_collection(AssetTypes.MESH, properties)
    child_meshes = []
    for mesh_object in mesh_objects:
        if rig_object == get_armature_modifier_rig_object(mesh_object):
            child_meshes.append(mesh_object)
    return child_meshes


def get_unreal_asset_name(asset_name, properties, lod=False):
    """
    Takes a given asset name and removes the postfix _LOD and other non-alpha numeric characters
    that unreal won't except.

    :param str asset_name: The original name of the asset to export.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param bool lod: Whether to use the lod post fix of not.
    :return str: The formatted name of the asset to export.
    """
    asset_name = re.sub(r"\W+", "_", asset_name)

    if properties.import_lods:
        # remove the lod name from the asset
        result = re.search(rf"({properties.lod_regex})", asset_name)
        if result and not lod:
            asset_name = asset_name.replace(result.groups()[0], '')

    return asset_name


def get_asset_name(asset_name, properties, lod=False):
    """
    Takes a given asset name and removes the postfix _LOD and other non-alpha numeric characters
    that unreal won't except.

    :param str asset_name: The original name of the asset to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool lod: Whether to use the lod post fix of not.
    :return str: The formatted name of the asset to export.
    """
    if properties.use_immediate_parent_collection_name:
        asset_object = bpy.data.objects.get(asset_name)
        export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
        if asset_object and export_collection:
            parent_collection = get_parent_collection(asset_object, export_collection)
            if parent_collection and parent_collection.name != ToolInfo.EXPORT_COLLECTION.value:
                return get_unreal_asset_name(parent_collection.name, properties, lod)
    return get_unreal_asset_name(asset_name, properties, lod)


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


def get_skeleton_asset_path(rig_object, properties):
    """
    Gets the asset path to the skeleton.

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
        export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
        mesh_collection_objects = get_from_collection(AssetTypes.MESH, properties)

        if properties.use_immediate_parent_collection_name and export_collection:
            # use the collection that is the parent of a child mesh to build the skeleton game path
            for child in children:
                parent_collection = get_parent_collection(child, export_collection)
                if parent_collection and parent_collection.name != ToolInfo.EXPORT_COLLECTION.value:
                    import_path = get_full_import_path(child, properties, AssetTypes.MESH)
                    return f'{import_path}{parent_collection.name}_Skeleton'

        # use the child mesh that is in the mesh collection to build the skeleton game path
        for child in children:
            if child in mesh_collection_objects:
                asset_name = get_asset_name(child.name, properties)
                import_path = get_full_import_path(child, properties, AssetTypes.MESH)
                return f'{import_path}{asset_name}_Skeleton'

        # otherwise just use the first child mesh
        for child in children:
            if child in [mesh_object for mesh_object in bpy.data.objects if mesh_object.type == AssetTypes.MESH]:
                asset_name = get_asset_name(child.name, properties)
                import_path = get_full_import_path(child, properties, AssetTypes.MESH)
                return f'{import_path}{asset_name}_Skeleton'

    report_error(
        f'"{rig_object.name}" needs its unreal skeleton asset path specified under the "Path" settings '
        f'so it can be imported correctly!'
    )


def get_transform_in_degrees(transform, decimals=4):
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


def set_to_title(text):
    """
    Converts text to titles.

    :param str text: The original text to convert to a title.
    :return str: The new title text.
    """
    return ' '.join([word.capitalize() for word in text.lower().split('_')]).strip('.json')


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


def set_action_mute_values(rig_object, action_names):
    """
    This function un-mutes the values based of the provided list

    :param object rig_object: A object of type armature with animation data.
    :param list action_names: A list of action names to un-mute
    """
    if rig_object:
        if rig_object.animation_data:
            for nla_track in rig_object.animation_data.nla_tracks:
                for strip in nla_track.strips:
                    if strip.action:
                        if strip.action.name in action_names:
                            nla_track.mute = False
                        else:
                            nla_track.mute = True


def set_selected_objects(scene_object_names):
    """
    Sets selection only on the given objects.

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
    Sets the current context of the scene and its objects.

    :param dict context: A dictionary of values the the context should be set to.
    """
    mode = context.get('mode', 'OBJECT')
    active_object_name = context.get('active_object')
    object_contexts = context.get('objects')
    for object_name, attributes in object_contexts.items():
        scene_object = bpy.data.objects.get(object_name)
        if scene_object:
            scene_object.hide_set(attributes.get('hide', False))
            scene_object.select_set(attributes.get('select', False))

            active_action = attributes.get('active_action')
            if active_action:
                scene_object.animation_data.action = bpy.data.actions.get(active_action)

            set_all_action_attributes(scene_object, attributes.get('actions', {}))

    # set the active object
    if active_object_name:
        bpy.context.view_layer.objects.active = bpy.data.objects.get(active_object_name)

    # set the mode
    if bpy.context.mode != mode:
        # Note:
        # When the mode context is read in edit mode it can be 'EDIT_ARMATURE' or 'EDIT_MESH', even though you
        # are only able to set the context to 'EDIT' mode. Thus, if 'EDIT' was read from the mode context, the mode
        # is set to edit.
        if 'EDIT' in mode:
            mode = 'EDIT'
        bpy.ops.object.mode_set(mode=mode)


def set_all_action_attributes(rig_object, attributes):
    """
    This function sets the action attributes to the provided values.

    :param object rig_object: A object of type armature with animation data.
    :param dict attributes: The values of the action attributes.
    """
    if rig_object.animation_data:
        for nla_track in rig_object.animation_data.nla_tracks:
            for strip in nla_track.strips:
                if strip.action:
                    action_attributes = attributes.get(strip.action.name)
                    if action_attributes:
                        strip.frame_start = action_attributes.get('frame_start', strip.frame_start)
                        strip.frame_end = action_attributes.get('frame_end', strip.frame_end)
                        nla_track.mute = action_attributes.get('mute', nla_track.mute)

                        is_solo = action_attributes.get('is_solo')
                        if is_solo:
                            nla_track.is_solo = is_solo


def set_action_mute_value(rig_object, action_name, mute):
    """
    This function sets a given action's nla track to the provided mute value.

    :param object rig_object: A object of type armature with animation data.
    :param str action_name: The name of the action mute value to modify
    :param bool mute: Whether or not to mute the nla track
    """
    if rig_object:
        if rig_object.animation_data:
            for nla_track in rig_object.animation_data.nla_tracks:
                for strip in nla_track.strips:
                    if strip.action:
                        if strip.action.name == action_name:
                            nla_track.mute = mute


def set_all_action_mute_values(rig_object, mute):
    """
    This function set all mute values on all nla tracks on the provided rig objects animation data.

    :param object rig_object: A object of type armature with animation data.
    :param bool mute: Whether or not to mute all nla tracks

    """
    if rig_object:
        if rig_object.animation_data:
            for nla_track in rig_object.animation_data.nla_tracks:
                nla_track.mute = mute


def is_unreal_connected():
    """
    Checks if the unreal rpc server is connected, and if not attempts a bootstrap.
    """
    try:
        unreal.bootstrap_unreal_with_rpc_server()
        return True
    except ConnectionError:
        report_error('Could not find an open Unreal Editor instance!')
        return False


def is_lod_of(asset_name, mesh_object_name, properties):
    """
    Checks if the given asset name matches the lod naming convention.

    :param str asset_name: The name of the asset to export.
    :param str mesh_object_name: The name of the lod mesh.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    return asset_name == get_asset_name(mesh_object_name, properties)


def is_collision_of(asset_name, mesh_object_name, properties):
    """
    Checks if the given asset name matches the collision naming convention.

    :param str asset_name: The name of the asset to export.
    :param str mesh_object_name: The name of the collision mesh.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    """
    return bool(
        re.fullmatch(
            r"U(BX|CP|SP|CX)_" + asset_name + r"(_\d+)?",
            mesh_object_name
        ) or re.fullmatch(
            r"U(BX|CP|SP|CX)_" + asset_name + rf"{properties.lod_regex}(_\d+)?", mesh_object_name
        )
    )


def has_extension_draw(location):
    """
    Checks whether the given location has any draw functions.

    :param str location: The name of the draw location i.e. export, import, validations.
    """
    for key in bpy.app.driver_namespace.keys():
        if key.startswith(Extensions.DRAW_NAMESPACE) and key.endswith(f'_draw_{location}'):
            return True
    return False


def create_collections():
    """
    Creates the collections for the addon.
    """
    # Create the default collections if they don't already exist
    for collection_name in ToolInfo.COLLECTION_NAMES.value:
        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)


def create_operator(bl_idname, function):
    """
    Creates a operator class

    :param str bl_idname: The operators bl_idname.
    :param callable function: The function called within the operator.
    :return Operator: A operator class.
    """
    def execute(self, context):
        function(bpy.context.scene.send2ue)
        return {'FINISHED'}

    return type(
        convert_to_class_name(bl_idname),
        (bpy.types.Operator,),
        {
            'bl_idname': bl_idname,
            'bl_label': bl_idname.replace('.', ' ').replace('_', ' '),
            'execute': execute,
            # 'window_manager_properties': bpy.context.window_manager.send2ue
        })


def remove_data(data):
    """
    Removes the provided data.

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

    :param list[object] data_blocks: A blender data block object.
    :param list[object] original_data_blocks: A list of the original data blocks.
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
    temp_folder = os.path.join(
        tempfile.gettempdir(),
        ToolInfo.NAME.value
    )
    remove_from_disk(temp_folder, directory=True)


def remove_temp_data():
    """
    Removes the temp data folder and its contents.
    """
    temp_folder = get_temp_folder()
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)


def remove_unpacked_files(unpacked_files):
    """
    Removes a list of files that were unpacked and re-packs them.

    :param dict unpacked_files: A dictionary of image names and file paths that where unpacked.
    """
    for image_name, file_path in unpacked_files.items():
        image = bpy.data.images.get(image_name)
        if image:
            image.pack()

        if os.path.exists(file_path):
            remove_from_disk(file_path)

        # remove the parent folder if it is empty
        folder = os.path.dirname(file_path)
        if not os.listdir(folder):
            remove_from_disk(folder, directory=True)


def refresh_all_areas():
    """
    Iterates of all windows and screens and tags them for a redraw
    """
    for window_manager in bpy.data.window_managers:
        for window in window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()


def select_asset_collisions(asset_name, properties):
    """
    Selects the collision assets for the given asset.

    :param str asset_name: The name of the asset to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    export_collection = bpy.data.collections.get(ToolInfo.EXPORT_COLLECTION.value)
    if export_collection:
        for mesh_object in export_collection.objects:
            if is_collision_of(asset_name, mesh_object.name, properties):
                mesh_object.select_set(True)


def join_collisions(collisions):
    """
    Joins the given collisions into a single mesh.

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


def convert_to_class_name(bl_idname):
    """
    Converts the bl_idname to a class name.

    :param str bl_idname: A bl_idname.
    :return str: A class name.
    """
    return ''.join([word.capitalize() for word in re.split(r'\.|_', bl_idname)])


def convert_blender_to_unreal_location(location):
    """
    Converts blender location coordinates to unreal location coordinates.

    :return list[float]: The unreal location.
    """
    x = location[0]*100
    y = location[1]*100
    z = location[2]*100
    return [x, -y, z]


def convert_unreal_to_blender_location(location):
    """
    Converts unreal location coordinates to blender location coordinates.

    :return list[float]: The blender location.
    """
    x = location[0]/100
    y = location[1]/100
    z = location[2]/100
    return [x, -y, z]


def addon_enabled(*args):
    """
    This function is designed to be called once after the addon is activated. Since the scene context
    is not accessible from inside a addon's register function, this function can be added to the event
    timer, then make function calls that use the scene context, and then is removed.
    """
    setup_project()


def setup_project(*args):
    """
    This is run when the integration launches, and on new file load events.

    :param args: This soaks up the extra arguments for the app handler.
    """
    # remove the cached files
    remove_temp_folder()

    # create the default settings template
    settings.create_default_template()

    # if the scene properties are not available yet recall this function
    properties = getattr(bpy.context.scene, ToolInfo.NAME.value, None)
    if not properties:
        bpy.app.timers.register(setup_project, first_interval=0.1)

    # ensure the extension draws are created
    extension_factory = extension.ExtensionFactory()
    extension_factory.create_draws()

    # create the scene collections
    addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
    if addon and addon.preferences.automatically_create_collections:
        create_collections()

    # create the header menu
    if importlib.util.find_spec('unpipe') is None:
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
    :param str details: The error message details to display to the user.
    """
    if not os.environ.get('SEND2UE_DEV'):
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


def select_all_children(scene_object, object_type, properties, exclude_postfix_tokens=False):
    """
    Selects all of an objects children.

    :param object scene_object: A object.
    :param str object_type: The type of object to select.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool exclude_postfix_tokens: Whether or not to exclude objects that have a postfix token.
    """
    children = scene_object.children or get_meshes_using_armature_modifier(scene_object, properties)
    for child_object in children:
        if child_object.type == object_type:
            if exclude_postfix_tokens:
                if any(child_object.name.startswith(f'{token.value}_') for token in PreFixToken):
                    continue

            child_object.select_set(True)
            if child_object.children:
                select_all_children(child_object, object_type, properties, exclude_postfix_tokens)


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
            select_all_children(selected_object, 'MESH', properties, exclude_postfix_tokens=True)

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
        mesh_objects = bpy.data.collections[ToolInfo.EXPORT_COLLECTION.value].all_objects.values()
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
    Stashes the active action on an object into its nla strips.

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

    # TODO fix relative path speed
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


def import_unreal_asset(file_path):
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
    if properties.source_application in ['ue4', 'ue5']:
        import_unreal_asset(file_path)

    clear_undo_history('Asset Import')


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
    Unpacks the textures from the .blend file if they dont exist on disk, so
    the images will be included in the fbx export.

    :return list: A dictionary of image names and file paths that where unpacked.
    """
    unpacked_files = {}

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
                                    unpacked_files[image.name] = image.filepath_from_user()

    return unpacked_files


def apply_transform(scene_object, use_location=False, use_rotation=False, use_scale=False):
    """
    Apply the transform on the given object.

    :param object scene_object: A object.
    :param bool use_location: Whether or not to apply the location.
    :param bool use_rotation: Whether or not to apply the rotation.
    :param bool use_scale: Whether or not to apply the scale.
    """
    matrix_basis = scene_object.matrix_basis
    identity_matrix = Matrix()
    location, rotation, scale = matrix_basis.decompose()

    # get matrices
    translation_matrix = Matrix.Translation(location)
    rotation_matrix = matrix_basis.to_3x3().normalized().to_4x4()
    scale_matrix = Matrix.Diagonal(scale).to_4x4()

    transform = [identity_matrix, identity_matrix, identity_matrix]
    basis = [translation_matrix, rotation_matrix, scale_matrix]

    def swap(i):
        transform[i], basis[i] = basis[i], transform[i]

    if use_location:
        swap(0)
    if use_rotation:
        swap(1)
    if use_scale:
        swap(2)

    matrix = transform[0] @ transform[1] @ transform[2]
    if hasattr(scene_object.data, 'transform'):
        scene_object.data.transform(matrix)
    for child in scene_object.children:
        child.matrix_local = matrix @ child.matrix_local

    scene_object.matrix_basis = basis[0] @ basis[1] @ basis[2]


def safe_call(function):
    """
    Safely calls a function and handles the exception.

    :param callable function: A callable.
    """
    try:
        function()
    except Exception as error:
        sys.stderr.write(f'{error}\n')
