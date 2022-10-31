# Copyright Epic Games, Inc. All Rights Reserved.

import json
import math
import os
import re
import bpy
from . import utilities, validations, settings, formatting, ingest, extension
from ..constants import PathModes, BlenderTypes, UnrealTypes, FileTypes, PreFixToken, ToolInfo, ExtensionTasks


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
        mesh_objects = utilities.get_from_collection(BlenderTypes.MESH, properties)
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


def get_visible_particle_modifiers(mesh_object, properties, p_type=None):
    """
    Gets particle modifiers and the associated particle systems (that are visible by user visibility setting)
    on a mesh as a list of tuples.

    :param object mesh_object: A mesh object
    :param str p_type: The type of the particle is either 'HAIR' or 'EMITTER'.
    :param PropertyData properties: A property data instance that contains all property values of the tool.
    :return list(modifier, particle_system): A list of tuples that contain the particle modifier and particle system.
    """
    # dynamically uses what the user selected in export settings ('RENDER' or 'VIEWPORT') to decide visibility
    context = properties.blender.export_method.abc.scene_options.evaluation_mode
    return utilities.get_particle_modifiers(mesh_object, p_type, visible=context)


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
        if rig_object in utilities.get_from_collection(BlenderTypes.SKELETON, properties):
            # select the parent object
            rig_object.select_set(True)

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
    mesh_objects = utilities.get_from_collection(BlenderTypes.MESH, properties)

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

        # run pre bone scale task
        extension.run_extension_tasks(ExtensionTasks.PRE_BONE_SCALE.value)

        # duplicate objects
        context = duplicate_objects_for_export(scene_scale, scale_factor, context, properties)

        for duplicate_object in context['duplicate_objects']:
            if duplicate_object.type == 'ARMATURE':
                # rename the duplicated objects and save the original object references to the context
                context = rename_duplicate_object(duplicate_object, context, properties)

                # set each object in a armature modifier to a parent
                set_armatures_as_parents(properties)

                # fix the armature scale and its animation and save that information to the context
                context = fix_armature_scale(duplicate_object, scale_factor, context)

        # run post bone scale task
        extension.run_extension_tasks(ExtensionTasks.MID_BONE_SCALE.value)

        # restore the duplicate object selection for the export
        for duplicate_object in context['duplicate_objects']:
            duplicate_object.select_set(True)

    return context


