# Copyright Epic Games, Inc. All Rights Reserved.

import json
import math
import os
import re
import bpy
from . import utilities, validations, settings, formatting, ingest, extension
from ..constants import PathModes, AssetTypes, PreFixToken, ToolInfo, ExtensionOperators


def get_file_path(asset_name, properties, asset_type, lod=False, file_extension='fbx'):
    """
    Gets the export path if it doesn't already exist.  Then it returns the full path.

    :param str asset_name: The name of the asset that will be exported to a file.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param str asset_type: The type of data being exported.
    :param bool lod: Whether to use the lod post fix of not.
    :param str file_extension: The file extension in the file path.
    :return str: The full path to the file.
    """
    export_folder = None
    # if saving in a temp location
    if properties.path_mode in [
        PathModes.SEND_TO_PROJECT.value,
        PathModes.SEND_TO_DISK_THEN_PROJECT.value
    ]:
        export_folder = os.path.join(utilities.get_temp_folder(), asset_type.lower())

    # if saving to a specified location
    if properties.path_mode in [
        PathModes.SEND_TO_DISK.value,
        PathModes.SEND_TO_DISK_THEN_PROJECT.value
    ]:
        if asset_type == AssetTypes.MESH:
            export_folder = formatting.resolve_path(properties.disk_mesh_folder_path)

        if asset_type == AssetTypes.ANIMATION:
            export_folder = formatting.resolve_path(properties.disk_animation_folder_path)

    return os.path.join(
        export_folder,
        f'{utilities.get_asset_name(asset_name, properties, lod)}.{file_extension}'
    )


def export_lods(asset_id, asset_name, properties):
    """
    Exports the lod meshes and returns there file paths.

    :param str asset_id: The unique id of the asset.
    :param str asset_name: The name of the asset that will be exported to a file.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :return list: A list of lod file paths.
    """
    lods = {}
    if properties.import_lods:
        mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)
        for mesh_object in mesh_objects:
            if utilities.is_lod_of(asset_name, mesh_object.name, properties):
                if mesh_object.name != utilities.get_lod0_name(mesh_object.name, properties):
                    lod_index = utilities.get_lod_index(mesh_object.name, properties)
                    file_path = get_file_path(mesh_object.name, properties, asset_type=AssetTypes.MESH, lod=True)
                    export_mesh(asset_id, mesh_object, properties, lod=lod_index)
                    if file_path:
                        lods[str(lod_index)] = file_path
        return lods


def get_pre_scaled_context():
    """
    This function fetches the current scene's attributes.

    :return dict: A dictionary containing the current data attributes.
    """
    # look for an armature object and get its name
    context = {}
    for selected_object in bpy.context.selected_objects:
        if selected_object.type == 'ARMATURE':
            context['source_object'] = {}
            context['source_object']['object_name'] = selected_object.name
            context['source_object']['armature_name'] = selected_object.data.name
            bpy.context.view_layer.objects.active = selected_object

            # save the current scene scale
            context['scene_scale'] = bpy.context.scene.unit_settings.scale_length
            context['objects'] = bpy.data.objects.values()
            context['meshes'] = bpy.data.meshes.values()
            context['armatures'] = bpy.data.armatures.values()
            context['actions'] = bpy.data.actions.values()

    return context


def set_parent_rig_selection(mesh_object, properties):
    """
    Recursively selects all parents of an object as long as the parent are in the rig collection.

    :param object mesh_object: A object of type mesh.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return object: A armature object.
    """
    rig_object = utilities.get_armature_modifier_rig_object(mesh_object) or mesh_object.parent

    # if the scene object has a parent
    if rig_object:

        # if the scene object's parent is in the rig collection
        if rig_object in utilities.get_from_collection(AssetTypes.SKELETON, properties):
            # select the parent object
            rig_object.select_set(True)

            # if the combine child meshes option is on, then select all the rigs children that are meshes
            if properties.combine_child_meshes:
                utilities.select_all_children(rig_object, AssetTypes.MESH, properties, exclude_postfix_tokens=True)

            # call the function again to see if this object has a parent that
            set_parent_rig_selection(rig_object, properties)
    return rig_object


