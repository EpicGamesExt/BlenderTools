# Copyright Epic Games, Inc. All Rights Reserved.

import json
import math
import os
import bpy
from . import utilities, validations, settings, ingest, extension, io
from ..constants import BlenderTypes, UnrealTypes, FileTypes, PreFixToken, ToolInfo, ExtensionTasks


def get_file_path(asset_name, properties, asset_type, lod=False, file_extension='fbx'):
    """
    Gets the export path if it doesn't already exist.  Then it returns the full path.

    :param str asset_name: The name of the asset that will be exported to a file.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :param str asset_type: The unreal type of data being exported.
    :param bool lod: Whether to use the lod post fix of not.
    :param str file_extension: The file extension in the file path.
    :return str: The full path to the file.
    """
    export_folder = utilities.get_export_folder_path(properties, asset_type)
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
        mesh_objects = utilities.get_from_collection(BlenderTypes.MESH)
        for mesh_object in mesh_objects:
            if utilities.is_lod_of(asset_name, mesh_object.name, properties):
                if mesh_object.name != utilities.get_lod0_name(mesh_object.name, properties):
                    lod_index = utilities.get_lod_index(mesh_object.name, properties)
                    asset_type = utilities.get_mesh_unreal_type(mesh_object)
                    file_path = get_file_path(mesh_object.name, properties, asset_type, lod=True)
                    export_mesh(asset_id, mesh_object, properties, lod=lod_index)
                    if file_path:
                        lods[str(lod_index)] = file_path
        return lods


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
        if rig_object in utilities.get_from_collection(BlenderTypes.SKELETON):
            # select the parent object
            rig_object.select_set(True)

            # call the function again to see if this object has a parent that
            set_parent_rig_selection(rig_object, properties)
    return rig_object


def export_fbx_file(file_path, export_settings):
    """
    Exports a fbx file.

    :param str file_path: A file path where the file will be exported.
    :param dict export_settings: A dictionary of blender export settings for the specific file type.
    """
    io.fbx.export(
        filepath=file_path,
        use_selection=True,
        bake_anim_use_nla_strips=True,
        bake_anim_use_all_actions=False,
        object_types={'ARMATURE', 'MESH', 'EMPTY'},
        **export_settings
    )


def export_alembic_file(file_path, export_settings):
    """
    Exports an abc file.

    :param str file_path: A file path where the file will be exported.
    :param dict export_settings: A dictionary of blender export settings for the specific file type.
    """
    bpy.ops.wm.alembic_export(
        filepath=file_path,
        end=1,
        selected=True,
        visible_objects_only=True,
        export_hair=True,
        export_particles=False,
        evaluation_mode='RENDER',
        **export_settings
    )


def export_custom_property_fcurves(action_name, properties):
    """
    Exports custom property fcurves to a file.

    :param str action_name: The name of the action to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    asset_id = bpy.context.window_manager.send2ue.asset_id
    file_path = bpy.context.window_manager.send2ue.asset_data[asset_id]['file_path']

    fcurve_file_path = None
    fcurve_data = utilities.get_custom_property_fcurve_data(action_name)
    if fcurve_data and properties.export_custom_property_fcurves:
        file_path, file_extension = os.path.splitext(file_path)
        fcurve_file_path = ToolInfo.FCURVE_FILE.value.format(file_path=file_path)
        if fcurve_data:
            with open(fcurve_file_path, 'w') as fcurves_file:
                json.dump(fcurve_data, fcurves_file)

    bpy.context.window_manager.send2ue.asset_data[asset_id]['fcurve_file_path'] = fcurve_file_path


def export_file(properties, lod=0, file_type=FileTypes.FBX):
    """
    Calls the blender export operator with specific settings.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool lod: Whether the exported mesh is a lod.
    :param str file_type: File type of the export.
    """
    asset_id = bpy.context.window_manager.send2ue.asset_id
    asset_data = bpy.context.window_manager.send2ue.asset_data[asset_id]

    # skip if specified
    if asset_data.get('skip'):
        return

    file_path = asset_data.get('file_path')
    if lod != 0:
        file_path = asset_data['lods'][str(lod)]

    # if the folder does not exist create it
    folder_path = os.path.abspath(os.path.join(file_path, os.pardir))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # get blender export settings
    export_settings = {}
    for group_name, group_data in settings.get_settings_by_path('blender-export_method', file_type).items():
        prefix = settings.get_generated_prefix(f'blender-export_method-{file_type}', group_name)
        for attribute_name in group_data.keys():
            export_settings[attribute_name] = settings.get_property_by_path(prefix, attribute_name, properties)

    if file_type == FileTypes.FBX:
        export_fbx_file(file_path, export_settings)

    elif file_type == FileTypes.ABC:
        export_alembic_file(file_path, export_settings)


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
                relative_location = utilities.convert_blender_to_unreal_location(
                    child.matrix_local.translation
                )
                relative_rotation = utilities.convert_blender_rotation_to_unreal_rotation(
                    child.rotation_euler
                )
                socket_data[name] = {
                    'relative_location': relative_location,
                    'relative_rotation': relative_rotation,
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
    """
    # deselect everything
    utilities.deselect_all_objects()

    # run the pre mesh export extensions
    if lod == 0:
        extension.run_extension_tasks(ExtensionTasks.PRE_MESH_EXPORT.value)

    # select the scene object
    mesh_object.select_set(True)

    # select any rigs this object is parented too
    set_parent_rig_selection(mesh_object, properties)

    # select collision meshes
    asset_name = utilities.get_asset_name(mesh_object.name, properties)
    utilities.select_asset_collisions(asset_name, properties)

    # Note: this is a weird work around for morph targets not exporting when
    # particle systems are on the mesh. Making them not visible fixes this bug
    existing_display_options = utilities.disable_particles(mesh_object)
    # export selection to a file
    export_file(properties, lod)
    # restore the particle system display options
    utilities.restore_particles(mesh_object, existing_display_options)

    # run the post mesh export extensions
    if lod == 0:
        extension.run_extension_tasks(ExtensionTasks.POST_MESH_EXPORT.value)