def restore_rig_objects(context, properties):
    """
    This function takes the previous context of the scene scale and rig objects and sets them to the values in
    the context dictionary.

    :param dict context: The original context of the scene scale and its selected objects before changes occurred.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    if properties.automatically_scale_bones and context:
        scale_factor = bpy.context.scene.unit_settings.scale_length / context['scene_scale']

        # run post bone scale task
        extension.run_extension_tasks(ExtensionTasks.POST_BONE_SCALE.value)

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


def export_fbx_file(file_path, export_settings):
    """
    Exports a fbx file.

    :param str file_path: A file path where the file will be exported.
    :param dict export_settings: A dictionary of blender export settings for the specific file type.
    """
    bpy.ops.export_scene.fbx(
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


def export_file(properties, lod=0, file_type=FileTypes.FBX, asset_data=None):
    """
    Calls the blender export operator with specific settings.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool lod: Whether the exported mesh is a lod.
    :param str file_type: File type of the export.
    :param dict asset_data: A mutable dictionary of asset data for the current asset.
    """
    if not asset_data:
        asset_id = bpy.context.window_manager.send2ue.asset_id
        asset_data = bpy.context.window_manager.send2ue.asset_data[asset_id]

    file_path = asset_data.get('file_path')
    if lod != 0:
        file_path = asset_data['lods'][str(lod)]

    # if the folder does not exists create it
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
        # change the scene scale and scale the rig objects and get their original context
        context = scale_rig_objects(properties)

        export_fbx_file(file_path, export_settings)

        # restores the original rig objects
        restore_rig_objects(context, properties)

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

    # export selection to a file
    export_file(properties, lod)

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
def export_hair(asset_id, mesh_object, properties):
    """
    Exports a mesh to a file.

    :param str asset_id: The unique id of the asset.
    :param object mesh_object: A object of type mesh.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # deselect everything
    utilities.deselect_all_objects()

    # run the pre groom export extensions
    extension.run_extension_tasks(ExtensionTasks.PRE_GROOM_EXPORT.value)

    asset_data = bpy.context.window_manager.send2ue.asset_data[asset_id]

    # only export if asset_data contains groom attribute (indicates there is hair present on a mesh)
    if asset_data.get('groom'):
        # select the scene object if there is particle systems present
        if len(mesh_object.particle_systems) > 0:
            mesh_object.select_set(True)

        # export the abc file
        export_file(properties, file_type=FileTypes.ABC)

        # run the pre groom export extensions
        extension.run_extension_tasks(ExtensionTasks.POST_GROOM_EXPORT.value)

        # delete particle systems that were converted from curves objects
        curves_object_names = asset_data['_converted_curves']
        utilities.remove_particle_systems(curves_object_names, [mesh_object])


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
                file_path = get_file_path(action_name, properties, UnrealTypes.ANIMATION)
                asset_name = utilities.get_asset_name(action_name, properties)

                # export the animation
                asset_id = utilities.get_asset_id(file_path)
                export_animation(asset_id, rig_object, action_name, properties)

                # save the import data
                asset_id = utilities.get_asset_id(file_path)
                animation_data[asset_id] = {
                    '_asset_type': UnrealTypes.ANIMATION,
                    '_action_name': action_name,
                    '_armature_object_name': rig_object.name,
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
                'skeletal_mesh': bool(rig_objects),
                'skeleton_asset_path': properties.unreal_skeleton_asset_path,
                'lods': export_lods(asset_id, asset_name, properties),
                'sockets': get_asset_sockets(mesh_object.name, properties),
                'import_mesh': True
            }
            previous_asset_names.append(asset_name)

    return mesh_data


