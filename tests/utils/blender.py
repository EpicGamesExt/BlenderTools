import os
import rpc
from utils.addon_packager import AddonPackager
import logging
import importlib
import tempfile

try:
    import bpy
    import addon_utils
except ModuleNotFoundError:
    pass

DEFAULT_IMPORTS = ['import bpy']
REMAP_PAIRS = []
BLENDER_PORT = int(os.environ.get('BLENDER_PORT', 9997))

# use different remap pairs when inside a container
if os.environ.get('TEST_ENVIRONMENT'):
    BLENDER_PORT = int(os.environ.get('BLENDER_PORT', 8997))
    REMAP_PAIRS = [(os.environ.get('HOST_REPO_FOLDER'), os.environ.get('CONTAINER_REPO_FOLDER'))]


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
remote_blender_decorator = rpc.factory.remote_call(
    port=BLENDER_PORT,
    remap_pairs=REMAP_PAIRS,
    default_imports=DEFAULT_IMPORTS
)


@rpc.factory.remote_class(remote_blender_decorator)
class BlenderRemoteCalls:
    @staticmethod
    def get_data_block_names(data_block_type):
        data_blocks = getattr(bpy.data, data_block_type)
        return list(data_blocks.keys())

    @staticmethod
    def set_all_action_locations(world_location):
        for action in bpy.data.actions:
            Blender.set_action_location(action, world_location)

    @staticmethod
    def install_addons(repo_folder, addons):
        """
        Installs the given addons from the release folder.
        """
        for addon in addons:
            addon_folder_path = os.path.join(repo_folder, addon)
            release_folder = os.path.join(repo_folder, 'release')
            addon_packager = AddonPackager(addon, addon_folder_path, release_folder)
            addon_packager.install_addon()

    @staticmethod
    def path_exists(file_path):
        return os.path.exists(file_path)

    @staticmethod
    def is_addon_enabled(addon_name):
        return bool(bpy.context.preferences.addons.get(addon_name))

    @staticmethod
    def register_addon(addon_name):
        addon = importlib.import_module(addon_name)
        importlib.reload(addon)
        addon.register()

    @staticmethod
    def unregister_addon(addon_name):
        addon = importlib.import_module(addon_name)
        importlib.reload(addon)
        addon.unregister()

    @staticmethod
    def send2ue_setup_project():
        addon = importlib.import_module('send2ue')
        importlib.reload(addon)
        addon.utilities.setup_project()

    @staticmethod
    def get_addon_property(context_name, addon_name, property_name):
        return Blender.get_addon_property(context_name, addon_name, property_name)

    @staticmethod
    def has_addon_property(context_name, addon_name, property_name):
        return Blender.has_addon_property(context_name, addon_name, property_name)

    @staticmethod
    def has_data_block(data_type, name):
        data = getattr(bpy.data, data_type)
        return bool(data.get(name))

    @staticmethod
    def set_addon_property(context_name, addon_name, property_name, value, data_type=None):
        # handle addon preferences
        if context_name == 'preferences':
            properties = bpy.context.preferences.addons[addon_name].preferences
        # otherwise the normal contexts
        else:
            context = getattr(bpy.context, context_name)
            properties = getattr(context, addon_name)

        module_path = property_name.split('.')
        for index, sub_property_name in enumerate(module_path, 1):
            if index == len(module_path):
                if data_type == 'object':
                    value = bpy.data.objects.get(value)

                setattr(properties, sub_property_name, value)
                break
            properties = getattr(properties, sub_property_name)

    @staticmethod
    def check_particles(mesh_name, particle_names):
        """
        Checks whether the given mesh has any of the particles specified in particle_names.

        :param str mesh_name: The name of the mesh to query.
        :param str particle_names: The name of the property attribute to check.
        :return list(str): A list of names that is a subset of particle_names that exist on the specified mesh.
        """
        mesh_particles_names = set(bpy.data.objects.get(mesh_name).particle_systems.keys())
        return list(filter(lambda name: name in mesh_particles_names, particle_names))

    @staticmethod
    def check_property_attribute(addon, attribute_name, excluded=None):
        """
        Checks that the given addon property attribute is unique and not empty.

        :param str addon: The name of the addon.
        :param str attribute_name: The name of the property attribute to check.
        :param list[str] excluded: A list of excluded property names not to check.
        """
        if excluded is None:
            excluded = []

        attributes = {}
        properties = getattr(bpy.context.scene, addon)
        for key, value in properties.bl_rna.properties.items():
            # skip if property name is excluded
            if key in excluded:
                continue

            property_type = getattr(value, 'type')
            if property_type != 'POINTER':
                attribute_value = getattr(value, attribute_name)

                # checks if the attribute is an empty string
                assert attribute_value, f'"{key}" has a blank {attribute_name}!'

                # checks if the attribute is unique
                assert (attribute_value not in attributes.keys()), \
                    f'"{key}" has the same {attribute_name} as "{attributes.get(attribute_value)}"!'

                # save each unique attribute
                attributes[attribute_value] = key

    @staticmethod
    def set_particles_visible(mesh_name, particle_modifier_names, visible=True):
        """
        Sets a list of particle systems on a mesh to be visible/invisible in viewport.

        :param str mesh_name: A mesh object name.
        :param list(str) particle_modifier_names: A list of particle modifier names.
        :param bool visible: Whether to the set the list of particles visible or invisible.
        """
        mesh_object = bpy.data.objects.get(mesh_name)
        if mesh_object:
            for name in particle_modifier_names:
                particle = mesh_object.modifiers.get(name)
                if particle:
                    particle.show_viewport = visible

    @staticmethod
    def set_scene_collection_hierarchy(collection_names):
        """
        Sets the collection hierarchy to the order of the given list.

        :param list[str] collection_names: A list of collection names.
        """
        previous_collection = None
        for index, collection_name in enumerate(collection_names):
            collection = bpy.data.collections.get(collection_name)
            if index == 0:
                if collection not in bpy.context.scene.collection.children.values():
                    bpy.context.scene.collection.children.link(collection)
            else:
                if collection not in previous_collection.children.values():
                    previous_collection.children.link(collection)

                if collection in bpy.context.scene.collection.children.values():
                    bpy.context.scene.collection.children.unlink(collection)
            previous_collection = collection

    @staticmethod
    def set_rigify_ik_fk(rig_name, ik_fk_switch, value):
        """
        Sets the a rigify IK/FK switch value.
        """
        if bpy.context.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        bpy.ops.pose.select_all(action='DESELECT')

        for bone_name, control_name in ik_fk_switch.items():
            # set the switch value on the bone
            bpy.data.objects[rig_name].pose.bones[bone_name]['IK_FK'] = value
            # then select the control
            bpy.data.objects[rig_name].data.bones[control_name].select = True

    @staticmethod
    def select_bones(rig_name, bone_names):
        bones = bpy.data.objects[rig_name].data.bones
        for bone in bones:
            bone.select = False

        for bone_name in bone_names:
            bones[bone_name].select = True

    @staticmethod
    def create_empty(name):
        Blender.create_empty(name)

    @staticmethod
    def create_scene_collections(collection_names):
        """
        Creates a collection and links it to the current view layer.

        :param list[str] collection_names: A list of collection names.
        """
        for collection_name in collection_names:
            if collection_name not in bpy.data.collections:
                new_collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(new_collection)

    @staticmethod
    def separate_mesh_by_selection(object_name, new_object_name):
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        scene_object = bpy.data.objects.get(object_name)
        bpy.context.view_layer.objects.active = scene_object
        scene_object.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')

        for scene_object in bpy.context.selected_objects:
            if scene_object.name != object_name:
                scene_object.name = new_object_name

    @staticmethod
    def move_to_collection(object_name, collection_name):
        """
        Moves each object into the given collection.

        :param str object_name: The name of the object to move.
        :param str collection_name: The name of the collection to move the objects to.
        """
        object_instance = bpy.data.objects.get(object_name)
        collection_instance = bpy.data.collections.get(collection_name)

        if object_instance not in collection_instance.objects.values():
            collection_instance.objects.link(object_instance)

        for collection in bpy.data.collections:
            if collection.name != collection_name:
                if object_instance in collection.objects.values():
                    collection.objects.unlink(object_instance)

    @staticmethod
    def remove_from_collection(object_name, collection_name):
        """
        Removes each object from the given collection.

        :param str object_name: The name of the object to move.
        :param str collection_name: The name of the collection to remove objects from.
        """
        object_instance = bpy.data.objects.get(object_name)
        collection_instance = bpy.data.collections.get(collection_name)

        if object_instance in collection_instance.objects.values():
            collection_instance.objects.unlink(object_instance)

    @staticmethod
    def parent_to(child_name, parent_name):
        """
        Parent to child object to the parent object.

        :param str child_name: The name of the child.
        :param str parent_name: The name of the parent.
        """
        child_object = bpy.data.objects.get(str(child_name))
        parent_object = bpy.data.objects.get(str(parent_name))
        if child_object and parent_object:
            child_object.parent = parent_object

    @staticmethod
    def set_object_transforms(object_name, transforms):
        """
        Sets the world transform on an object.

        :param str object_name: The name of the object to move.
        :param dict transforms: A dictionary of location, rotation, and scale.
        """
        scene_object = bpy.data.objects[object_name]
        location = transforms.get('location')
        rotation = transforms.get('rotation')
        scale = transforms.get('scale')

        if location:
            scene_object.location = location
        if rotation:
            scene_object.rotation = rotation
        if scale:
            scene_object.scale = scale

    @staticmethod
    def get_object_transforms(object_name, decimals=2):
        """
        Gets the transforms of an object.

        :param str object_name: The name of the object to move.
        :param int decimals: How many decimals to round each value to.
        :return dict: A dictionary of location, rotation, and scale.
        """
        scene_object = bpy.data.objects.get(object_name)
        return {
            'location': [round(i, decimals) for i in scene_object.location],
            'rotation': [round(i, decimals) for i in scene_object.rotation_euler],
            'scale': [round(i, decimals) for i in scene_object.scale]
        }

    @staticmethod
    def stash_animation_data(object_name):
        """
        Stashes the active action on an object into its nla strips.

        :param str object_name: The name of the object of type armature with animation data.
        """
        rig_object = bpy.data.objects.get(object_name)
        Blender.stash_animation_data(rig_object)

    @staticmethod
    def set_all_action_attributes(object_name, attributes):
        """
        Sets the action attributes to the provided values.

        :param str object_name: The name of the object.
        :param dict attributes: The values of the action attributes.
        """
        scene_object = bpy.data.objects.get(object_name)
        Blender.set_all_action_attributes(scene_object, attributes)

    @staticmethod
    def get_bone_path_to_root(rig_object_name, bone_name, include_object=True):
        """
        Gets parent bone names as a list.

        :param str rig_object_name: The name of the rig object.
        :param str bone_name: A bone name.
        :param bool include_object: A list of bone names.
        """
        rig_object = bpy.data.objects.get(rig_object_name)
        return Blender.get_bone_path_to_root(rig_object, bone_name, include_object)

    @staticmethod
    def get_world_bone_translation_for_frame(rig_name, bone_name, action_name, frame, control_rig_name=None, decimals=2):
        """
        Gets the transformations of the given bone on the given frame.

        :param str rig_name: The name of the rig object.
        :param str bone_name: The name of the bone to get the transforms of.
        :param str action_name: The name of the action.
        :param float frame: The frame number.
        :param str control_rig_name: The name of the rig object.
        :param int decimals: How many decimals to round each value to.
        :return tuple: The world translation.
        """
        rig_object = bpy.data.objects.get(rig_name)
        bone = rig_object.pose.bones.get(bone_name)
        action = bpy.data.actions.get(action_name)

        # deselect everything
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        if control_rig_name:
            control_rig = bpy.data.objects.get(control_rig_name)
            control_rig.select_set(True)
            bpy.context.view_layer.objects.active = control_rig
            control_rig.animation_data.action = action
        else:
            rig_object.select_set(True)
            bpy.context.view_layer.objects.active = rig_object
            rig_object.animation_data.action = action

        bpy.context.scene.frame_set(frame)

        # get the world matrix for the bone
        bone_world_matrix = rig_object.matrix_world @ bone.matrix

        return [round(i, decimals) for i in bone_world_matrix.to_translation()]

    @staticmethod
    def send2ue():
        """
        Runs the send to unreal operator.
        """
        bpy.ops.wm.send2ue()

    @staticmethod
    def run_addon_operator(addon_name, operator_name, args=None, kwargs=None):
        """
        Runs the given operator.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        operator_context = getattr(bpy.ops, addon_name)
        operator = getattr(operator_context, operator_name)
        operator(*args, **kwargs)

    @staticmethod
    def run_property_group_method(context_name, addon_name, method_name, args=None, kwargs=None):
        """
        Runs the given operator.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        method = Blender.get_addon_property(context_name, addon_name, method_name)
        if method:
            return method(*args, **kwargs)

    @staticmethod
    def has_driver_namespace(name):
        """
        Checks if the given driver namespace exists.
        """
        return bool(bpy.app.driver_namespace.get(name))

    @staticmethod
    def enable_addon(addon_name):
        """
        Enable the given addon.

        :param object addon_name: The addon name.
        """
        bpy.ops.preferences.addon_enable(module=addon_name)

    @staticmethod
    def create_predefined_collections():
        """
        Runs the create predefined collections operator.
        """
        bpy.ops.send2ue.create_predefined_collections()

    @staticmethod
    def has_temp_file(sub_path):
        """
        Checks if the temp file path exists.
        """
        return os.path.exists(os.path.join(
            tempfile.gettempdir(),
            *sub_path
        ))

    @staticmethod
    def open_file(test_folder, file_name):
        # load in the file you will run tests on
        file_path = os.path.join(test_folder, 'test_files', 'blender_files', file_name)
        bpy.ops.wm.open_mainfile(filepath=file_path)

    @staticmethod
    def save_file(test_folder, file_name):
        file_path = os.path.join(test_folder, 'test_files', 'blender_files', file_name)
        bpy.ops.wm.save_mainfile(filepath=file_path)

    @staticmethod
    def delete_file(test_folder, file_name):
        file_path = os.path.join(test_folder, 'test_files', 'blender_files', file_name)
        os.remove(file_path)

    @staticmethod
    def open_default():
        # restore blend file to the default test file
        bpy.ops.wm.read_homefile(app_template="")

    @staticmethod
    def duplicate_with_linked_data(object_name, new_object_name, location):
        if not bpy.data.objects.get(new_object_name):
            scene_object = bpy.data.objects.get(object_name)
            scene_object_duplicate = bpy.data.objects.new(new_object_name, scene_object.data)
            bpy.context.scene.collection.objects.link(scene_object_duplicate)

            scene_object_duplicate.location.x = location[0]
            scene_object_duplicate.location.y = location[1]
            scene_object_duplicate.location.z = location[2]

            return scene_object.data.name