def set_selected_objects_to_center(properties):
    """
    This function gets the original world position and centers the objects at world zero for export.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return dict: A dictionary of tuple that are the original position values of the selected objects.
    """
    original_positions = {}

    if properties.use_object_origin:

        for selected_object in bpy.context.selected_objects:
            # get the original locations
            original_x = selected_object.location.x
            original_y = selected_object.location.y
            original_z = selected_object.location.z

            # set the location to zero
            selected_object.location.x = 0.0
            selected_object.location.y = 0.0
            selected_object.location.z = 0.0

            original_positions[selected_object.name] = original_x, original_y, original_z

    # return the original positions
    return original_positions


def set_object_positions(original_positions):
    """
    This function sets the given object's location in world space.

    :param object original_positions: A dictionary of tuple that are the original position values of the
    selected objects.
    """
    for object_name, positions in original_positions.items():
        scene_object = bpy.data.objects.get(object_name)
        if scene_object:
            scene_object.location.x = positions[0]
            scene_object.location.y = positions[1]
            scene_object.location.z = positions[2]


def set_armatures_as_parents(properties):
    """
    Sets the armature in a mesh modifier as a rig's parent.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)

    for mesh_object in mesh_objects:
        rig_object = utilities.get_armature_modifier_rig_object(mesh_object)
        if rig_object and not mesh_object.parent:
            mesh_object.parent = rig_object


def duplicate_objects_for_export(scene_scale, scale_factor, context, properties):
    """
    This function duplicates and prepares the selected objects for export.

    :param float scene_scale: The value to set the scene scale to.
    :param float scale_factor: The amount to scale the control rig by.
    :param dict context: A dictionary containing the current data attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return dict: A dictionary containing the current data attributes.
    """
    # duplicate the the selected objects so the originals are not modified
    bpy.ops.object.duplicate()

    context['duplicate_objects'] = bpy.context.selected_objects

    return context


def rename_duplicate_object(duplicate_object, context, properties):
    """
    This function renames the duplicated objects to match their original names and save a reference to them.
    :param object duplicate_object: A scene object.
    :param dict context: A dictionary containing the current data attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return dict: A dictionary containing the current data attributes.
    """
    # Get a the root object name and save the object reference. This needs to happen so when the
    # duplicate armature is renamed to correctly to match the original object. For example a
    # duplicated object named 'Armature' is automatically given the name 'Armature.001' by Blender.
    # By saving this object reference, its name can be restored back to 'Armature' after the export.
    context['source_object']['object'] = bpy.data.objects.get(context['source_object']['object_name'])
    context['source_object']['armature'] = bpy.data.armatures.get(context['source_object']['armature_name'])

    # use the armature objects name as the root in unreal
    object_name = context['source_object']['object_name']
    armature_name = context['source_object']['armature_name']

    if properties.export_object_name_as_root:
        # if the object is already named armature this forces the object name to root
        if 'armature' in [object_name.lower(), armature_name.lower()]:
            object_name = 'root'
            armature_name = 'root'
    # otherwise don't use the armature objects name as the root in unreal
    else:
        # Rename the armature object to 'Armature'. This is important, because this is a special
        # reserved keyword for the Unreal FBX importer that will be ignored when the bone hierarchy
        # is imported from the FBX file. That way there is not an additional root bone in the Unreal
        # skeleton hierarchy.
        object_name = 'Armature'
        armature_name = 'Armature'

    duplicate_object.name = object_name
    duplicate_object.data.name = armature_name

    return context


def fix_armature_scale(armature_object, scale_factor, context):
    """
    This function scales the provided armature object and it's animations.

    :param object armature_object: A object of type armature.
    :param float scale_factor: The amount to scale the control rig by.
    :param dict context: A dictionary containing the current data attributes.
    :return dict: A dictionary containing the current data attributes.
    """
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # scale the duplicate rig object
    utilities.scale_object(armature_object, scale_factor)

    # select the rig object
    armature_object.select_set(True)

    # apply the scale transformations on the selected object
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # scale up the objects action location keyframes to fix the applied scale
    actions = utilities.get_actions(armature_object)
    context['source_object']['actions'] = actions
    utilities.scale_object_actions([armature_object], actions, scale_factor)

    return context


def scale_rig_objects(properties):
    """
    This function changes the scene scale to 0.01 and scales the selected rig objects to offset that scene scale change.
    Then it return to original context.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return dict: The original context of the scene scale and its selected objects before changes occurred.
    """
    scene_scale = 0.01
    # get the context of the scene before any of the scaling operations
    context = get_pre_scaled_context()

    # only scale the rig object if there was a root object added to the context and automatically scaling bones is on
    if properties.automatically_scale_bones and context:
        # scale the rig objects by the scale factor needed to offset the 0.01 scene scale
        scale_factor = context['scene_scale'] / scene_scale

        # switch to object mode
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # change scene scale to 0.01
        bpy.context.scene.unit_settings.scale_length = scene_scale

        context = duplicate_objects_for_export(scene_scale, scale_factor, context, properties)

        for duplicate_object in context['duplicate_objects']:
            if duplicate_object.type == 'ARMATURE':
                # rename the duplicated objects and save the original object references to the context
                context = rename_duplicate_object(duplicate_object, context, properties)

                # set each object in a armature modifier to a parent
                set_armatures_as_parents(properties)

                # fix the armature scale and its animation and save that information to the context
                context = fix_armature_scale(duplicate_object, scale_factor, context)

        # restore the duplicate object selection for the export
        for duplicate_object in context['duplicate_objects']:
            duplicate_object.select_set(True)

    return context


def restore_rig_objects(context, properties):
    """
    This function takes the previous context of the scene scale and rig objects and sets them to the values in
    the context dictionary.

    :param dict context: The original context of the scene scale and its selected objects before changes occurred.
    :param properties:
    """
    if properties.automatically_scale_bones and context:
        scale_factor = bpy.context.scene.unit_settings.scale_length / context['scene_scale']

        # scale the control rig if needed
        # scale_control_rig(scale_factor, properties)

        # restore action scale the duplicated actions
        utilities.scale_object_actions(context['duplicate_objects'], context['source_object']['actions'], scale_factor)

        # remove all the duplicate objects
        utilities.remove_extra_data(bpy.data.objects, context['objects'])

        # remove all the duplicate meshes
        utilities.remove_extra_data(bpy.data.meshes, context['meshes'])

        # remove all the duplicate armatures
        utilities.remove_extra_data(bpy.data.armatures, context['armatures'])

        # remove all the duplicate actions
        utilities.remove_extra_data(bpy.data.actions, context['actions'])

        # restore the scene scale
        bpy.context.scene.unit_settings.scale_length = context['scene_scale']

        # restore the original object name on the root object name if needed
        source_object = context['source_object'].get('object')
        if source_object:
            source_object.name = context['source_object']['object_name']
            source_object.data.name = context['source_object']['armature_name']


def export_fbx_file(file_path, properties):
    """
    Exports a fbx file.

    :param str file_path: A file path where the file will be exported.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    export_settings = {}
    for group_name, group_data in settings.get_settings_by_path('blender-export_method', 'fbx').items():
        prefix = settings.get_generated_prefix('blender-export_method-fbx', group_name)
        for attribute_name in group_data.keys():
            export_settings[attribute_name] = settings.get_property_by_path(prefix, attribute_name, properties)

    bpy.ops.export_scene.fbx(
        filepath=file_path,
        use_selection=True,
        bake_anim_use_nla_strips=True,
        bake_anim_use_all_actions=False,
        object_types={'ARMATURE', 'MESH', 'EMPTY'},
        **export_settings
    )