def create_groom_data(mesh_objects, curves_objects, rig_objects, properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param list mesh_objects: A list of mesh objects.
    :param list curves_objects: A list of curves objects.
    :param list rig_objects: A list of armature objects.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries containing the groom import data.
    """
    groom_data = {}
    if not properties.import_grooms:
        return groom_data
    # convert curves objects to particle systems and store the names of the converted curves objects
    curves_object_names = utilities.convert_curves_to_particle_systems(curves_objects)

    # clear animation transformations prior to export, so groom exports with no distortion
    for rig_object in rig_objects:
        if rig_object.animation_data.action:
            rig_object.animation_data.action = None
        utilities.set_all_action_mute_values(rig_object, mute=True)
        utilities.clear_pose(rig_object)

    for mesh_object in mesh_objects:
        # only export particle systems on meshes that are lod 0 if lod option is on
        if properties.import_lods and utilities.get_lod_index(mesh_object.name, properties) != 0:
            continue
        # turn show_emitter off in particle system render settings
        mesh_object.show_instancer_for_render = False

        # get all particle systems of type 'HAIR' and its modifier on the current mesh
        hair_systems = get_visible_particle_modifiers(mesh_object, properties, p_type=BlenderTypes.PARTICLE_HAIR)

        if len(hair_systems) > 0:
            groom_systems_data = {}

            # get head particle from the particle system list sorted by creation order
            hair_particles = list(dict(hair_systems).values())
            head_particle = utilities.get_particle_systems(
                mesh_object, p_type=BlenderTypes.PARTICLE_HAIR, index=0, exclusive_list=hair_particles
            )

            # populate groom_systems_data dictionary, storing assets data of particle systems on the current mesh
            for modifier, particle in hair_systems:
                # get file path and asset id
                file_path = get_file_path(particle.name, properties, UnrealTypes.GROOM, lod=False, file_extension='abc')
                asset_id = utilities.get_asset_id(file_path)
                # create groom asset data in groom_systems_data dictionary
                groom_systems_data[asset_id] = create_groom_system_data(
                    properties,
                    particle.name,
                    mesh_object.name,
                    modifier.name
                )
                # if this is the head particle, add created groom asset data to groom_data dictionary to be returned
                if particle == head_particle:
                    groom_data[asset_id] = groom_systems_data[asset_id].copy()
                    head_particle_id = asset_id

            # append groom_systems_data dictionary as an attribute to head particle's asset data
            groom_data[head_particle_id].update({
                '_groom_systems_data': groom_systems_data,
                '_converted_curves': curves_object_names
            })
            # export particle hair systems as alembic file
            export_hair(head_particle_id, mesh_object, properties)

        # when there is no hair systems surfaced on the current mesh
        else:
            temp_path = get_file_path(mesh_object.name, properties, UnrealTypes.GROOM, lod=False, file_extension='abc')
            asset_id = utilities.get_asset_id(temp_path)

            # this is for extensions that might use pre groom export callbacks to populate asset data
            groom_data[asset_id] = {
                '_asset_type': UnrealTypes.GROOM,
                '_mesh_object_name': mesh_object.name,
                '_converted_curves': curves_object_names
            }
            # export particle hair systems as alembic file
            export_hair(asset_id, mesh_object, properties)

    return groom_data


def create_groom_system_data(properties, hair_name, mesh_object_name=None, modifier_name=None):
    """
    Returns a dictionary that is the asset data for a groom system.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param str hair_name: the name of the particle system.
    :param str mesh_object_name: the name of the mesh that the particle system is surfaced on.
    :param str modifier_name: the name of the modifier controlling the particle system.
    :return dict: A dictionary of groom import data.
    """
    groom_import_path = utilities.get_import_path(properties, UnrealTypes.GROOM)
    groom_asset_name = utilities.get_asset_name(hair_name, properties)

    file_path = get_file_path(hair_name, properties, UnrealTypes.GROOM, lod=False, file_extension='abc')

    asset_data = {
        '_asset_type': UnrealTypes.GROOM,
        '_hair_particle_name': hair_name,
        'file_path': file_path,
        'asset_folder': groom_import_path,
        'asset_path': f'{groom_import_path}{groom_asset_name}',
        'groom': True
    }

    if mesh_object_name:
        mesh_import_path = utilities.get_import_path(properties, UnrealTypes.SKELETAL_MESH)
        mesh_asset_name = utilities.get_asset_name(mesh_object_name, properties)
        asset_data.update({
            '_mesh_object_name': mesh_object_name,
            'mesh_asset_path': f'{mesh_import_path}{mesh_asset_name}'
        })

    if modifier_name:
        asset_data.update({
            '_modifier_name': modifier_name
        })
    return asset_data


def create_asset_data(properties):
    """
    Collects and creates all the asset data needed for the import process.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get the mesh and rig objects from their collections
    mesh_objects = utilities.get_from_collection(BlenderTypes.MESH, properties)
    rig_objects = utilities.get_from_collection(BlenderTypes.SKELETON, properties)
    curves_objects = utilities.get_from_collection(BlenderTypes.CURVES, properties)

    # filter the rigs and meshes based on the extension filter methods
    rig_objects, mesh_objects, groom_surface_objects = extension.run_extension_filters(
        rig_objects,
        mesh_objects
    )

    # get the asset data for all the mesh objects
    mesh_data = create_mesh_data(mesh_objects, rig_objects, properties)

    # get the asset data for all the actions on the rig objects
    animation_data = create_animation_data(rig_objects, properties)

    # get the asset data for all the hair systems
    hair_data = create_groom_data(groom_surface_objects, curves_objects, rig_objects, properties)

    # update the properties with the asset data
    bpy.context.window_manager.send2ue.asset_data.update({**mesh_data, **animation_data, **hair_data})


def send2ue(properties):
    """
    Sends assets to unreal.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # clear the asset_data and current id
    bpy.context.window_manager.send2ue.asset_id = ''
    bpy.context.window_manager.send2ue.asset_data.clear()

    # if there are no failed validations continue
    validation_manager = validations.ValidationManager(properties)
    if validation_manager.run():
        # create the asset data
        create_asset_data(properties)
        ingest.assets(properties)
