import addon_utils
import os
import bpy
import array
from mathutils import Vector, Matrix
from importlib.machinery import SourceFileLoader
from bpy_extras import node_shader_utils

addons = {os.path.basename(os.path.dirname(module.__file__)): module.__file__ for module in addon_utils.modules()}
addon_folder_path = os.path.dirname(addons.get('io_scene_fbx'))

try:
    SourceFileLoader('io_scene_fbx', os.path.join(addon_folder_path, '__init__.py')).load_module()
except RuntimeError as error:
    print(error)

import io_scene_fbx.export_fbx_bin as export_fbx_bin
import io_scene_fbx.fbx_utils as fbx_utils
import io_scene_fbx.data_types as data_types
from io_scene_fbx import ExportFBX
from io_scene_fbx.fbx_utils import (
    # Constants.
    FBX_VERSION, FBX_HEADER_VERSION, FBX_SCENEINFO_VERSION, FBX_TEMPLATES_VERSION,
    FBX_MODELS_VERSION,
    FBX_GEOMETRY_VERSION, FBX_GEOMETRY_NORMAL_VERSION, FBX_GEOMETRY_BINORMAL_VERSION, FBX_GEOMETRY_TANGENT_VERSION,
    FBX_GEOMETRY_SMOOTHING_VERSION, FBX_GEOMETRY_CREASE_VERSION, FBX_GEOMETRY_VCOLOR_VERSION, FBX_GEOMETRY_UV_VERSION,
    FBX_GEOMETRY_MATERIAL_VERSION, FBX_GEOMETRY_LAYER_VERSION,
    FBX_GEOMETRY_SHAPE_VERSION, FBX_DEFORMER_SHAPE_VERSION, FBX_DEFORMER_SHAPECHANNEL_VERSION,
    FBX_POSE_BIND_VERSION, FBX_DEFORMER_SKIN_VERSION, FBX_DEFORMER_CLUSTER_VERSION,
    FBX_MATERIAL_VERSION, FBX_TEXTURE_VERSION,
    FBX_ANIM_KEY_VERSION,
    FBX_ANIM_PROPSGROUP_NAME,
    FBX_KTIME,
    BLENDER_OTHER_OBJECT_TYPES, BLENDER_OBJECT_TYPES_MESHLIKE,
    FBX_LIGHT_TYPES, FBX_LIGHT_DECAY_TYPES,
    RIGHT_HAND_AXES, FBX_FRAMERATES,
    # Miscellaneous utils.
    PerfMon,
    units_blender_to_fbx_factor, units_convertor, units_convertor_iter,
    matrix4_to_array, similar_values, similar_values_iter,
    # Mesh transform helpers.
    vcos_transformed_gen, nors_transformed_gen,
    # UUID from key.
    get_fbx_uuid_from_key,
    # Key generators.
    get_blenderID_key, get_blenderID_name,
    get_blender_mesh_shape_key, get_blender_mesh_shape_channel_key,
    get_blender_empty_key, get_blender_bone_key,
    get_blender_bindpose_key, get_blender_armature_skin_key, get_blender_bone_cluster_key,
    get_blender_anim_id_base, get_blender_anim_stack_key, get_blender_anim_layer_key,
    get_blender_anim_curve_node_key, get_blender_anim_curve_key,
    get_blender_nodetexture_key,
    # FBX element data.
    elem_empty,
    elem_data_single_bool, elem_data_single_int16, elem_data_single_int32, elem_data_single_int64,
    elem_data_single_float32, elem_data_single_float64,
    elem_data_single_bytes, elem_data_single_string, elem_data_single_string_unicode,
    elem_data_single_bool_array, elem_data_single_int32_array, elem_data_single_int64_array,
    elem_data_single_float32_array, elem_data_single_float64_array, elem_data_vec_float64,
    # FBX element properties.
    elem_properties, elem_props_set, elem_props_compound,
    # FBX element properties handling templates.
    elem_props_template_init, elem_props_template_set, elem_props_template_finalize,
    # Templates.
    FBXTemplate, fbx_templates_generate,
    # Objects.
    ObjectWrapper, fbx_name_class,
    # Top level.
    FBXExportSettingsMedia, FBXExportSettings, FBXExportData,
)

convert_rad_to_deg_iter = units_convertor_iter("radian", "degree")

from io_scene_fbx.export_fbx_bin import (
    fbx_template_def_animstack,
    fbx_template_def_geometry,
    fbx_template_def_camera,
    fbx_template_def_bone,
    fbx_template_def_null,
    fbx_template_def_light,
    fbx_template_def_globalsettings,
    fbx_template_def_video,
    fbx_template_def_texture_file,
    fbx_template_def_material,
    fbx_template_def_deformer,
    fbx_template_def_pose,
    fbx_template_def_model,
    fbx_template_def_animcurvenode,
    fbx_template_def_animlayer,
    fbx_animations,
    fbx_template_def_animcurve,
    fbx_generate_leaf_bones,
    PRINCIPLED_TEXTURE_SOCKETS_TO_FBX,
    fbx_data_element_custom_properties
)