class Blender:
    @staticmethod
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

    @staticmethod
    def get_parent_bone_list(rig_object, bone_name, bone_list=None):
        """
        Recursively adds parent bone names to a list.

        :param object rig_object: A object of type armature.
        :param str bone_name: A bone name.
        :param list bone_list: A list of bone names.
        """
        if bone_list is None:
            bone_list = []

        bone = rig_object.data.bones.get(bone_name)
        if bone.parent:
            bone_list = Blender.get_parent_bone_list(rig_object, bone.parent.name, bone_list)
        bone_list.append(bone_name)
        return bone_list

    @staticmethod
    def get_bone_path_to_root(rig_object, bone_name, include_object=True):
        """
        Gets parent bone names as a list.

        :param object rig_object: A object of type armature.
        :param str bone_name: A bone name.
        :param bool include_object: A list of bone names.
        """
        bone_list = list(reversed(Blender.get_parent_bone_list(rig_object, bone_name)))

        if include_object:
            bone_list.append(rig_object.name)

        return bone_list

    @staticmethod
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

    @staticmethod
    def set_all_action_attributes(scene_object, attributes):
        """
        Sets the action attributes to the provided values.

        :param object scene_object: A scene object.
        :param dict attributes: The values of the action attributes.
        """
        if scene_object and scene_object.animation_data:
            for nla_track in scene_object.animation_data.nla_tracks:
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

    @staticmethod
    def set_action_location(action, world_location):
        """
        Sets the world location of an action based of the first frame of the action
        and returns its original world location.

        :param bpy.types.Action action: A object.
        :param list world_location: x,y,z coordinates.
        :returns: The original world location values of the given object.
        :rtype: list
        """
        original_location = []
        if action:
            for fcurve in action.fcurves:
                if fcurve.data_path == 'location':
                    # the offset from the first location keyframe and the passed in world location
                    offset = world_location[fcurve.array_index] - fcurve.keyframe_points[0].co[1]
                    for keyframe_point in fcurve.keyframe_points:
                        # save the original location
                        original_location.append(keyframe_point.co[1])

                        # apply the offset to all keys and handles
                        keyframe_point.co[1] = keyframe_point.co[1] + offset
                        keyframe_point.handle_left[1] = keyframe_point.handle_left[1] + offset
                        keyframe_point.handle_right[1] = keyframe_point.handle_right[1] + offset
        return original_location

    @staticmethod
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
                        action_names = Blender.get_action_names(rig_object)
                        if action_names.count(strip.action.name) > 1:
                            rig_object.animation_data.nla_tracks.remove(nla_track)

    @staticmethod
    def stash_animation_data(rig_object):
        """
        Stashes the active action on an object into its nla strips.

        :param object rig_object: A object of type armature with animation data.
        """
        if rig_object.animation_data:
            # if there is an active action on the rig object
            active_action = rig_object.animation_data.action

            attributes = Blender.get_all_action_attributes(rig_object)

            # remove any nla tracks that have the active action, have duplicate names, or no strips
            Blender.clean_nla_tracks(rig_object, active_action)

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

            Blender.set_all_action_attributes(rig_object, attributes)

    @staticmethod
    def get_addon_property(context_name, addon_name, property_name):
        # handle addon preferences
        if context_name == 'preferences':
            properties = bpy.context.preferences.addons[addon_name].preferences
        # otherwise the normal contexts
        else:
            context = getattr(bpy.context, context_name)
            properties = getattr(context, addon_name)

        module_path = property_name.split('.')
        try:
            for index, sub_property_name in enumerate(module_path, 1):
                if index == len(module_path):
                    return getattr(properties, sub_property_name)
                properties = getattr(properties, sub_property_name)
        except AttributeError:
            return None

    @staticmethod
    def has_addon_property(context_name, addon_name, property_name):
        # handle addon preferences
        if context_name == 'preferences':
            properties = bpy.context.preferences.addons[addon_name].preferences
        # otherwise the normal contexts
        else:
            context = getattr(bpy.context, context_name)
            properties = getattr(context, addon_name)

        module_path = property_name.split('.')
        try:
            for index, sub_property_name in enumerate(module_path, 1):
                if index == len(module_path):
                    return hasattr(properties, sub_property_name)
                properties = getattr(properties, sub_property_name)
        except AttributeError:
            return False

    @staticmethod
    def create_empty(name):
        empty_object = bpy.data.objects.get(name)
        if not empty_object:
            empty_object = bpy.data.objects.new(name, object_data=None)

        if empty_object not in bpy.context.scene.collection.objects.values():
            bpy.context.scene.collection.objects.link(empty_object)