def export_custom_property_fcurves(action_name, properties):
    """
    Exports custom property fcurves to a file.

    :param str action_name: The name of the action to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    file_path = properties.asset_data[properties.asset_id]['file_path']

    fcurve_file_path = None
    fcurve_data = utilities.get_custom_property_fcurve_data(action_name)
    if fcurve_data and properties.export_custom_property_fcurves:
        file_path, file_extension = os.path.splitext(file_path)
        fcurve_file_path = ToolInfo.FCURVE_FILE.value.format(file_path=file_path)
        if fcurve_data:
            with open(fcurve_file_path, 'w') as fcurves_file:
                json.dump(fcurve_data, fcurves_file)

    properties.asset_data[properties.asset_id]['fcurve_file_path'] = fcurve_file_path


def export_file(properties, lod=0):
    """
    Calls the blender export operator with specific settings.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool lod: Whether the exported mesh is a lod.
    """
    asset_data = properties.asset_data[properties.asset_id]
    file_path = asset_data['file_path']
    if lod != 0:
        file_path = asset_data['lods'][str(lod)]

    # gets the original position and sets the objects position according to the selected properties.
    original_positions = set_selected_objects_to_center(properties)

    # change the scene scale and scale the rig objects and get their original context
    context = scale_rig_objects(properties)

    # combine all child meshes if option is on
    selected_object_names, duplicate_data = utilities.combine_child_meshes(properties)

    # if the folder does not exists create it
    folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # export the fbx file
    export_fbx_file(file_path, properties)

    # remove duplicate objects
    utilities.remove_data(duplicate_data)

    # restore selection
    utilities.set_selected_objects(selected_object_names)

    # restores original positions
    set_object_positions(original_positions)

    # restores the original rig objects
    restore_rig_objects(context, properties)


def get_asset_sockets(asset_name, properties):
    """
    Gets the socket under the given asset.

    :param str asset_name: The name of the asset to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    socket_data = {}
    mesh_object = bpy.data.objects.get(asset_name)
    if mesh_object:
        for child in mesh_object.children:
            if child.type == 'EMPTY' and child.name.startswith(f'{PreFixToken.SOCKET.value}_'):
                name = utilities.get_asset_name(child.name.replace(f'{PreFixToken.SOCKET.value}_', ''), properties)
                socket_data[name] = {
                    'relative_location': utilities.convert_blender_to_unreal_location(child.matrix_local.translation),
                    'relative_rotation': [math.degrees(i) for i in child.matrix_local.to_euler()],
                    'relative_scale': child.matrix_local.to_scale()[:]
                }
    return socket_data