class AnimationCurveNodeWrapper:
    """
    This class provides a same common interface for all (FBX-wise) AnimationCurveNode and AnimationCurve elements,
    and easy API to handle those.
    """
    __slots__ = (
        'elem_keys', '_keys', 'default_values', 'fbx_group', 'fbx_gname', 'fbx_props',
        'force_keying', 'force_startend_keying')

    kinds = {
        'LCL_TRANSLATION': ("Lcl Translation", "T", ("X", "Y", "Z")),
        'LCL_ROTATION': ("Lcl Rotation", "R", ("X", "Y", "Z")),
        'LCL_SCALING': ("Lcl Scaling", "S", ("X", "Y", "Z")),
        'SHAPE_KEY': ("DeformPercent", "DeformPercent", ("DeformPercent",)),
        'CAMERA_FOCAL': ("FocalLength", "FocalLength", ("FocalLength",)),
    }

    def __init__(self, elem_key, kind, force_keying, force_startend_keying, default_values=...):
        self.elem_keys = [elem_key]
        assert (kind in self.kinds)
        self.fbx_group = [self.kinds[kind][0]]
        self.fbx_gname = [self.kinds[kind][1]]
        self.fbx_props = [self.kinds[kind][2]]
        self.force_keying = force_keying
        self.force_startend_keying = force_startend_keying
        self._keys = []  # (frame, values, write_flags)
        if default_values is not ...:
            assert (len(default_values) == len(self.fbx_props[0]))
            self.default_values = default_values
        else:
            self.default_values = (0.0) * len(self.fbx_props[0])

    def __bool__(self):
        # We are 'True' if we do have some validated keyframes...
        return bool(self._keys) and (True in ((True in k[2]) for k in self._keys))

    def add_group(self, elem_key, fbx_group, fbx_gname, fbx_props):
        """
        Add another whole group stuff (curvenode, animated item/prop + curvnode/curve identifiers).
        E.g. Shapes animations is written twice, houra!
        """
        assert (len(fbx_props) == len(self.fbx_props[0]))
        self.elem_keys.append(elem_key)
        self.fbx_group.append(fbx_group)
        self.fbx_gname.append(fbx_gname)
        self.fbx_props.append(fbx_props)

    def add_keyframe(self, frame, values):
        """
        Add a new keyframe to all curves of the group.
        """
        assert (len(values) == len(self.fbx_props[0]))
        self._keys.append((frame, values, [True] * len(values)))  # write everything by default.

    def simplify(self, fac, step, force_keep=False):
        """
        Simplifies sampled curves by only enabling samples when:
            * their values relatively differ from the previous sample ones.
        """
        if not self._keys:
            return

        if fac == 0.0:
            return

        # So that, with default factor and step values (1), we get:
        min_reldiff_fac = fac * 1.0e-3  # min relative value evolution: 0.1% of current 'order of magnitude'.
        min_absdiff_fac = 0.1  # A tenth of reldiff...
        keys = self._keys

        p_currframe, p_key, p_key_write = keys[0]
        p_keyed = list(p_key)
        are_keyed = [False] * len(p_key)
        for currframe, key, key_write in keys:
            for idx, (val, p_val) in enumerate(zip(key, p_key)):
                key_write[idx] = False
                p_keyedval = p_keyed[idx]
                if val == p_val:
                    # Never write keyframe when value is exactly the same as prev one!
                    continue
                # This is contracted form of relative + absolute-near-zero difference:
                #     absdiff = abs(a - b)
                #     if absdiff < min_reldiff_fac * min_absdiff_fac:
                #         return False
                #     return (absdiff / ((abs(a) + abs(b)) / 2)) > min_reldiff_fac
                # Note that we ignore the '/ 2' part here, since it's not much significant for us.
                if abs(val - p_val) > (min_reldiff_fac * max(abs(val) + abs(p_val), min_absdiff_fac)):
                    # If enough difference from previous sampled value, key this value *and* the previous one!
                    key_write[idx] = True
                    p_key_write[idx] = True
                    p_keyed[idx] = val
                    are_keyed[idx] = True
                elif abs(val - p_keyedval) > (min_reldiff_fac * max((abs(val) + abs(p_keyedval)), min_absdiff_fac)):
                    # Else, if enough difference from previous keyed value, key this value only!
                    key_write[idx] = True
                    p_keyed[idx] = val
                    are_keyed[idx] = True
            p_currframe, p_key, p_key_write = currframe, key, key_write

        # If we write nothing (action doing nothing) and are in 'force_keep' mode, we key everything! :P
        # See T41766.
        # Also, it seems some importers (e.g. UE4) do not handle correctly armatures where some bones
        # are not animated, but are children of animated ones, so added an option to systematically force writing
        # one key in this case.
        # See T41719, T41605, T41254...
        if self.force_keying or (force_keep and not self):
            are_keyed[:] = [True] * len(are_keyed)

        # If we did key something, ensure first and last sampled values are keyed as well.
        if self.force_startend_keying:
            for idx, is_keyed in enumerate(are_keyed):
                if is_keyed:
                    keys[0][2][idx] = keys[-1][2][idx] = True

    def get_final_data(self, scene, ref_id, force_keep=False):
        """
        Yield final anim data for this 'curvenode' (for all curvenodes defined).
        force_keep is to force to keep a curve even if it only has one valid keyframe.
        """
        curves = [[] for k in self._keys[0][1]]
        for currframe, key, key_write in self._keys:
            for curve, val, wrt in zip(curves, key, key_write):
                if wrt:
                    curve.append((currframe, val))

        force_keep = force_keep or self.force_keying
        for elem_key, fbx_group, fbx_gname, fbx_props in \
            zip(self.elem_keys, self.fbx_group, self.fbx_gname, self.fbx_props):
            group_key = get_blender_anim_curve_node_key(scene, ref_id, elem_key, fbx_group)
            group = {}
            for c, def_val, fbx_item in zip(curves, self.default_values, fbx_props):
                fbx_item = FBX_ANIM_PROPSGROUP_NAME + "|" + fbx_item
                curve_key = get_blender_anim_curve_key(scene, ref_id, elem_key, fbx_group, fbx_item)
                # (curve key, default value, keyframes, write flag).
                group[fbx_item] = (curve_key, def_val, c,
                                   True if (len(c) > 1 or (len(c) > 0 and force_keep)) else False)
            yield elem_key, group_key, group, fbx_group, fbx_gname


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
        animdata_ob[ob_obj] = (ACNW(ob_obj.key, 'LCL_TRANSLATION', force_key, force_sek, loc * 100),
                               ACNW(ob_obj.key, 'LCL_ROTATION', force_key, force_sek, rot_deg),
                               ACNW(ob_obj.key, 'LCL_SCALING', force_key, force_sek, scale / 100))
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
        acnode = AnimationCurveNodeWrapper(cam_key, 'CAMERA_FOCAL', force_key, force_sek, (cam.lens,))
        animdata_cameras[cam_key] = (acnode, cam)

    currframe = f_start
    while currframe <= f_end:
        real_currframe = currframe - f_start if start_zero else currframe
        scene.frame_set(int(currframe), subframe=currframe - int(currframe))

        for dp_obj in ob_obj.dupli_list_gen(depsgraph):
            pass  # Merely updating dupli matrix of ObjectWrapper...
        for ob_obj, (anim_loc, anim_rot, anim_scale) in animdata_ob.items():
            location_multiple = 100

            # if this curve is the object root then keep its scale at 1
            if len(str(ob_obj).split('|')) == 1:
                location_multiple = 1

            # We compute baked loc/rot/scale for all objects (rot being euler-compat with previous value!).
            p_rot = p_rots.get(ob_obj, None)
            loc, rot, scale, _m, _mr = ob_obj.fbx_object_tx(scene_data, rot_euler_compat=p_rot)
            p_rots[ob_obj] = rot
            anim_loc.add_keyframe(real_currframe, loc * location_multiple)
            anim_rot.add_keyframe(real_currframe, tuple(convert_rad_to_deg_iter(rot)))
            anim_scale.add_keyframe(real_currframe, scale / 100)
        for anim_shape, me, shape in animdata_shapes.values():
            anim_shape.add_keyframe(real_currframe, (shape.value * 100.0,))
        for anim_camera, camera in animdata_cameras.values():
            anim_camera.add_keyframe(real_currframe, (camera.lens,))
        currframe += bake_step

    scene.frame_set(back_currframe, subframe=0.0)

    animations = {}

    # And now, produce final data (usable by FBX export code)
    # Objects-like loc/rot/scale...
    for ob_obj, anims in animdata_ob.items():
        for anim in anims:
            anim.simplify(simplify_fac, bake_step, force_keep)
            if not anim:
                continue
            for obj_key, group_key, group, fbx_group, fbx_gname in anim.get_final_data(scene, ref_id, force_keep):
                anim_data = animations.setdefault(obj_key, ("dummy_unused_key", {}))
                anim_data[1][fbx_group] = (group_key, group, fbx_gname)

    # And meshes' shape keys.
    for channel_key, (anim_shape, me, shape) in animdata_shapes.items():
        final_keys = {}
        anim_shape.simplify(simplify_fac, bake_step, force_keep)
        if not anim_shape:
            continue
        for elem_key, group_key, group, fbx_group, fbx_gname in anim_shape.get_final_data(scene, ref_id, force_keep):
            anim_data = animations.setdefault(elem_key, ("dummy_unused_key", {}))
            anim_data[1][fbx_group] = (group_key, group, fbx_gname)

    # And cameras' lens keys.
    for cam_key, (anim_camera, camera) in animdata_cameras.items():
        final_keys = {}
        anim_camera.simplify(simplify_fac, bake_step, force_keep)
        if not anim_camera:
            continue
        for elem_key, group_key, group, fbx_group, fbx_gname in anim_camera.get_final_data(scene, ref_id, force_keep):
            anim_data = animations.setdefault(elem_key, ("dummy_unused_key", {}))
            anim_data[1][fbx_group] = (group_key, group, fbx_gname)

    astack_key = get_blender_anim_stack_key(scene, ref_id)
    alayer_key = get_blender_anim_layer_key(scene, ref_id)
    name = (get_blenderID_name(ref_id) if ref_id else scene.name).encode()

    if start_zero:
        f_end -= f_start
        f_start = 0.0

    # TODO remove
    import json
    with open(r"C:\BlenderTools\animation_data.json", "w") as file:
        json.dump(animations, file)
    return (astack_key, animations, alayer_key, name, f_start, f_end) if animations else None


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
        elem_data_single_float64_array(fbx_posenode, b"Matrix", matrix4_to_array(mat_world_arm))

    # # get the list of objects that do not have parents
    # no_parents = [unordered_object for unordered_object in unordered_objects if not unordered_object.parent]
    #
    # # get the list of objects that have parents
    # parents = [unordered_object for unordered_object in unordered_objects if unordered_object.parent]
    #
    # # re-order the imported objects to have the top of the hierarchies iterated first
    # ordered_objects = no_parents + parents

    # And all bones of armature!
    mat_world_bones = {}
    for bo_obj in bones:
        bomat = bo_obj.fbx_object_matrix(scene_data, rest=True, global_space=True)

        mat_world_bones[bo_obj] = bomat
        fbx_posenode = elem_empty(fbx_pose, b"PoseNode")
        elem_data_single_int64(fbx_posenode, b"Node", bo_obj.fbx_uuid)
        elem_data_single_float64_array(fbx_posenode, b"Matrix", matrix4_to_array(bomat))

    return mat_world_obj, mat_world_bones


