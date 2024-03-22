import os
import bpy
import numpy as np
from ..utilities import report_error
from mathutils import Vector
from importlib.machinery import SourceFileLoader

SCALE_FACTOR = 100


def export(**keywords):
    """
    Note that this function imports the blender FBX addon's module and monkey patches
    some functions to fix the scale factor and world origins of the objects, so that they import
    nicely into unreal engine.

    The functions below have been tweaked from their originals here:
    https://github.com/blender/blender-addons/blob/master/io_scene_fbx/export_fbx_bin.py
    """
    import addon_utils
    addons = {os.path.basename(os.path.dirname(module.__file__)): module.__file__ for module in addon_utils.modules()}
    addon_folder_path = os.path.dirname(addons.get('io_scene_fbx'))

    # this load the io_scene_fbx module from the blender FBX addon
    try:
        SourceFileLoader('io_scene_fbx', os.path.join(addon_folder_path, '__init__.py')).load_module()
    except RuntimeError as error:
        print(error)

    import io_scene_fbx.export_fbx_bin as export_fbx_bin
    from io_scene_fbx.export_fbx_bin import (
        fbx_data_bindpose_element,
        AnimationCurveNodeWrapper
    )
    from bpy_extras.io_utils import axis_conversion
    from io_scene_fbx.fbx_utils import (
        FBX_MODELS_VERSION,
        FBX_POSE_BIND_VERSION,
        FBX_DEFORMER_SKIN_VERSION,
        FBX_DEFORMER_CLUSTER_VERSION,
        BLENDER_OBJECT_TYPES_MESHLIKE,
        FBX_KTIME,
        units_convertor_iter,
        matrix4_to_array,
        get_fbx_uuid_from_key,
        get_blenderID_name,
        get_blender_bindpose_key,
        get_blender_anim_stack_key,
        get_blender_anim_layer_key,
        elem_empty,
        elem_data_single_bool,
        elem_data_single_int32,
        elem_data_single_int64,
        elem_data_single_float64,
        elem_data_single_string,
        elem_data_single_int32_array,
        elem_data_single_float64_array,
        elem_properties,
        elem_props_template_init,
        elem_props_template_set,
        elem_props_template_finalize,
        fbx_name_class
    )
    
    # Added version check to import new elem data type added in 4.0. Shading element was updated to use char instead of bool
    if bpy.app.version >= (4,0,0): 
        from io_scene_fbx.fbx_utils import (
            elem_data_single_char
        )

    convert_rad_to_deg_iter = units_convertor_iter("radian", "degree")

    from io_scene_fbx.export_fbx_bin import fbx_data_element_custom_properties

    def fbx_animations_do(scene_data, ref_id, f_start, f_end, start_zero, objects=None, force_keep=False):
        """
        Generate animation data (a single AnimStack) from objects, for a given frame range.
        """
        bake_step = scene_data.settings.bake_anim_step
        simplify_fac = scene_data.settings.bake_anim_simplify_factor
        scene = scene_data.scene
        depsgraph = scene_data.depsgraph
        force_keying = scene_data.settings.bake_anim_use_all_bones
        force_sek = scene_data.settings.bake_anim_force_startend_keying
        gscale = scene_data.settings.global_scale

        if objects is not None:
            # Add bones and duplis!
            for ob_obj in tuple(objects):
                if not ob_obj.is_object:
                    continue
                if ob_obj.type == 'ARMATURE':
                    objects |= {bo_obj for bo_obj in ob_obj.bones if bo_obj in scene_data.objects}
                for dp_obj in ob_obj.dupli_list_gen(depsgraph):
                    if dp_obj in scene_data.objects:
                        objects.add(dp_obj)
        else:
            objects = scene_data.objects

        back_currframe = scene.frame_current
        animdata_ob = {}
        p_rots = {}

        for ob_obj in objects:
            if ob_obj.parented_to_armature:
                continue
            ACNW = AnimationCurveNodeWrapper
            loc, rot, scale, _m, _mr = ob_obj.fbx_object_tx(scene_data)
            rot_deg = tuple(convert_rad_to_deg_iter(rot))
            force_key = (simplify_fac == 0.0) or (ob_obj.is_bone and force_keying)

            animdata_ob[ob_obj] = (ACNW(ob_obj.key, 'LCL_TRANSLATION', force_key, force_sek, loc),
                                   ACNW(ob_obj.key, 'LCL_ROTATION', force_key, force_sek, rot_deg),
                                   ACNW(ob_obj.key, 'LCL_SCALING', force_key, force_sek, scale))
            p_rots[ob_obj] = rot

        force_key = (simplify_fac == 0.0)
        animdata_shapes = {}

        for me, (me_key, _shapes_key, shapes) in scene_data.data_deformers_shape.items():
            # Ignore absolute shape keys for now!
            if not me.shape_keys.use_relative:
                continue
            for shape, (channel_key, geom_key, _shape_verts_co, _shape_verts_idx) in shapes.items():
                acnode = AnimationCurveNodeWrapper(channel_key, 'SHAPE_KEY', force_key, force_sek, (0.0,))
                # Sooooo happy to have to twist again like a mad snake... Yes, we need to write those curves twice. :/
                acnode.add_group(me_key, shape.name, shape.name, (shape.name,))
                animdata_shapes[channel_key] = (acnode, me, shape)

        animdata_cameras = {}
        for cam_obj, cam_key in scene_data.data_cameras.items():
            cam = cam_obj.bdata.data
            acnode_lens = AnimationCurveNodeWrapper(cam_key, 'CAMERA_FOCAL', force_key, force_sek, (cam.lens,))
            acnode_focus_distance = AnimationCurveNodeWrapper(cam_key, 'CAMERA_FOCUS_DISTANCE', force_key,
                                                            force_sek, (cam.dof.focus_distance,))
            animdata_cameras[cam_key] = (acnode_lens, acnode_focus_distance, cam)

        # Get all parent bdata of animated dupli instances, so that we can quickly identify which instances in
        # `depsgraph.object_instances` are animated and need their ObjectWrappers' matrices updated each frame.
        dupli_parent_bdata = {dup.get_parent().bdata for dup in animdata_ob if dup.is_dupli}
        has_animated_duplis = bool(dupli_parent_bdata)

        # Initialize keyframe times array. Each AnimationCurveNodeWrapper will share the same instance.
        # `np.arange` excludes the `stop` argument like when using `range`, so we use np.nextafter to get the next
        # representable value after f_end and use that as the `stop` argument instead.
        currframes = np.arange(f_start, np.nextafter(f_end, np.inf), step=bake_step)

        # Convert from Blender time to FBX time.
        fps = scene.render.fps / scene.render.fps_base
        real_currframes = currframes - f_start if start_zero else currframes
        real_currframes = (real_currframes / fps * FBX_KTIME).astype(np.int64)

        # Generator that yields the animated values of each frame in order.
        def frame_values_gen():
            # Precalculate integer frames and subframes.
            int_currframes = currframes.astype(int)
            subframes = currframes - int_currframes

            # Create simpler iterables that return only the values we care about.
            animdata_shapes_only = [shape for _anim_shape, _me, shape in animdata_shapes.values()]
            animdata_cameras_only = [camera for _anim_camera_lens, _anim_camera_focus_distance, camera
                                    in animdata_cameras.values()]
            # Previous frame's rotation for each object in animdata_ob, this will be updated each frame.
            animdata_ob_p_rots = p_rots.values()

            # Iterate through each frame and yield the values for that frame.
            # Iterating .data, the memoryview of an array, is faster than iterating the array directly.
            for int_currframe, subframe in zip(int_currframes.data, subframes.data):
                scene.frame_set(int_currframe, subframe=subframe)

                if has_animated_duplis:
                    # Changing the scene's frame invalidates existing dupli instances. To get the updated matrices of duplis
                    # for this frame, we must get the duplis from the depsgraph again.
                    for dup in depsgraph.object_instances:
                        if (parent := dup.parent) and parent.original in dupli_parent_bdata:
                            # ObjectWrapper caches its instances. Attempting to create a new instance updates the existing
                            # ObjectWrapper instance with the current frame's matrix and then returns the existing instance.
                            ObjectWrapper(dup)
                next_p_rots = []
                for ob_obj, p_rot in zip(animdata_ob, animdata_ob_p_rots):


                    #
                    # send2ue: Scale shennanigans
                    #
                    location_multiple = 100
                    scale_factor = 1
                    # if this curve is the object root then keep its scale at 1
                    if len(str(ob_obj).split('|')) == 1:
                        location_multiple = 1
                        # Todo add to FBX addon
                        scale_factor = SCALE_FACTOR



                    # We compute baked loc/rot/scale for all objects (rot being euler-compat with previous value!).
                    loc, rot, scale, _m, _mr = ob_obj.fbx_object_tx(scene_data, rot_euler_compat=p_rot)


                    #
                    # send2ue: Make location keyframes relative to the armature object
                    #
                    # Todo add to FBX addon
                    # the armature object's position is the reference we use to offset all location keyframes
                    if ob_obj.type == 'ARMATURE':
                        location_offset = loc
                        # subtract the location offset from each location keyframe if the use_object_origin is on
                        if bpy.context.scene.send2ue.use_object_origin:
                            loc = Vector(
                                (loc[0] - location_offset[0], loc[1] - location_offset[1], loc[2] - location_offset[2]))



                    next_p_rots.append(rot)
                    yield from loc * location_multiple # send2ue: Apply translation scalar
                    yield from rot
                    yield from scale / scale_factor # send2ue: Apply scale factor
                animdata_ob_p_rots = next_p_rots
                for shape in animdata_shapes_only:
                    yield shape.value
                for camera in animdata_cameras_only:
                    yield camera.lens
                    yield camera.dof.focus_distance

        # Providing `count` to np.fromiter pre-allocates the array, avoiding extra memory allocations while iterating.
        num_ob_values = len(animdata_ob) * 9  # Location, rotation and scale, each of which have x, y, and z components
        num_shape_values = len(animdata_shapes)  # Only 1 value per shape key
        num_camera_values = len(animdata_cameras) * 2  # Focal length (`.lens`) and focus distance
        num_values_per_frame = num_ob_values + num_shape_values + num_camera_values
        num_frames = len(real_currframes)
        all_values_flat = np.fromiter(frame_values_gen(), dtype=float, count=num_frames * num_values_per_frame)

        # Restore the scene's current frame.
        scene.frame_set(back_currframe, subframe=0.0)

        # View such that each column is all values for a single frame and each row is all values for a single curve.
        all_values = all_values_flat.reshape(num_frames, num_values_per_frame).T
        # Split into views of the arrays for each curve type.
        split_at = [num_ob_values, num_shape_values, num_camera_values]
        # For unequal sized splits, np.split takes indices to split at, which can be acquired through a cumulative sum
        # across the list.
        # The last value isn't needed, because the last split is assumed to go to the end of the array.
        split_at = np.cumsum(split_at[:-1])
        all_ob_values, all_shape_key_values, all_camera_values = np.split(all_values, split_at)

        all_anims = []

        # Set location/rotation/scale curves.
        # Split into equal sized views of the arrays for each object.
        split_into = len(animdata_ob)
        per_ob_values = np.split(all_ob_values, split_into) if split_into > 0 else ()
        for anims, ob_values in zip(animdata_ob.values(), per_ob_values):
            # Split again into equal sized views of the location, rotation and scaling arrays.
            loc_xyz, rot_xyz, sca_xyz = np.split(ob_values, 3)
            # In-place convert from Blender rotation to FBX rotation.
            np.rad2deg(rot_xyz, out=rot_xyz)

            anim_loc, anim_rot, anim_scale = anims
            anim_loc.set_keyframes(real_currframes, loc_xyz)
            anim_rot.set_keyframes(real_currframes, rot_xyz)
            anim_scale.set_keyframes(real_currframes, sca_xyz)
            all_anims.extend(anims)

        # Set shape key curves.
        # There's only one array per shape key, so there's no need to split `all_shape_key_values`.
        for (anim_shape, _me, _shape), shape_key_values in zip(animdata_shapes.values(), all_shape_key_values):
            # In-place convert from Blender Shape Key Value to FBX Deform Percent.
            shape_key_values *= 100.0
            anim_shape.set_keyframes(real_currframes, shape_key_values)
            all_anims.append(anim_shape)

        # Set camera curves.
        # Split into equal sized views of the arrays for each camera.
        split_into = len(animdata_cameras)
        per_camera_values = np.split(all_camera_values, split_into) if split_into > 0 else ()
        zipped = zip(animdata_cameras.values(), per_camera_values)
        for (anim_camera_lens, anim_camera_focus_distance, _camera), (lens_values, focus_distance_values) in zipped:
            # In-place convert from Blender focus distance to FBX.
            focus_distance_values *= (1000 * gscale)
            anim_camera_lens.set_keyframes(real_currframes, lens_values)
            anim_camera_focus_distance.set_keyframes(real_currframes, focus_distance_values)
            all_anims.append(anim_camera_lens)
            all_anims.append(anim_camera_focus_distance)

        animations = {}

        # And now, produce final data (usable by FBX export code)
        for anim in all_anims:
            anim.simplify(simplify_fac, bake_step, force_keep)
            if not anim:
                continue
            for obj_key, group_key, group, fbx_group, fbx_gname in anim.get_final_data(scene, ref_id, force_keep):
                anim_data = animations.setdefault(obj_key, ("dummy_unused_key", {}))
                anim_data[1][fbx_group] = (group_key, group, fbx_gname)

        astack_key = get_blender_anim_stack_key(scene, ref_id)
        alayer_key = get_blender_anim_layer_key(scene, ref_id)
        name = (get_blenderID_name(ref_id) if ref_id else scene.name).encode()

        if start_zero:
            f_end -= f_start
            f_start = 0.0

        return (astack_key, animations, alayer_key, name, f_start, f_end) if animations else None

    def fbx_data_armature_elements(root, arm_obj, scene_data):
        """
        Write:
            * Bones "data" (NodeAttribute::LimbNode, contains pretty much nothing!).
            * Deformers (i.e. Skin), bind between an armature and a mesh.
            ** SubDeformers (i.e. Cluster), one per bone/vgroup pair.
            * BindPose.
        Note armature itself has no data, it is a mere "Null" Model...
        """
        mat_world_arm = arm_obj.fbx_object_matrix(scene_data, global_space=True)
        bones = tuple(bo_obj for bo_obj in arm_obj.bones if bo_obj in scene_data.objects)

        bone_radius_scale = 33.0

        # Bones "data".
        for bo_obj in bones:
            bo = bo_obj.bdata
            bo_data_key = scene_data.data_bones[bo_obj]
            fbx_bo = elem_data_single_int64(root, b"NodeAttribute", get_fbx_uuid_from_key(bo_data_key))
            fbx_bo.add_string(fbx_name_class(bo.name.encode(), b"NodeAttribute"))
            fbx_bo.add_string(b"LimbNode")
            elem_data_single_string(fbx_bo, b"TypeFlags", b"Skeleton")

            tmpl = elem_props_template_init(scene_data.templates, b"Bone")
            props = elem_properties(fbx_bo)
            elem_props_template_set(tmpl, props, "p_double", b"Size", bo.head_radius * bone_radius_scale * SCALE_FACTOR)
            elem_props_template_finalize(tmpl, props)

            # Custom properties.
            if scene_data.settings.use_custom_props:
                fbx_data_element_custom_properties(props, bo)

            # Store Blender bone length - XXX Not much useful actually :/
            # (LimbLength can't be used because it is a scale factor 0-1 for the parent-child distance:
            # http://docs.autodesk.com/FBX/2014/ENU/FBX-SDK-Documentation/cpp_ref/class_fbx_skeleton.html#a9bbe2a70f4ed82cd162620259e649f0f )
            # elem_props_set(props, "p_double", "BlenderBoneLength".encode(), (bo.tail_local - bo.head_local).length, custom=True)

        # Skin deformers and BindPoses.
        # Note: we might also use Deformers for our "parent to vertex" stuff???
        deformer = scene_data.data_deformers_skin.get(arm_obj, None)
        if deformer is not None:
            for me, (skin_key, ob_obj, clusters) in deformer.items():
                # BindPose.
                mat_world_obj, mat_world_bones = fbx_data_bindpose_element(root, ob_obj, me, scene_data,
                                                                           arm_obj, mat_world_arm, bones)

                # Deformer.
                fbx_skin = elem_data_single_int64(root, b"Deformer", get_fbx_uuid_from_key(skin_key))
                fbx_skin.add_string(fbx_name_class(arm_obj.name.encode(), b"Deformer"))
                fbx_skin.add_string(b"Skin")

                elem_data_single_int32(fbx_skin, b"Version", FBX_DEFORMER_SKIN_VERSION)
                elem_data_single_float64(fbx_skin, b"Link_DeformAcuracy", 50.0)  # Only vague idea what it is...

                # Pre-process vertex weights (also to check vertices assigned ot more than four bones).
                ob = ob_obj.bdata
                bo_vg_idx = {bo_obj.bdata.name: ob.vertex_groups[bo_obj.bdata.name].index
                             for bo_obj in clusters.keys() if bo_obj.bdata.name in ob.vertex_groups}
                valid_idxs = set(bo_vg_idx.values())
                vgroups = {vg.index: {} for vg in ob.vertex_groups}
                verts_vgroups = (
                sorted(((vg.group, vg.weight) for vg in v.groups if vg.weight and vg.group in valid_idxs),
                       key=lambda e: e[1], reverse=True)
                for v in me.vertices)
                for idx, vgs in enumerate(verts_vgroups):
                    for vg_idx, w in vgs:
                        vgroups[vg_idx][idx] = w

                for bo_obj, clstr_key in clusters.items():
                    bo = bo_obj.bdata
                    # Find which vertices are affected by this bone/vgroup pair, and matching weights.
                    # Note we still write a cluster for bones not affecting the mesh, to get 'rest pose' data
                    # (the TransformBlah matrices).
                    vg_idx = bo_vg_idx.get(bo.name, None)
                    indices, weights = ((), ()) if vg_idx is None or not vgroups[vg_idx] else zip(
                        *vgroups[vg_idx].items())

                    # Create the cluster.
                    fbx_clstr = elem_data_single_int64(root, b"Deformer", get_fbx_uuid_from_key(clstr_key))
                    fbx_clstr.add_string(fbx_name_class(bo.name.encode(), b"SubDeformer"))
                    fbx_clstr.add_string(b"Cluster")

                    elem_data_single_int32(fbx_clstr, b"Version", FBX_DEFORMER_CLUSTER_VERSION)
                    # No idea what that user data might be...
                    fbx_userdata = elem_data_single_string(fbx_clstr, b"UserData", b"")
                    fbx_userdata.add_string(b"")
                    if indices:
                        elem_data_single_int32_array(fbx_clstr, b"Indexes", indices)
                        elem_data_single_float64_array(fbx_clstr, b"Weights", weights)
                    # Transform, TransformLink and TransformAssociateModel matrices...
                    # They seem to be doublons of BindPose ones??? Have armature (associatemodel) in addition, though.
                    # WARNING! Even though official FBX API presents Transform in global space,
                    #          **it is stored in bone space in FBX data!** See:
                    #          http://area.autodesk.com/forum/autodesk-fbx/fbx-sdk/why-the-values-return-
                    #                 by-fbxcluster-gettransformmatrix-x-not-same-with-the-value-in-ascii-fbx-file/
                    # test_data[bo_obj.name] = matrix4_to_array(mat_world_bones[bo_obj].inverted_safe() @ mat_world_obj)

                    # Todo add to FBX addon
                    transform_matrix = mat_world_bones[bo_obj].inverted_safe() @ mat_world_obj
                    transform_link_matrix = mat_world_bones[bo_obj]
                    transform_associate_model_matrix = mat_world_arm

                    transform_matrix = transform_matrix.LocRotScale(
                        [i * SCALE_FACTOR for i in transform_matrix.to_translation()],
                        transform_matrix.to_quaternion(),
                        [i * SCALE_FACTOR for i in transform_matrix.to_scale()],
                    )

                    elem_data_single_float64_array(fbx_clstr, b"Transform", matrix4_to_array(transform_matrix))
                    elem_data_single_float64_array(fbx_clstr, b"TransformLink", matrix4_to_array(transform_link_matrix))
                    elem_data_single_float64_array(fbx_clstr, b"TransformAssociateModel",
                                                   matrix4_to_array(transform_associate_model_matrix))

    def fbx_data_object_elements(root, ob_obj, scene_data):
        """
        Write the Object (Model) data blocks.
        Note this "Model" can also be bone or dupli!
        """
        obj_type = b"Null"  # default, sort of empty...
        if ob_obj.is_bone:
            obj_type = b"LimbNode"
        elif (ob_obj.type == 'ARMATURE'):
            if scene_data.settings.armature_nodetype == 'ROOT':
                obj_type = b"Root"
            elif scene_data.settings.armature_nodetype == 'LIMBNODE':
                obj_type = b"LimbNode"
            else:  # Default, preferred option...
                obj_type = b"Null"
        elif (ob_obj.type in BLENDER_OBJECT_TYPES_MESHLIKE):
            obj_type = b"Mesh"
        elif (ob_obj.type == 'LIGHT'):
            obj_type = b"Light"
        elif (ob_obj.type == 'CAMERA'):
            obj_type = b"Camera"

        if ob_obj.type == 'ARMATURE':
            if bpy.context.scene.send2ue.export_object_name_as_root:
                # if the object is already named armature this forces the object name to root
                if 'armature' == ob_obj.name.lower():
                    ob_obj.name = 'root'

            # otherwise don't use the armature objects name as the root in unreal
            else:
                # Rename the armature object to 'Armature'. This is important, because this is a special
                # reserved keyword for the Unreal FBX importer that will be ignored when the bone hierarchy
                # is imported from the FBX file. That way there is not an additional root bone in the Unreal
                # skeleton hierarchy.
                ob_obj.name = 'Armature'

        model = elem_data_single_int64(root, b"Model", ob_obj.fbx_uuid)
        model.add_string(fbx_name_class(ob_obj.name.encode(), b"Model"))
        model.add_string(obj_type)

        elem_data_single_int32(model, b"Version", FBX_MODELS_VERSION)

        # Object transform info.
        loc, rot, scale, matrix, matrix_rot = ob_obj.fbx_object_tx(scene_data)
        rot = tuple(convert_rad_to_deg_iter(rot))

        # Todo add to FBX addon
        if ob_obj.type == 'ARMATURE':
            scale = Vector((scale[0] / SCALE_FACTOR, scale[1] / SCALE_FACTOR, scale[2] / SCALE_FACTOR))
            if bpy.context.scene.send2ue.use_object_origin:
                loc = Vector((0, 0, 0))

        elif ob_obj.type == 'Ellipsis':
            loc = Vector((loc[0] * SCALE_FACTOR, loc[1] * SCALE_FACTOR, loc[2] * SCALE_FACTOR))
        elif ob_obj.type == 'MESH':
            # centers mesh object by their object origin
            if bpy.context.scene.send2ue.use_object_origin:
                asset_id = bpy.context.window_manager.send2ue.asset_id
                asset_data = bpy.context.window_manager.send2ue.asset_data.get(asset_id)

                # if this is a static mesh then check that all other mesh objects in this export are
                # centered relative the asset object
                if asset_data['_asset_type'] == 'StaticMesh':
                    asset_object = bpy.data.objects.get(asset_data['_mesh_object_name'])
                    current_object = bpy.data.objects.get(ob_obj.name)
                    # get the world location of the current mesh
                    object_world_location = current_object.matrix_world.to_translation()

                    # if this is using the empty from the combined meshes option
                    # https://github.com/EpicGamesExt/BlenderTools/issues/627
                    empty_object_name = asset_data.get('empty_object_name')
                    if empty_object_name:
                        empty_object = bpy.data.objects.get(empty_object_name)
                        empty_world_location = empty_object.matrix_world.to_translation()
                        loc = Vector((
                            (object_world_location[0] - empty_world_location[0]) * SCALE_FACTOR,
                            (object_world_location[1] - empty_world_location[1]) * SCALE_FACTOR,
                            (object_world_location[2] - empty_world_location[2]) * SCALE_FACTOR
                        ))
                        rot = (0, 0, 0)
                    else:
                        asset_world_location = asset_object.matrix_world.to_translation()
                        loc = Vector((
                            (object_world_location[0] - asset_world_location[0]),
                            (object_world_location[1] - asset_world_location[1]),
                            (object_world_location[2] - asset_world_location[2])
                        ))
                        # only adjust the asset object so collisions and lods are not effected
                        # https://github.com/EpicGamesExt/BlenderTools/issues/587
                        if asset_object == current_object:
                            # clear rotation and scale only if spawning actor
                            # https://github.com/EpicGamesExt/BlenderTools/issues/610
                            rot = (0, 0, 0)
                            scale = (1.0 * SCALE_FACTOR, 1.0 * SCALE_FACTOR, 1.0 * SCALE_FACTOR)
                else:
                    loc = Vector((0, 0, 0))

        tmpl = elem_props_template_init(scene_data.templates, b"Model")
        # For now add only loc/rot/scale...
        props = elem_properties(model)
        elem_props_template_set(tmpl, props, "p_lcl_translation", b"Lcl Translation", loc,
                                animatable=True, animated=((ob_obj.key, "Lcl Translation") in scene_data.animated))
        elem_props_template_set(tmpl, props, "p_lcl_rotation", b"Lcl Rotation", rot,
                                animatable=True, animated=((ob_obj.key, "Lcl Rotation") in scene_data.animated))
        elem_props_template_set(tmpl, props, "p_lcl_scaling", b"Lcl Scaling", scale,
                                animatable=True, animated=((ob_obj.key, "Lcl Scaling") in scene_data.animated))
        elem_props_template_set(tmpl, props, "p_visibility", b"Visibility", float(not ob_obj.hide))

        # Absolutely no idea what this is, but seems mandatory for validity of the file, and defaults to
        # invalid -1 value...
        elem_props_template_set(tmpl, props, "p_integer", b"DefaultAttributeIndex", 0)

        elem_props_template_set(tmpl, props, "p_enum", b"InheritType", 1)  # RSrs

        # Custom properties.
        if scene_data.settings.use_custom_props:
            # Here we want customprops from the 'pose' bone, not the 'edit' bone...
            bdata = ob_obj.bdata_pose_bone if ob_obj.is_bone else ob_obj.bdata
            fbx_data_element_custom_properties(props, bdata)

        # Those settings would obviously need to be edited in a complete version of the exporter, may depends on
        # object type, etc.
        elem_data_single_int32(model, b"MultiLayer", 0)
        elem_data_single_int32(model, b"MultiTake", 0)
        if (bpy.app.version >= (4,0,0)):
            elem_data_single_char(model, b"Shading", b"\x01")  # Shading was changed to a char from bool in blender 4
        else:
            elem_data_single_bool(model, b"Shading", True)
        elem_data_single_string(model, b"Culling", b"CullingOff")

        if obj_type == b"Camera":
            # Why, oh why are FBX cameras such a mess???
            # And WHY add camera data HERE??? Not even sure this is needed...
            render = scene_data.scene.render
            width = render.resolution_x * 1.0
            height = render.resolution_y * 1.0
            elem_props_template_set(tmpl, props, "p_enum", b"ResolutionMode", 0)  # Don't know what it means
            elem_props_template_set(tmpl, props, "p_double", b"AspectW", width)
            elem_props_template_set(tmpl, props, "p_double", b"AspectH", height)
            elem_props_template_set(tmpl, props, "p_bool", b"ViewFrustum", True)
            elem_props_template_set(tmpl, props, "p_enum", b"BackgroundMode", 0)  # Don't know what it means
            elem_props_template_set(tmpl, props, "p_bool", b"ForegroundTransparent", True)

        elem_props_template_finalize(tmpl, props)

    def fbx_data_bindpose_element(root, me_obj, me, scene_data, arm_obj=None, mat_world_arm=None, bones=[]):
        """
        Helper, since bindpose are used by both meshes shape keys and armature bones...
        """
        if arm_obj is None:
            arm_obj = me_obj
        # We assume bind pose for our bones are their "Editmode" pose...
        # All matrices are expected in global (world) space.
        bindpose_key = get_blender_bindpose_key(arm_obj.bdata, me)
        fbx_pose = elem_data_single_int64(root, b"Pose", get_fbx_uuid_from_key(bindpose_key))
        fbx_pose.add_string(fbx_name_class(me.name.encode(), b"Pose"))
        fbx_pose.add_string(b"BindPose")

        elem_data_single_string(fbx_pose, b"Type", b"BindPose")
        elem_data_single_int32(fbx_pose, b"Version", FBX_POSE_BIND_VERSION)
        elem_data_single_int32(fbx_pose, b"NbPoseNodes", 1 + (1 if (arm_obj != me_obj) else 0) + len(bones))

        # First node is mesh/object.
        mat_world_obj = me_obj.fbx_object_matrix(scene_data, global_space=True)
        fbx_posenode = elem_empty(fbx_pose, b"PoseNode")
        elem_data_single_int64(fbx_posenode, b"Node", me_obj.fbx_uuid)
        elem_data_single_float64_array(fbx_posenode, b"Matrix", matrix4_to_array(mat_world_obj))

        # Second node is armature object itself.
        if arm_obj != me_obj:
            fbx_posenode = elem_empty(fbx_pose, b"PoseNode")
            elem_data_single_int64(fbx_posenode, b"Node", arm_obj.fbx_uuid)

            # Todo merge into blenders FBX addon
            mat_world_arm = mat_world_arm.LocRotScale(
                mat_world_arm.to_translation(),
                mat_world_arm.to_quaternion(),
                [i / SCALE_FACTOR for i in mat_world_arm.to_scale()],
            )

            elem_data_single_float64_array(fbx_posenode, b"Matrix", matrix4_to_array(mat_world_arm))

        # And all bones of armature!
        mat_world_bones = {}
        for bo_obj in bones:
            bomat = bo_obj.fbx_object_matrix(scene_data, rest=True, global_space=True)
            mat_world_bones[bo_obj] = bomat
            fbx_posenode = elem_empty(fbx_pose, b"PoseNode")
            elem_data_single_int64(fbx_posenode, b"Node", bo_obj.fbx_uuid)

            # Todo merge into blenders FBX addon
            bomat = bomat.LocRotScale(
                bomat.to_translation(),
                bomat.to_quaternion(),
                [i / SCALE_FACTOR for i in bomat.to_scale()]
            )

            elem_data_single_float64_array(fbx_posenode, b"Matrix", matrix4_to_array(bomat))

        return mat_world_obj, mat_world_bones

    keywords["global_matrix"] = (
        axis_conversion(
            to_forward=keywords['axis_forward'],
            to_up=keywords['axis_up'],
        ).to_4x4()
    )

    # save a copy of the original export bin
    original_fbx_animations_do = export_fbx_bin.fbx_animations_do
    original_fbx_data_armature_elements = export_fbx_bin.fbx_data_armature_elements
    original_fbx_data_object_elements = export_fbx_bin.fbx_data_object_elements
    original_fbx_data_bindpose_element = export_fbx_bin.fbx_data_bindpose_element

    # here is where we patch in our tweaked functions
    export_fbx_bin.fbx_animations_do = fbx_animations_do
    export_fbx_bin.fbx_data_armature_elements = fbx_data_armature_elements
    export_fbx_bin.fbx_data_object_elements = fbx_data_object_elements
    export_fbx_bin.fbx_data_bindpose_element = fbx_data_bindpose_element

    # patch in a report method on self to fake the fbx export operator class
    self = type(
        'Send2UeExportFBX',
        (object,),
        {'report': report_error}
    )
    export_fbx_bin.save(self, bpy.context, **keywords)

    # now re-patch back the export bin module so that the existing fbx addon still has its original code
    # https://github.com/EpicGamesExt/BlenderTools/issues/598
    export_fbx_bin.fbx_animations_do = original_fbx_animations_do
    export_fbx_bin.fbx_data_armature_elements = original_fbx_data_armature_elements
    export_fbx_bin.fbx_data_object_elements = original_fbx_data_object_elements
    export_fbx_bin.fbx_data_bindpose_element = original_fbx_data_bindpose_element