@utilities.track_progress(message='Exporting mesh "{attribute}"...', attribute='file_path')
def export_mesh(asset_id, mesh_object, properties, lod=0):
    """
    Exports a mesh to a file.

    :param str asset_id: The unique id of the asset.
    :param object mesh_object: A object of type mesh.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool lod: Whether the exported mesh is a lod.
    :return str: The fbx file path of the exported mesh
    """
    # set the current asset id
    properties.asset_id = asset_id

    # run the pre mesh export extensions
    if lod == 0:
        extension.run_operators(ExtensionOperators.PRE_MESH_EXPORT.value)

    # deselect everything
    utilities.deselect_all_objects()

    mesh_object_name = mesh_object.name

    # select the scene object
    mesh_object.select_set(True)

    # select any rigs this object is parented too
    set_parent_rig_selection(mesh_object, properties)

    # select collision meshes
    utilities.select_asset_collisions(mesh_object_name, properties)

    # export selection to an fbx file
    export_file(properties, lod)

    # deselect the exported object
    mesh_object = bpy.data.objects.get(mesh_object_name)
    if mesh_object:
        mesh_object.select_set(False)

    # run the post mesh export extensions
    if lod == 0:
        extension.run_operators(ExtensionOperators.POST_MESH_EXPORT.value)


@utilities.track_progress(message='Exporting animation "{attribute}"...', attribute='file_path')
def export_animation(asset_id, rig_object, action_name, properties):
    """
    Exports a single action from a rig object to a file.

    :param str asset_id: The unique id of the asset.
    :param object rig_object: A object of type armature with animation data.
    :param str action_name: The name of the action to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return str: The fbx file path of the exported action
    """
    # set the current asset id
    properties.asset_id = asset_id

    # run the pre animation export extensions
    extension.run_operators(ExtensionOperators.PRE_ANIMATION_EXPORT.value)

    if rig_object.animation_data:
        rig_object.animation_data.action = None

    # deselect everything
    utilities.deselect_all_objects()

    # select the scene object
    rig_object.select_set(True)

    # un-mute the action
    utilities.set_action_mute_value(rig_object, action_name, False)

    # export the action
    export_file(properties)

    # export custom property fcurves
    export_custom_property_fcurves(action_name, properties)

    # ensure the rigs are in rest position before setting the mute values
    utilities.clear_pose(rig_object)

    # mute the action
    utilities.set_action_mute_value(rig_object, action_name, True)

    # run the post animation export extensions
    extension.run_operators(ExtensionOperators.POST_ANIMATION_EXPORT.value)