def fbx_data_armature_elements(root, arm_obj, scene_data):
    """
    Write:
        * Bones "data" (NodeAttribute::LimbNode, contains pretty much nothing!).
        * Deformers (i.e. Skin), bind between an armature and a mesh.
        ** SubDeformers (i.e. Cluster), one per bone/vgroup pair.
        * BindPose.
    Note armature itself has no data, it is a mere "Null" Model...
    """
    test_data = {}
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
        elem_props_template_set(tmpl, props, "p_double", b"Size", bo.head_radius * bone_radius_scale)
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
            verts_vgroups = (sorted(((vg.group, vg.weight) for vg in v.groups if vg.weight and vg.group in valid_idxs),
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
                indices, weights = ((), ()) if vg_idx is None or not vgroups[vg_idx] else zip(*vgroups[vg_idx].items())

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

                elem_data_single_float64_array(fbx_clstr, b"Transform", matrix4_to_array(mat_world_bones[bo_obj].inverted_safe() @ mat_world_obj))
                elem_data_single_float64_array(fbx_clstr, b"TransformLink", matrix4_to_array(mat_world_bones[bo_obj]))
                elem_data_single_float64_array(fbx_clstr, b"TransformAssociateModel", matrix4_to_array(mat_world_arm))

    import json
    with open(r'C:\BlenderTools\skeleton_data.json', 'w') as file:
        json.dump(test_data, file)


class Send2UEExportFBX(ExportFBX):
    """Write a FBX file"""
    bl_idname = "send2ue.export_fbx"

    def execute(self, context):
        if not self.filepath:
            raise Exception("filepath not set")

        # global_matrix = (axis_conversion(to_forward=self.axis_forward,
        #                                  to_up=self.axis_up,
        #                                  ).to_4x4()
        #                 if self.use_space_transform else Matrix())
        global_matrix = Matrix()

        keywords = self.as_keywords(ignore=("check_existing",
                                            "filter_glob",
                                            "ui_tab",
                                            ))

        keywords["global_matrix"] = global_matrix

        # export_fbx_bin.fbx_animations_do = fbx_animations_do
        export_fbx_bin.fbx_data_armature_elements = fbx_data_armature_elements
        export_fbx_bin.save(self, context, **keywords)
        return {'FINISHED'}


if __name__ == '__main__':
    bpy.utils.register_class(ExportFBX)
    bpy.ops.send2ue.export_fbx()