@utilities.track_progress(message='Exporting animation "{attribute}"...', attribute='file_path')
def export_animation(asset_id, rig_object, action_name, properties):
    """
    Exports a single action from a rig object to a file.

    :param str asset_id: The unique id of the asset.
    :param object rig_object: A object of type armature with animation data.
    :param str action_name: The name of the action to export.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # run the pre animation export extensions
    extension.run_extension_tasks(ExtensionTasks.PRE_ANIMATION_EXPORT.value)

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
    extension.run_extension_tasks(ExtensionTasks.POST_ANIMATION_EXPORT.value)


@utilities.track_progress(message='Exporting curves/hair particle system "{attribute}"...', attribute='file_path')
def export_hair(asset_id, properties):
    """
    Exports a mesh to a file.

    :param str asset_id: The unique id of the asset.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    asset_data = bpy.context.window_manager.send2ue.asset_data[asset_id]

    # deselect everything
    utilities.deselect_all_objects()

    # clear animation transformations prior to export so groom exports with no distortion
    for scene_object in bpy.data.objects:
        if scene_object.animation_data:
            if scene_object.animation_data.action:
                scene_object.animation_data.action = None
        utilities.set_all_action_mute_values(scene_object, mute=True)
        if scene_object.type == BlenderTypes.SKELETON:
            utilities.clear_pose(scene_object)

    object_type = asset_data.get('_object_type')
    object_name = asset_data.get('_object_name')

    mesh_object = utilities.get_mesh_object_for_groom_name(object_name)

    # get all particle systems display options on all mesh objects
    all_existing_display_options = utilities.get_all_particles_display_options()

    if object_type == BlenderTypes.CURVES:
        curves_object = bpy.data.objects.get(object_name)
        utilities.convert_curve_to_particle_system(curves_object)

    # turn show_emitter off in particle system render settings
    mesh_object.show_instancer_for_render = False

    # display only the particle to export
    utilities.set_particles_display_option(mesh_object, False)
    utilities.set_particles_display_option(mesh_object, True, only=object_name)

    # select the mesh to export
    mesh_object.select_set(True)

    # run the pre groom export extensions
    extension.run_extension_tasks(ExtensionTasks.PRE_GROOM_EXPORT.value)

    # export the abc file
    export_file(properties, file_type=FileTypes.ABC)

    # restore all the display options on all objects
    utilities.restore_all_particles(all_existing_display_options)

    # run the pre groom export extensions
    extension.run_extension_tasks(ExtensionTasks.POST_GROOM_EXPORT.value)


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
                file_path = get_file_path(action_name, properties, UnrealTypes.ANIM_SEQUENCE)
                asset_name = utilities.get_asset_name(action_name, properties)

                # export the animation
                asset_id = utilities.get_asset_id(file_path)
                export_animation(asset_id, rig_object, action_name, properties)

                # save the import data
                asset_id = utilities.get_asset_id(file_path)
                animation_data[asset_id] = {
                    '_asset_type': UnrealTypes.ANIM_SEQUENCE,
                    '_action_name': action_name,
                    '_armature_object_name': rig_object.name,
                    'file_path': file_path,
                    'asset_path': f'{properties.unreal_animation_folder_path}{asset_name}',
                    'asset_folder': properties.unreal_animation_folder_path,
                    'skeleton_asset_path': utilities.get_skeleton_asset_path(rig_object, properties),
                    'skip': False
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
    if not properties.import_meshes:
        return mesh_data

    previous_asset_names = []

    # get the asset data for the scene objects
    for mesh_object in mesh_objects:
        already_exported = False
        asset_name = utilities.get_asset_name(mesh_object.name, properties)

        # only export meshes that are lod 0
        if properties.import_lods and utilities.get_lod_index(mesh_object.name, properties) != 0:
            continue

        # TODO: don't think this block is needed, how would the code ever reach this block since all LODs except LOD0 are skipped?
        # check each previous asset name for its lod mesh
        for previous_asset in previous_asset_names:
            if utilities.is_lod_of(previous_asset, mesh_object.name, properties):
                already_exported = True
                break

        if not already_exported:
            asset_type = utilities.get_mesh_unreal_type(mesh_object)
            # get file path
            file_path = get_file_path(mesh_object.name, properties, asset_type, lod=False)
            # export the object
            asset_id = utilities.get_asset_id(file_path)
            export_mesh(asset_id, mesh_object, properties)
            import_path = utilities.get_import_path(properties, asset_type)

            # save the asset data
            mesh_data[asset_id] = {
                '_asset_type': asset_type,
                '_mesh_object_name': mesh_object.name,
                'file_path': file_path,
                'asset_folder': import_path,
                'asset_path': f'{import_path}{asset_name}',
                'skeleton_asset_path': properties.unreal_skeleton_asset_path,
                'lods': export_lods(asset_id, asset_name, properties),
                'sockets': get_asset_sockets(mesh_object.name, properties),
                'skip': False
            }
            previous_asset_names.append(asset_name)

    return mesh_data


def create_groom_data(hair_objects, properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param list hair_objects: A list of hair objects that can be either curve objects or particle systems.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries containing the groom import data.
    """

    groom_data = {}
    if properties.import_grooms:
        for hair_object in hair_objects:
            if type(hair_object) == bpy.types.Object:
                object_type = hair_object.type
                particle_object_name = None
            else:
                # the object type is set to the particle object rather then the particle system
                object_type = hair_object.settings.type
                particle_object_name = hair_object.settings.name

            file_path = get_file_path(
                hair_object.name,
                properties,
                UnrealTypes.GROOM,
                lod=False,
                file_extension='abc'
            )
            asset_id = utilities.get_asset_id(file_path)
            import_path = utilities.get_import_path(properties, UnrealTypes.GROOM)
            asset_name = utilities.get_asset_name(hair_object.name, properties)

            groom_data[asset_id] = {
                '_asset_type': UnrealTypes.GROOM,
                '_object_name': hair_object.name,
                '_particle_object_name': particle_object_name,
                '_object_type': object_type,
                'file_path': file_path,
                'asset_folder': import_path,
                'asset_path': f'{import_path}{asset_name}',
                'skip': False
            }
            # export particle hair systems as alembic file
            export_hair(asset_id, properties)

    return groom_data


def create_asset_data(properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get the mesh and rig objects from their collections
    mesh_objects = utilities.get_from_collection(BlenderTypes.MESH)
    rig_objects = utilities.get_from_collection(BlenderTypes.SKELETON)
    hair_objects = utilities.get_hair_objects(properties)

    # filter the rigs and meshes based on the extension filter methods
    rig_objects, mesh_objects, hair_objects = extension.run_extension_filters(
        rig_objects,
        mesh_objects,
        hair_objects
    )

    # get the asset data for all the mesh objects
    mesh_data = create_mesh_data(mesh_objects, rig_objects, properties)

    # get the asset data for all the actions on the rig objects
    animation_data = create_animation_data(rig_objects, properties)

    # get the asset data for all the hair systems
    hair_data = create_groom_data(hair_objects, properties)

    # update the properties with the asset data
    bpy.context.window_manager.send2ue.asset_data.update({**mesh_data, **animation_data, **hair_data})


def send2ue(properties):
    """
    Sends assets to unreal.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get out of local view
    utilities.escape_local_view()

    # clear the asset_data and current id
    bpy.context.window_manager.send2ue.asset_id = ''
    bpy.context.window_manager.send2ue.asset_data.clear()

    # if there are no failed validations continue
    validation_manager = validations.ValidationManager(properties)
    if validation_manager.run():
        # create the asset data
        create_asset_data(properties)
        ingest.assets(properties)