def create_animation_data(rig_objects, properties):
    """
    Collects and creates all the action data needed for an animation import.

    :param list rig_objects: A list of rig objects.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries containing the action import data.
    """
    animation_data = {}

    if properties.import_animations:
        # get the asset data for the skeletal animations
        for rig_object in rig_objects:

            # if auto stash active action option is on
            if properties.auto_stash_active_action:
                # stash the active animation data in the rig object's nla strips
                utilities.stash_animation_data(rig_object)

            # get the names of all the actions to export
            action_names = utilities.get_action_names(rig_object, all_actions=properties.export_all_actions)

            # mute all actions
            utilities.set_all_action_mute_values(rig_object, mute=True)

            # export the actions and create the action import data
            for action_name in action_names:
                file_path = get_file_path(action_name, properties, AssetTypes.ANIMATION)
                asset_name = utilities.get_asset_name(action_name, properties)

                # export the animation
                asset_id = utilities.get_asset_id(file_path)
                export_animation(asset_id, rig_object, action_name, properties)

                # save the import data
                asset_id = utilities.get_asset_id(file_path)
                animation_data[asset_id] = {
                    'asset_type': AssetTypes.ANIMATION,
                    'file_path': file_path,
                    'asset_path': f'{properties.unreal_animation_folder_path}{asset_name}',
                    'asset_folder': properties.unreal_animation_folder_path,
                    'skeleton_asset_path': utilities.get_skeleton_asset_path(rig_object, properties),
                    'animation': True
                }

    return animation_data


def create_mesh_data(mesh_objects, rig_objects, properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param list mesh_objects: A list of mesh objects.
    :param list rig_objects: A list of rig objects.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries containing the mesh import data.
    """
    mesh_data = {}
    previous_asset_names = []

    # get the asset data for the scene objects
    for mesh_object in mesh_objects:
        already_exported = False
        asset_name = utilities.get_asset_name(mesh_object.name, properties)

        # only export meshes that are lod 0
        if properties.import_lods and utilities.get_lod_index(mesh_object.name, properties) != 0:
            continue

        # check each previous asset name for its lod mesh
        for previous_asset in previous_asset_names:
            if utilities.is_lod_of(previous_asset, mesh_object.name, properties):
                already_exported = True
                break

        if not already_exported:
            # get file path
            file_path = get_file_path(mesh_object.name, properties, AssetTypes.MESH, lod=False)
            # export the object
            asset_id = utilities.get_asset_id(file_path)
            export_mesh(asset_id, mesh_object, properties)
            import_path = utilities.get_full_import_path(mesh_object, properties, AssetTypes.MESH)

            # save the asset data
            mesh_data[asset_id] = {
                'asset_type': AssetTypes.MESH,
                'file_path': file_path,
                'asset_folder': import_path,
                'asset_path': f'{import_path}{asset_name}',
                'skeletal_mesh': bool(rig_objects),
                'skeleton_asset_path': properties.unreal_skeleton_asset_path,
                'lods': export_lods(asset_id, asset_name, properties),
                'sockets': get_asset_sockets(mesh_object.name, properties),
                'import_mesh': True
            }
            previous_asset_names.append(asset_name)

    return mesh_data


def create_asset_data(properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get the mesh and rig objects from their collections
    mesh_objects = utilities.get_from_collection(AssetTypes.MESH, properties)
    rig_objects = utilities.get_from_collection(AssetTypes.SKELETON, properties)

    # if the combine meshes option is on, get only meshes with unique armature parents
    mesh_objects = utilities.get_unique_parent_mesh_objects(rig_objects, mesh_objects, properties)

    # get the asset data for all the mesh objects
    mesh_data = create_mesh_data(mesh_objects, rig_objects, properties)

    # get the asset data for all the actions on the rig objects
    animation_data = create_animation_data(rig_objects, properties)

    # update the properties with the asset data
    properties.asset_data.update({**mesh_data, **animation_data})


def send2ue(properties):
    """
    Sends assets to unreal.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # clear the asset_data and current id
    properties.asset_id = ''
    properties.asset_data.clear()

    # update the server timeout value
    utilities.set_unreal_rpc_timeout()

    # if there are no failed validations continue
    validation_manager = validations.ValidationManager(properties)
    if validation_manager.run():
        # create the asset data
        create_asset_data(properties)
        ingest.asset(properties)

    # clear the current id
    properties.asset_id = ''
