# Copyright Epic Games, Inc. All Rights Reserved.

import os
import json
import time
import sys
import inspect
from xmlrpc.client import ProtocolError
from http.client import RemoteDisconnected

sys.path.append(os.path.dirname(__file__))
import rpc.factory
import remote_execution

try:
    import unreal
except ModuleNotFoundError:
    pass

REMAP_PAIRS = []
UNREAL_PORT = int(os.environ.get('UNREAL_PORT', 9998))

# use a different remap pairs when inside a container
if os.environ.get('TEST_ENVIRONMENT'):
    UNREAL_PORT = int(os.environ.get('UNREAL_PORT', 8998))
    REMAP_PAIRS = [(os.environ.get('HOST_REPO_FOLDER'), os.environ.get('CONTAINER_REPO_FOLDER'))]

# this defines a the decorator that makes function run as remote call in unreal
remote_unreal_decorator = rpc.factory.remote_call(
    port=UNREAL_PORT,
    default_imports=['import unreal'],
    remap_pairs=REMAP_PAIRS,
)

rpc_client = rpc.client.RPCClient(port=UNREAL_PORT)
unreal_response = ''


def get_response():
    """
    Gets the stdout produced by the remote python call.

    :return str: The stdout produced by the remote python command.
    """
    if unreal_response:
        full_output = []
        output = unreal_response.get('output')
        if output:
            full_output.append('\n'.join([line['output'] for line in output if line['type'] != 'Warning']))

        result = unreal_response.get('result')
        if result != 'None':
            full_output.append(result)

        return '\n'.join(full_output)
    return ''


def add_indent(commands, indent):
    """
    Adds an indent to the list of python commands.

    :param list commands: A list of python commands that will be run by unreal engine.
    :param str indent: A str of tab characters.
    :return str: A list of python commands that will be run by unreal engine.
    """
    indented_line = []
    for command in commands:
        for line in command.split('\n'):
            indented_line.append(f'{indent}{line}')

    return indented_line


def print_python(commands):
    """
    Prints the list of commands as formatted output for debugging and development.

    :param list commands: A list of python commands that will be run by unreal engine.
    """
    if os.environ.get('REMOTE_EXECUTION_SHOW_PYTHON'):
        dashes = '-' * 50
        label = 'Remote Execution'
        sys.stdout.write(f'{dashes}{label}{dashes}\n')

        # get the function name
        current_frame = inspect.currentframe()
        caller_frame = inspect.getouterframes(current_frame, 2)
        function_name = caller_frame[3][3]

        kwargs = caller_frame[3][0].f_locals
        kwargs.pop('commands', None)
        kwargs.pop('result', None)

        # write out the function name and its arguments
        sys.stdout.write(
            f'{function_name}(kwargs={json.dumps(kwargs, indent=2, default=lambda element: type(element).__name__)})\n')

        # write out the code with the lines numbers
        for index, line in enumerate(commands, 1):
            sys.stdout.write(f'{index} {line}\n')

        sys.stdout.write(f'{dashes}{"-" * len(label)}{dashes}\n')


def run_unreal_python_commands(remote_exec, commands, failed_connection_attempts=0):
    """
    Finds the open unreal editor with remote connection enabled, and sends it python commands.

    :param object remote_exec: A RemoteExecution instance.
    :param list commands: A list of python commands that will be run by unreal engine.
    :param int failed_connection_attempts: A counter that keeps track of how many times an editor connection attempt
    was made.
    """
    if failed_connection_attempts == 0:
        print_python(commands)

    # wait a tenth of a second before attempting to connect
    time.sleep(0.1)
    try:
        # try to connect to an editor
        for node in remote_exec.remote_nodes:
            remote_exec.open_command_connection(node.get("node_id"))

        # if a connection is made
        if remote_exec.has_command_connection():
            # run the import commands and save the response in the global unreal_response variable
            global unreal_response
            unreal_response = remote_exec.run_command('\n'.join(commands), unattended=False)

        # otherwise make an other attempt to connect to the engine
        else:
            if failed_connection_attempts < 50:
                run_unreal_python_commands(remote_exec, commands, failed_connection_attempts + 1)
            else:
                remote_exec.stop()
                raise ConnectionError("Could not find an open Unreal Editor instance!")

    # catch all errors
    except:
        raise ConnectionError("Could not find an open Unreal Editor instance!")

    # shutdown the connection
    finally:
        remote_exec.stop()

    return get_response()


def run_commands(commands):
    """
    Runs a list of python commands and returns the result of the output.

    :param list commands: A formatted string of python commands that will be run by unreal engine.
    :return str: The stdout produced by the remote python command.
    """
    # wrap the commands in a try except so that all exceptions can be logged in the output
    commands = ['try:'] + add_indent(commands, '\t') + ['except Exception as error:', '\tprint(error)']

    # start a connection to the engine that lets you send python-commands.md strings
    remote_exec = remote_execution.RemoteExecution()
    remote_exec.start()

    # send over the python code as a string and run it
    return run_unreal_python_commands(remote_exec, commands)


def is_connected():
    """
    Checks the rpc server connection
    """
    try:
        return rpc_client.proxy.is_running()
    except (RemoteDisconnected, ConnectionRefusedError, ProtocolError):
        return False


def set_rpc_env(key, value):
    """
    Sets an env value on the unreal RPC server.
    """
    rpc_client.proxy.set_env(key, value)


def bootstrap_unreal_with_rpc_server():
    """
    Bootstraps the running unreal editor with the unreal rpc server if it doesn't already exist.
    """
    if not os.environ.get('TEST_ENVIRONMENT'):
        if not is_connected():
            import bpy
            rpc_response_timeout = bpy.context.preferences.addons["send2ue"].preferences.rpc_response_timeout
            dependencies_path = os.path.dirname(__file__)
            result = run_commands(
                [
                    'import sys',
                    'import os',
                    'import threading',
                    'for thread in threading.enumerate():',
                    '\tif thread.name =="UnrealRPCServer":',
                    '\t\tthread.kill()',
                    f'os.environ["RPC_TIME_OUT"] = "{rpc_response_timeout}"',
                    f'sys.path.append(r"{dependencies_path}")',
                    'from rpc import unreal_server',
                    'rpc_server = unreal_server.RPCServer()',
                    'rpc_server.start(threaded=True)',
                ]
            )
            if result:
                raise ConnectionError(result)


class Unreal:
    @staticmethod
    def get_value(value, unreal_type=None):
        """
        Gets the value as an unreal type.

        :param Any value: A value that can be any generic python type.
        :param str unreal_type: The name of an unreal type.
        :return Any: The converted unreal value.
        """
        if unreal_type == 'Array':
            if isinstance(value, str):
                value = value.split(',')

            if value:
                array = unreal.Array(type(value[0]))
                for element in value:
                    array.append(element)
                return array

        elif unreal_type == 'Int32Interval':
            int_32_interval = unreal.Int32Interval()
            int_32_interval.set_editor_property("min", value[0])
            int_32_interval.set_editor_property("max", value[1])
            return int_32_interval

        elif unreal_type == 'Vector':
            return unreal.Vector(x=value[0], y=value[1], z=value[2])

        elif unreal_type == 'Rotator':
            return unreal.Rotator(roll=value[0], pitch=value[1], yaw=value[2])

        elif unreal_type == 'Color':
            return unreal.Color(r=value[0], g=value[1], b=value[2], a=value[3])

        elif unreal_type == 'Name':
            return unreal.Name(value)

        elif unreal_type == 'SoftObjectPath':
            return unreal.SoftObjectPath(path_string=value)

        elif unreal_type == 'Enum':
            enum_value = unreal
            for attribute in value.split('.')[1:]:
                enum_value = getattr(enum_value, attribute)
            return enum_value

        elif unreal_type == 'Asset':
            if value:
                return Unreal.get_asset(value)
            else:
                return None
        else:
            return value

    @staticmethod
    def get_asset(asset_path):
        """
        Adds the commands that load an unreal asset.

        :param str asset_path: The unreal project path of an asset.
        :return str: A list of python commands that will be run by unreal engine.
        """
        asset = unreal.load_asset(asset_path)
        if not asset:
            raise RuntimeError(f"The {asset_path} does not exist in the project!")
        return asset

    @staticmethod
    def get_component_handles(blueprint_asset_path):
        """
        Gets all subobject data handles of a blueprint asset.

        :param str blueprint_asset_path: The unreal path to the blueprint asset.
        :return list(subobjectDataHandle) data_handle: A list of subobject data handles within the blueprint asset.
        """
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

        blueprint_asset = unreal.load_asset(blueprint_asset_path)
        subobject_data_handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint_asset)
        return subobject_data_handles

    @staticmethod
    def get_groom_handle(component_handles, binding_asset_path, groom_asset_path):
        """
        Gets the subobject data handle of a groom component from a list of component handles that contains assets drawn
        from binding_asset_path and groom_asset_path.

        :param str component_handles: A list of component handles.
        :param str binding_asset_path: The path to the unreal binding asset.
        :param str groom_asset_path: The path to the unreal groom asset.
        :return subobjectDataHandle data_handle: The subobject data handle of the groom component.
        """
        bp_subobject_library = unreal.SubobjectDataBlueprintFunctionLibrary

        for data_handle in component_handles:
            subobject = bp_subobject_library.get_object(bp_subobject_library.get_data(data_handle))
            if type(subobject) == unreal.GroomComponent:
                has_groom = subobject.get_editor_property('groom_asset') == unreal.load_asset(groom_asset_path)
                has_binding = subobject.get_editor_property('binding_asset') == unreal.load_asset(binding_asset_path)
                if has_groom and has_binding:
                    return data_handle
        return None

    @staticmethod
    def get_skeletal_mesh_handle(component_handles, mesh_asset_path):
        """
        Gets the subobject data handle of a skeletal mesh component from a list of component handles that contains
        asset drawn from mesh_asset_path.

        :param str component_handles: A list of component handles.
        :param str mesh_asset_path: The path to the unreal mesh asset.
        :return subobjectDataHandle data_handle: The subobject data handle of the skeletal mesh component.
        """
        bp_subobject_library = unreal.SubobjectDataBlueprintFunctionLibrary

        for data_handle in component_handles:
            subobject = bp_subobject_library.get_object(bp_subobject_library.get_data(data_handle))
            if type(subobject) == unreal.SkeletalMeshComponent:
                if subobject.get_skeletal_mesh_asset() == unreal.load_asset(mesh_asset_path):
                    return data_handle
        return None

    @staticmethod
    def get_bone_pose_for_frame(anim_sequence, bone_name, frame, extract_root_motion):
        """
        Gets the local transform of the bone at the specified frame in the anim sequence.


        :param object anim_sequence: An unreal anim sequence object.
        :param str bone_name: A bone name.
        :param float frame: The frame to get the transform at.
        :param bool extract_root_motion: Whether to include root motion in the returned transform.
        :returns: A transform.
        :rtype: unreal.Transform
        """
        pose_options = unreal.AnimPoseEvaluationOptions()
        pose_options.set_editor_property('extract_root_motion', extract_root_motion)
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_frame(anim_sequence, frame, pose_options)
        return unreal.AnimPoseExtensions.get_bone_pose(pose, bone_name)

    @staticmethod
    def set_settings(property_group, data_object):
        """
        Sets a group of properties onto an unreal object.

        :param dict property_group: A dictionary of properties and their data.
        :param object data_object: A object.
        """
        for attribute, data in property_group.items():
            value = Unreal.get_value(
                value=data.get('value'),
                unreal_type=data.get('unreal_type'),
            )
            data_object.set_editor_property(attribute, value)
        return data_object

    @staticmethod
    def is_parent_component_of_child(parent_data_handle, child_data_handle):
        """
        Checks to see if the component associated with child_data_handle is parented under a component associated with
        parent_data_handle.

        :param subobjectDataHandle parent_data_handle: The unreal handle of the parent component.
        :param subobjectDataHandle child_data_handle: The unreal handle of the child component.
        :return bool: Whether or not the child_data_handle is a child of parent_data_handle.
        """
        bp_subobject_library = unreal.SubobjectDataBlueprintFunctionLibrary
        child_data = bp_subobject_library.get_data(child_data_handle)
        return bp_subobject_library.is_attached_to(child_data, parent_data_handle)

    @staticmethod
    def object_attributes_to_dict(object_instance):
        """
        Converts the attributes of the given python object to a dictionary.

        :param object object_instance: A object instance.
        :return dict: A dictionary of attributes and values.
        """
        data = {}
        if object_instance:
            for attribute in dir(object_instance):
                value = getattr(object_instance, attribute)
                if isinstance(value, (bool, str, float, int, list)) and not attribute.startswith("_"):
                    data[attribute] = getattr(object_instance, attribute)
        return data

    @staticmethod
    def create_asset(asset_path, asset_class=None, asset_factory=None, unique_name=True):
        """
        Creates a new unreal asset.

        :param str asset_path: The project path to the asset.
        :param type(Class) asset_class: The unreal asset class.
        :param Factory asset_factory: The unreal factory.
        :param bool unique_name: Whether or not the check if the name is unique before creating the asset.
        """
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        if unique_name:
            asset_path, _ = asset_tools.create_unique_asset_name(
                base_package_name=asset_path,
                suffix=''
            )
        path, name = asset_path.rsplit("/", 1)
        return asset_tools.create_asset(
            asset_name=name,
            package_path=path,
            asset_class=asset_class,
            factory=asset_factory
        )

    @staticmethod
    def create_binding_asset(groom_asset_path, mesh_asset_path):
        """
        Creates a groom binding asset.

        :param str groom_asset_path: The unreal asset path to the imported groom asset.
        :param str mesh_asset_path: The unreal asset path to the associated mesh asset.
        :return str binding_asset_path: The unreal asset path to the created binding asset.
        """
        mesh_asset = Unreal.get_asset(mesh_asset_path)

        # only create binding asset if the particle system's mesh asset is a skeletal mesh
        if mesh_asset.__class__.__name__ == 'SkeletalMesh':
            groom_asset = Unreal.get_asset(groom_asset_path)

            binding_asset_path = f'{groom_asset_path}_{mesh_asset.get_name()}_Binding'
            temp_asset_path = f'{binding_asset_path}_Temp'

            # renames the existing binding asset (one that had the same name) that will be consolidated
            existing_binding_asset = unreal.load_asset(binding_asset_path)
            if existing_binding_asset:
                unreal.EditorAssetLibrary.rename_asset(
                    binding_asset_path,
                    temp_asset_path
                )

            # create the binding asset
            groom_binding_asset = Unreal.create_asset(
                binding_asset_path,
                unreal.GroomBindingAsset,
                unreal.GroomBindingFactory(),
                False
            )

            # source groom asset and target skeletal mesh for the binding asset
            groom_binding_asset.set_editor_property('groom', groom_asset)
            groom_binding_asset.set_editor_property('target_skeletal_mesh', mesh_asset)

            # if a previous version of the binding asset exists, consolidate all references with new asset
            if existing_binding_asset:
                unreal.EditorAssetLibrary.consolidate_assets(groom_binding_asset, [existing_binding_asset])
                unreal.EditorAssetLibrary.delete_asset(temp_asset_path)

            return binding_asset_path

    @staticmethod
    def create_blueprint_asset(blueprint_asset_path):
        """
        Creates a blueprint asset at the specified path.
        :param str blueprint_asset_path: The unreal path where the blueprint asset will be created.
        :return object(Blueprint): The blueprint asset created.
        """
        bp_factory = unreal.BlueprintFactory()
        bp_factory.set_editor_property("parent_class", unreal.Actor)

        return Unreal.create_asset(blueprint_asset_path, None, bp_factory, False)

    @staticmethod
    def create_blueprint_component(blueprint_asset, parent_handle, component_class, component_name='untitled_component'):
        """
        Creates a blueprint component for a blueprint asset.

        :param object(Blueprint) blueprint_asset: The blueprint context for the component to be created.
        :param SubobjectDataHandle parent_handle: The parent handle of the new component.
        :param type(Class) component_class: The class of the new subobject (component) that will be created.
        :param str component_name: The unreal path where the blueprint asset will be created.
        :return object(component), sub_handle: The component and its data handle.
        """
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        # add sub object
        sub_handle, fail_reason = subsystem.add_new_subobject(
            unreal.AddNewSubobjectParams(
                parent_handle=parent_handle,
                new_class=component_class,
                blueprint_context=blueprint_asset)
        )

        if not fail_reason.is_empty():
            raise Exception("ERROR from sub_object_subsystem.add_new_subobject: {fail_reason}")

        # Need futher investigation to whether attach_subobject call is actually necessary
        subsystem.attach_subobject(parent_handle, sub_handle)
        subsystem.rename_subobject(handle=sub_handle, new_name=unreal.Text(component_name))

        bp_subobject_library = unreal.SubobjectDataBlueprintFunctionLibrary
        component = bp_subobject_library.get_object(bp_subobject_library.get_data(sub_handle))

        return component, sub_handle

    @staticmethod
    def create_blueprint_for_groom(groom_asset_path, mesh_asset_path, binding_asset_path):
        """
        Creates a blueprint asset with a skeletal mesh component that has a child groom component populated by a
        groom asset and binding asset.

        :param dict groom_asset_path: The unreal asset path to the imported groom asset.
        :param str mesh_asset_path: The unreal asset path to the associated mesh asset.
        :param str binding_asset_path: The unreal asset path to the created binding asset.
        :return str blueprint_asset_path: The unreal path to the blueprint asset.
        """
        groom_asset_name = groom_asset_path.split('/')[-1]
        mesh_asset_name = mesh_asset_path.split('/')[-1]

        blueprint_asset_path = f'{mesh_asset_path}_BP'

        # Todo figure out why create blueprint in None sometimes on linux
        blueprint_asset = Unreal.create_blueprint_asset(blueprint_asset_path)
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        root_handles = subsystem.k2_gather_subobject_data_for_blueprint(context=blueprint_asset) or []

        if root_handles:
            skeletal_comp, skeletal_comp_handle = Unreal.create_blueprint_component(
                blueprint_asset,
                root_handles[0],
                unreal.SkeletalMeshComponent,
                mesh_asset_name
            )

            if skeletal_comp and skeletal_comp_handle:
                # add imported skeletal mesh asset to skeletal mesh component
                skeletal_comp.set_skeletal_mesh_asset(unreal.load_asset(mesh_asset_path))

                groom_comp, groom_comp_handle = Unreal.create_blueprint_component(
                    blueprint_asset,
                    skeletal_comp_handle,
                    unreal.GroomComponent,
                    groom_asset_name
                )

                # add binding asset and groom asset to groom component
                groom_comp.set_groom_asset(unreal.load_asset(groom_asset_path))
                groom_comp.set_binding_asset(unreal.load_asset(binding_asset_path))
        return blueprint_asset_path

    @staticmethod
    def add_groom_component_to_blueprint(groom_asset_path, mesh_asset_path, binding_asset_path):
        """
        Adds a groom component to a blueprint asset with specific skeletal mesh. If queried blueprint asset does not
        exist, creates a blueprint asset with a skeletal mesh component that has a child groom component populated by a
        groom asset and binding asset.

        :param dict groom_asset_path: The unreal asset path to the imported groom asset.
        :param str mesh_asset_path: The unreal asset path to the associated mesh asset.
        :param str binding_asset_path: The unreal asset path to the created binding asset.
        :return str blueprint_asset_path: The unreal path to the blueprint asset.
        """
        asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry_options = unreal.AssetRegistryDependencyOptions()
        registry_options.set_editor_property('include_hard_package_references', True)

        groom_asset_name = groom_asset_path.split('/')[-1]

        references = list(asset_registry.get_referencers(mesh_asset_path, registry_options) or [])
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        bp_subobject_library = unreal.SubobjectDataBlueprintFunctionLibrary

        if references:
            for reference_path in references:
                if unreal.EditorAssetLibrary.find_asset_data(reference_path).asset_class_path.asset_name == 'Blueprint':

                    blueprint_asset = Unreal.get_asset(reference_path)
                    subobject_data_handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint_asset)

                    skeletal_mesh_component_handle = None
                    groom_component = None

                    groom_asset = Unreal.get_asset(groom_asset_path)
                    mesh_asset = Unreal.get_asset(mesh_asset_path)
                    binding_asset = Unreal.get_asset(binding_asset_path)

                    for data_handle in subobject_data_handles:
                        subobject = bp_subobject_library.get_object(bp_subobject_library.get_data(data_handle))
                        if type(subobject) == unreal.SkeletalMeshComponent:
                            if subobject.get_skeletal_mesh_asset() == mesh_asset:
                                skeletal_mesh_component_handle = data_handle
                        if type(subobject) == unreal.GroomComponent:
                            if subobject.get_editor_property('groom_asset') == groom_asset:
                                groom_component = subobject

                    if not groom_component:
                        groom_component, groom_component_handle = Unreal.create_blueprint_component(
                            blueprint_asset,
                            skeletal_mesh_component_handle,
                            unreal.GroomComponent,
                            groom_asset_name
                        )

                        # add binding asset and groom asset to groom component
                        groom_component.set_groom_asset(groom_asset)
                        groom_component.set_binding_asset(binding_asset)
                        unreal.EditorAssetLibrary.save_loaded_asset(blueprint_asset)

                    return str(reference_path)
        # if there is no references to the surface mesh asset, create new blueprint
        else:
            blueprint_asset_path = Unreal.create_blueprint_for_groom(
                groom_asset_path,
                mesh_asset_path,
                binding_asset_path
            )
            unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(blueprint_asset_path))
            return blueprint_asset_path

    @staticmethod
    def get_assets_on_actor(actor, only_type=None):
        """
        Gets only actors that are created by directly instancing assets.
        """
        assets = []

        # only get the asset type specified in only_type if it is provided
        if not only_type or only_type == 'StaticMesh':
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                if component.static_mesh and actor.get_class().get_name() == 'StaticMeshActor':
                    # make sure we only get one unique instance of the asset
                    if component.static_mesh not in assets:
                        assets.append(component.static_mesh)

        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            if component.skeletal_mesh:
                # only get the asset type specified in only_type if it is provided
                if not only_type or only_type == 'SkeletalMesh':
                    # make sure we only get one unique instance of the asset
                    if component.skeletal_mesh not in assets:
                        assets.append(component.skeletal_mesh)

                # only get the asset type specified in only_type if it is provided
                if not only_type or only_type == 'AnimSequence':
                    if component.animation_mode == unreal.AnimationMode.ANIMATION_SINGLE_NODE:
                        if component.animation_data and component.animation_data.anim_to_play not in assets:
                            assets.append(component.animation_data.anim_to_play)

        return assets

    @staticmethod
    def get_asset_actors_in_level():
        """
        Gets actors from the active level that have assets assigned to them.
        """
        actors = []
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        for actor in actor_subsystem.get_all_level_actors():
            if Unreal.get_assets_on_actor(actor):
                actors.append(actor)
        return actors

    @staticmethod
    def get_asset_actor_by_label(label):
        """
        Gets the asset actor by the given label.
        """
        for actor in Unreal.get_asset_actors_in_level():
            if label == actor.get_actor_label():
                return actor

    @staticmethod
    def has_asset_actor_with_label(label):
        """
        Checks if the level has actors with the given label.
        """
        for actor in Unreal.get_asset_actors_in_level():
            if label == actor.get_actor_label():
                return True
        return False

    @staticmethod
    def delete_all_asset_actors():
        """
        Deletes all actors from the active level that have assets assigned to them.
        """
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in Unreal.get_asset_actors_in_level():
            actor_subsystem.destroy_actor(actor)
            break

    @staticmethod
    def delete_asset_actor_with_label(label):
        """
        Deletes the actor with the given label.
        """
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in Unreal.get_asset_actors_in_level():
            if label == actor.get_actor_label():
                actor_subsystem.destroy_actor(actor)
                break


class UnrealImportAsset(Unreal):
    def __init__(self, file_path, asset_data, property_data):
        """
        Initializes the import with asset data and property data.

        :param str file_path: The full path to the file to import.
        :param dict asset_data: A dictionary that contains various data about the asset.
        :param PropertyData property_data: A property data instance that contains all property values of the tool.
        """
        self._file_path = file_path
        self._asset_data = asset_data
        self._property_data = property_data
        self._import_task = unreal.AssetImportTask()
        self._options = None

    def set_skeleton(self):
        """
        Sets a skeleton to the import options.
        """
        skeleton_path = self._asset_data.get('skeleton_asset_path')
        if skeleton_path:
            self._options.skeleton = self.get_asset(skeleton_path)

    def set_physics_asset(self):
        """
        Sets a physics asset to the import options.
        """
        asset_path = self._asset_data.get('asset_path')
        physics_asset_path = self._property_data.get('unreal_physics_asset_path', {}).get('value', '')
        default_physics_asset = f'{asset_path}_PhysicsAsset'
        # try to load the provided physics asset
        if physics_asset_path:
            physics_asset = unreal.load_asset(physics_asset_path)
        else:
            physics_asset = unreal.load_asset(default_physics_asset)

        if physics_asset:
            self._options.create_physics_asset = False
            self._options.physics_asset = physics_asset
        else:
            self._options.create_physics_asset = True

    def set_static_mesh_import_options(self):
        """
        Sets the static mesh import options.
        """
        if self._asset_data.get('_asset_type') == 'StaticMesh':
            self._options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            self._options.static_mesh_import_data.import_mesh_lo_ds = False

            import_data = unreal.FbxStaticMeshImportData()
            self.set_settings(
                self._property_data['unreal']['import_method']['fbx']['static_mesh_import_data'],
                import_data
            )
            self._options.static_mesh_import_data = import_data

    def set_skeletal_mesh_import_options(self):
        """
        Sets the skeletal mesh import options.
        """
        if self._asset_data.get('_asset_type') == 'SkeletalMesh':
            self.set_skeleton()
            self.set_physics_asset()
            self._options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
            self._options.skeletal_mesh_import_data.import_mesh_lo_ds = False
            import_data = unreal.FbxSkeletalMeshImportData()
            self.set_settings(
                self._property_data['unreal']['import_method']['fbx']['skeletal_mesh_import_data'],
                import_data
            )
            self._options.skeletal_mesh_import_data = import_data

    def set_animation_import_options(self):
        """
        Sets the animation import options.
        """
        if self._asset_data.get('_asset_type') == 'AnimSequence':
            self.set_skeleton()
            self.set_physics_asset()
            self._options.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
            import_data = unreal.FbxAnimSequenceImportData()
            self.set_settings(
                self._property_data['unreal']['import_method']['fbx']['anim_sequence_import_data'],
                import_data,
            )
            self._options.anim_sequence_import_data = import_data

    def set_texture_import_options(self):
        """
        Sets the texture import options.
        """
        if self._property_data.get('import_materials_and_textures', {}).get('value', False):
            import_data = unreal.FbxTextureImportData()
            self.set_settings(
                self._property_data['unreal']['import_method']['fbx']['texture_import_data'],
                import_data
            )
            self._options.texture_import_data = import_data

    def set_groom_import_options(self):
        """
        Sets the groom import options.
        """
        self._options = unreal.GroomImportOptions()

        if self._asset_data.get('_asset_type') == 'Groom':
            import_data = unreal.GroomConversionSettings()
            self.set_settings(
                self._property_data['unreal']['import_method']['abc']['conversion_settings'],
                import_data
            )
            self._options.set_editor_property('conversion_settings', import_data)

    def set_fbx_import_task_options(self):
        """
        Sets the FBX import options.
        """
        self.set_import_task_options()

        import_materials_and_textures = self._property_data.get('import_materials_and_textures', {}).get('value', True)

        import_mesh = self._asset_data.get('_asset_type') in ['SkeletalMesh', 'StaticMesh']
        import_animations = self._asset_data.get('_asset_type') == 'AnimSequence'
        import_as_skeletal = self._asset_data.get('_asset_type') == 'SkeletalMesh'

        # set the options
        self._options = unreal.FbxImportUI()
        self._options.set_editor_property('automated_import_should_detect_type', False)
        self._options.set_editor_property('import_mesh', import_mesh)
        self._options.set_editor_property('import_as_skeletal', import_as_skeletal)
        self._options.set_editor_property('import_animations', import_animations)
        self._options.set_editor_property('import_materials', import_materials_and_textures)
        self._options.set_editor_property('import_textures', import_materials_and_textures)

        # set the static mesh import options
        self.set_static_mesh_import_options()

        # add the skeletal mesh import options
        self.set_skeletal_mesh_import_options()

        # add the animation import options
        self.set_animation_import_options()

        # add the texture import options
        self.set_texture_import_options()

    def set_abc_import_task_options(self):
        """
        Sets the ABC import options.
        """
        # set the options
        self.set_import_task_options()
        # set the groom import options
        self.set_groom_import_options()

    def set_import_task_options(self):
        """
        Sets common import options.
        """
        self._import_task.set_editor_property('filename', self._file_path)
        self._import_task.set_editor_property('destination_path', self._asset_data.get('asset_folder'))
        self._import_task.set_editor_property('replace_existing', True)
        self._import_task.set_editor_property('replace_existing_settings', True)
        self._import_task.set_editor_property(
            'automated',
            not self._property_data.get('advanced_ui_import', {}).get('value', False)
        )

    def run_import(self):
        # assign the options object to the import task and import the asset
        self._import_task.options = self._options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([self._import_task])

        return list(self._import_task.get_editor_property('imported_object_paths'))


class UnrealImportSequence(Unreal):
    def __init__(self, asset_path, file_path, track_name, start=None, end=None):
        """
        Initializes the import with asset data and property data.

        :param str asset_path: The project path to the asset.
        :param str file_path: The full file path to the import file.
        :param str track_name: The name of the track.
        :param int start: The start frame.
        :param int end: The end frame.
        """
        self._asset_path = asset_path
        self._file_path = file_path
        self._track_name = track_name
        self._control_channel_mappings = []
        self._sequence = self.get_asset(asset_path)
        self._control_rig_settings = unreal.MovieSceneUserImportFBXControlRigSettings()

        if start and end:
            self._control_rig_settings.start_time_range = int(start)
            self._control_rig_settings.end_time_range = int(end)

    @staticmethod
    def get_control_rig_mappings():
        """
        Set the control rig mappings.

        :return list[tuple]: A list channels, transforms and negations that define the control rig mappings.
        """
        return [
            (unreal.FControlRigChannelEnum.BOOL, unreal.FTransformChannelEnum.TRANSLATE_X, False),
            (unreal.FControlRigChannelEnum.FLOAT, unreal.FTransformChannelEnum.TRANSLATE_Y, False),
            (unreal.FControlRigChannelEnum.VECTOR2DX, unreal.FTransformChannelEnum.TRANSLATE_X, False),
            (unreal.FControlRigChannelEnum.VECTOR2DY, unreal.FTransformChannelEnum.TRANSLATE_Y, False),
            (unreal.FControlRigChannelEnum.POSITION_X, unreal.FTransformChannelEnum.TRANSLATE_X, False),
            (unreal.FControlRigChannelEnum.POSITION_Y, unreal.FTransformChannelEnum.TRANSLATE_Y, False),
            (unreal.FControlRigChannelEnum.POSITION_Z, unreal.FTransformChannelEnum.TRANSLATE_Z, False),
            (unreal.FControlRigChannelEnum.ROTATOR_X, unreal.FTransformChannelEnum.ROTATE_X, False),
            (unreal.FControlRigChannelEnum.ROTATOR_Y, unreal.FTransformChannelEnum.ROTATE_Y, False),
            (unreal.FControlRigChannelEnum.ROTATOR_Z, unreal.FTransformChannelEnum.ROTATE_Z, False),
            (unreal.FControlRigChannelEnum.SCALE_X, unreal.FTransformChannelEnum.SCALE_X, False),
            (unreal.FControlRigChannelEnum.SCALE_Y, unreal.FTransformChannelEnum.SCALE_Y, False),
            (unreal.FControlRigChannelEnum.SCALE_Z, unreal.FTransformChannelEnum.SCALE_Z, False)

        ]

    def set_control_mapping(self, control_channel, fbx_channel, negate):
        """
        Sets the control mapping.

        :param str control_channel: The unreal enum of the control channel.
        :param str fbx_channel: The unreal enum of the transform channel.
        :param bool negate: Whether or not the mapping is negated.
        :return str: A list of python commands that will be run by unreal engine.
        """
        control_map = unreal.ControlToTransformMappings()
        control_map.set_editor_property('control_channel', control_channel)
        control_map.set_editor_property('fbx_channel', fbx_channel)
        control_map.set_editor_property('negate', negate)
        self._control_maps.append(control_map)

    def remove_level_sequence_keyframes(self):
        """
        Removes all key frames from the given sequence and track name.
        """
        bindings = {binding.get_name(): binding for binding in self._sequence.get_bindings()}
        binding = bindings.get(self._track_name)
        track = binding.get_tracks()[0]
        section = track.get_sections()[0]
        for channel in section.get_channels():
            for key in channel.get_keys():
                channel.remove_key(key)

    def run_import(self, import_type='control_rig'):
        """
        Imports key frames onto the given sequence track name from a file.

        :param str import_type: What type of sequence import to run.
        """
        sequencer_tools = unreal.SequencerTools()
        self.remove_level_sequence_keyframes()

        if import_type == 'control_rig':
            for control_channel, fbx_channel, negate in self.get_control_rig_mappings():
                self.set_control_mapping(control_channel, fbx_channel, negate)

            self._control_rig_settings.control_channel_mappings = self._control_channel_mappings
            self._control_rig_settings.insert_animation = False
            self._control_rig_settings.import_onto_selected_controls = False
            sequencer_tools.import_fbx_to_control_rig(
                world=unreal.EditorLevelLibrary.get_editor_world(),
                sequence=self._sequence,
                actor_with_control_rig_track=self._track_name,
                selected_control_rig_names=[],
                import_fbx_control_rig_settings=self._control_rig_settings,
                import_filename=self._file_path
            )


@rpc.factory.remote_class(remote_unreal_decorator)
class UnrealRemoteCalls:
    @staticmethod
    def get_lod_count(asset_path):
        """
        Gets the number of lods on the given asset.

        :param str asset_path: The path to the unreal asset.
        :return int: The number of lods on the asset.
        """
        lod_count = 0
        asset = Unreal.get_asset(asset_path)
        if asset.__class__.__name__ == 'SkeletalMesh':
            lod_count = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem).get_lod_count(asset)

        if asset.__class__.__name__ == 'StaticMesh':
            lod_count = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_lod_count(asset)

        return lod_count
    @staticmethod
    def get_asset_type(asset_path):
        """
        Gets the asset type of the given asset.

        :param str asset_path: The path to the unreal asset.
        :return str: The number of lods on the asset.
        """
        asset = Unreal.get_asset(asset_path)
        if asset:
            return asset.__class__.__name__

    @staticmethod
    def asset_exists(asset_path):
        """
        Checks to see if an asset exist in unreal.

        :param str asset_path: The path to the unreal asset.
        :return bool: Whether the asset exists.
        """
        return bool(unreal.load_asset(asset_path))

    @staticmethod
    def directory_exists(asset_path):
        """
        Checks to see if a directory exist in unreal.

        :param str asset_path: The path to the unreal asset.
        :return bool: Whether or not the asset exists.
        """
        # TODO fix this when the unreal API is fixed where it queries the registry correctly
        #  https://jira.it.epicgames.com/browse/UE-142234
        # return unreal.EditorAssetLibrary.does_directory_exist(asset_path)
        return True

    @staticmethod
    def get_static_mesh_collision_info(asset_path):
        """
        Gets the number of convex and simple collisions on a static mesh.

        :param str asset_path: The path to the unreal asset.
        :return str: The name of the complex collision.
        """
        mesh = Unreal.get_asset(asset_path)
        return {
            'simple': unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_simple_collision_count(mesh),
            'convex': unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_convex_collision_count(mesh),
            'customized': mesh.get_editor_property('customized_collision')
        }

    @staticmethod
    def get_material_index_by_name(asset_path, material_name):
        """
        Checks to see if an asset has a complex collision.

        :param str asset_path: The path to the unreal asset.
        :param str material_name: The name of the material.
        :return str: The name of the complex collision.
        """
        mesh = Unreal.get_asset(asset_path)
        if mesh.__class__.__name__ == 'SkeletalMesh':
            for index, material in enumerate(mesh.materials):
                if material.material_slot_name == material_name:
                    return index
        if mesh.__class__.__name__ == 'StaticMesh':
            for index, material in enumerate(mesh.static_materials):
                if material.material_slot_name == material_name:
                    return index

    @staticmethod
    def get_enabled_plugins():
        """
        Checks to see if the current project has certain plugins enabled.

        :returns: Returns a list of missing plugins if any.
        :rtype: list[str]
        """
        uproject_path = unreal.Paths.get_project_file_path()
        with open(uproject_path, 'r') as uproject:
            project_data = json.load(uproject)

        return [plugin.get('Name') for plugin in project_data.get('Plugins', {}) if plugin.get('Enabled')]

    @staticmethod
    def get_project_settings_value(config_name, section_name, setting_name):
        """
        Gets a specified setting value from a project settings file. Note: method only works correctly
        with config sections with unique setting names.

        :param str config_name: The config file to use in the unreal project config directory.
        :param str section_name: The section to query in the config file.
        :param str setting_name: The setting to query in the supplied section.
        :return: Value of the queried setting.
        """
        engine_config_dir = unreal.Paths.project_config_dir()
        config_path = f'{engine_config_dir}{config_name}.ini'

        from configparser import ConfigParser
        # setting strict to False to bypass duplicate keys in the config file
        parser = ConfigParser(strict=False)
        parser.read(config_path)

        return parser.get(section_name, setting_name, fallback=None)

    @staticmethod
    def has_socket(asset_path, socket_name):
        """
        Checks to see if an asset has a socket.

        :param str asset_path: The path to the unreal asset.
        :param str socket_name: The name of the socket to look for.
        :return bool: Whether the asset has the given socket or not.
        """
        mesh = Unreal.get_asset(asset_path)
        return bool(mesh.find_socket(socket_name))

    @staticmethod
    def has_binding_groom_asset(binding_asset_path, groom_asset_path):
        """
        Checks to see if the binding asset at binding_asset_path has the groom asset set at groom_asset_path.

        :param str binding_asset_path: The path to the unreal binding asset.
        :param str groom_asset_path: The path to the unreal groom asset.
        :return bool: Whether the binding asset has the given groom.
        """
        binding_asset = unreal.load_asset(binding_asset_path)
        groom_asset = unreal.load_asset(groom_asset_path)

        if binding_asset and groom_asset:
            return bool(binding_asset.get_editor_property('groom') == groom_asset)
        return False

    @staticmethod
    def has_binding_target(binding_asset_path, target_mesh_path):
        """
        Checks to see if the binding asset at binding_asset_path has the target skeletal mesh asset
        set at target_mesh_path.

        :param str binding_asset_path: The path to the unreal binding asset.
        :param str target_mesh_path: The path to the unreal skeletal mesh asset.
        :return bool: Whether the binding asset has the given skeletal mesh target.
        """
        binding_asset = unreal.load_asset(binding_asset_path)
        mesh_asset = unreal.load_asset(target_mesh_path)

        if binding_asset and mesh_asset:
            return bool(binding_asset.get_editor_property('target_skeletal_mesh') == mesh_asset)
        return False

    @staticmethod
    def has_groom_and_mesh_components(blueprint_asset_path, binding_asset_path, groom_asset_path, mesh_asset_path):
        """
        Checks if a blueprint asset has mesh and groom components with the correct assets.

        :param str blueprint_asset_path: The path to the unreal blueprint asset.
        :param str binding_asset_path: The path to the unreal binding asset.
        :param str groom_asset_path: The path to the unreal groom asset.
        :param str mesh_asset_path: The path to the unreal mesh asset.
        :return bool: Whether the blueprint asset has the right mesh and groom components configured.
        """
        component_handles = Unreal.get_component_handles(blueprint_asset_path)

        groom_handle = Unreal.get_groom_handle(component_handles, binding_asset_path, groom_asset_path)
        mesh_handle = Unreal.get_skeletal_mesh_handle(component_handles, mesh_asset_path)

        return groom_handle and mesh_handle and Unreal.is_parent_component_of_child(mesh_handle, groom_handle)

    @staticmethod
    def has_groom_component(blueprint_asset_path, binding_asset_path, groom_asset_path):
        """
        Checks if a blueprint asset has groom component with the correct assets.

        :param str blueprint_asset_path: The path to the unreal blueprint asset.
        :param str binding_asset_path: The path to the unreal binding asset.
        :param str groom_asset_path: The path to the unreal groom asset.
        :return bool: Whether the blueprint asset has the right groom component configured.
        """
        component_handles = Unreal.get_component_handles(blueprint_asset_path)
        groom_handle = Unreal.get_groom_handle(component_handles, binding_asset_path, groom_asset_path)

        if groom_handle:
            return True
        return False

    @staticmethod
    def has_mesh_component(blueprint_asset_path, mesh_asset_path):
        """
        Checks if a blueprint asset has mesh component with the correct assets.

        :param str blueprint_asset_path: The path to the unreal blueprint asset.
        :param str mesh_asset_path: The path to the unreal mesh asset.
        :return bool: Whether the blueprint asset has the right mesh and groom components configured.
        """
        component_handles = Unreal.get_component_handles(blueprint_asset_path)
        mesh_handle = Unreal.get_skeletal_mesh_handle(component_handles, mesh_asset_path)

        if mesh_handle:
            return True
        return False

    @staticmethod
    def has_socket_outer(asset_path, socket_name):
        """
        Checks to see if an asset has a socket and the owner (outer) is assigned to the mesh.

        :param str asset_path: The path to the unreal asset.
        :param str socket_name: The name of the socket to look for.
        :return bool: Whether the asset has the given socket and the owner (outer) is properly assigned or not.
        """
        mesh = Unreal.get_asset(asset_path)
        socket = mesh.find_socket(socket_name)
        if socket:
            return socket.get_outer() == mesh
        else:
            return False

    @staticmethod
    def delete_asset(asset_path):
        """
        Deletes an asset in unreal.

        :param str asset_path: The path to the unreal asset.
        :return bool: Whether the asset was deleted.
        """
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            unreal.EditorAssetLibrary.delete_asset(asset_path)

    @staticmethod
    def delete_directory(directory_path):
        """
        Deletes a folder and its contents in unreal.

        :param str directory_path: The game path to the unreal project folder.
        :return bool: Whether the directory was deleted.
        """
        if unreal.EditorAssetLibrary.does_directory_exist(directory_path):
            unreal.EditorAssetLibrary.delete_directory(directory_path)

    @staticmethod
    def import_asset(file_path, asset_data, property_data):
        """
        Imports an asset to unreal based on the asset data in the provided dictionary.

        :param str file_path: The full path to the file to import.
        :param dict asset_data: A dictionary of import parameters.
        :param dict property_data: A dictionary representation of the properties.
        """
        # import if valid file_path was provided
        if file_path:
            unreal_import_asset = UnrealImportAsset(
                file_path=file_path,
                asset_data=asset_data,
                property_data=property_data
            )
            file_path, file_type = os.path.splitext(file_path)
            if file_type.lower() == '.fbx':
                unreal_import_asset.set_fbx_import_task_options()
            elif file_type.lower() == '.abc':
                unreal_import_asset.set_abc_import_task_options()

            # run the import task
            return unreal_import_asset.run_import()

    @staticmethod
    def create_asset(asset_path, asset_class=None, asset_factory=None, unique_name=True):
        """
        Creates a new unreal asset.

        :param str asset_path: The project path to the asset.
        :param str asset_class: The name of the unreal asset class.
        :param str asset_factory: The name of the unreal factory.
        :param bool unique_name: Whether the check if the name is unique before creating the asset.
        """
        asset_class = getattr(unreal, asset_class)
        factory = getattr(unreal, asset_factory)()

        unreal_asset = Unreal.create_asset(asset_path, asset_class, factory, unique_name)
        return unreal_asset

    @staticmethod
    def create_binding_asset(groom_asset_path, mesh_asset_path):
        """
        Creates a groom binding asset.

        :param str groom_asset_path: The unreal asset path to the imported groom asset.
        :param str mesh_asset_path: The unreal asset path to the associated mesh asset.
        :return str binding_asset_path: The unreal asset path to the created binding asset.
        """
        return Unreal.create_binding_asset(groom_asset_path, mesh_asset_path)

    @staticmethod
    def create_blueprint_with_groom(groom_asset_path, mesh_asset_path, binding_asset_path):
        """
        Adds a groom component to a blueprint asset with specific skeletal mesh. If queried blueprint asset does not
        exist, create a blueprint asset with a skeletal mesh component that has a child groom component with the
        imported groom asset and binding asset.

        :param dict groom_asset_path: The unreal asset path to the imported groom asset.
        :param str mesh_asset_path: The unreal asset path to the associated mesh asset.
        :param str binding_asset_path: The unreal asset path to the created binding asset.
        :return str blueprint_asset_path: The unreal path to the blueprint asset.
        """
        return Unreal.add_groom_component_to_blueprint(groom_asset_path, mesh_asset_path, binding_asset_path)

    @staticmethod
    def import_sequence_track(asset_path, file_path, track_name, start=None, end=None):
        """
        Initializes the import with asset data and property data.

        :param str asset_path: The project path to the asset.
        :param str file_path: The full file path to the import file.
        :param str track_name: The name of the track.
        :param int start: The start frame.
        :param int end: The end frame.
        """
        unreal_import_sequence = UnrealImportSequence(
            asset_path=asset_path,
            file_path=file_path,
            track_name=track_name,
            start=start,
            end=start
        )
        # run the import task
        unreal_import_sequence.run_import()

    @staticmethod
    def import_skeletal_mesh_lod(asset_path, file_path, index):
        """
        Imports a lod onto a skeletal mesh.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param str file_path: The path to the file that contains the lods on disk.
        :param int index: Which lod index to import the lod on.
        """
        skeletal_mesh = Unreal.get_asset(asset_path)
        skeletal_mesh_subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
        result = skeletal_mesh_subsystem.import_lod(skeletal_mesh, index, file_path)
        if result == -1:
            raise RuntimeError(f"{file_path} import failed!")

    @staticmethod
    def import_static_mesh_lod(asset_path, file_path, index):
        """
        Imports a lod onto a static mesh.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param str file_path: The path to the file that contains the lods on disk.
        :param int index: Which lod index to import the lod on.
        """
        static_mesh = Unreal.get_asset(asset_path)
        static_mesh_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        result = static_mesh_subsystem.import_lod(static_mesh, index, file_path)
        if result == -1:
            raise RuntimeError(f"{file_path} import failed!")

    @staticmethod
    def set_skeletal_mesh_lod_build_settings(asset_path, index, property_data):
        """
        Sets the lod build settings for skeletal mesh.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param int index: Which lod index to import the lod on.
        :param dict property_data: A dictionary representation of the properties.
        """
        skeletal_mesh = Unreal.get_asset(asset_path)
        skeletal_mesh_subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
        options = unreal.SkeletalMeshBuildSettings()
        options = Unreal.set_settings(
            property_data['unreal']['editor_skeletal_mesh_library']['lod_build_settings'],
            options
        )
        skeletal_mesh_subsystem.set_lod_build_settings(skeletal_mesh, index, options)

    @staticmethod
    def set_static_mesh_lod_build_settings(asset_path, index, property_data):
        """
        Sets the lod build settings for static mesh.

        :param str asset_path: The project path to the static mesh in unreal.
        :param int index: Which lod index to import the lod on.
        :param dict property_data: A dictionary representation of the properties.
        """
        static_mesh = Unreal.get_asset(asset_path)
        static_mesh_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        options = unreal.MeshBuildSettings()
        options = Unreal.set_settings(
            property_data['unreal']['editor_static_mesh_library']['lod_build_settings'],
            options
        )
        static_mesh_subsystem.set_lod_build_settings(static_mesh, index, options)

    @staticmethod
    def reset_skeletal_mesh_lods(asset_path, property_data):
        """
        Removes all lods on the given skeletal mesh.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param dict property_data: A dictionary representation of the properties.
        """
        skeletal_mesh = Unreal.get_asset(asset_path)
        skeletal_mesh_subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
        lod_count = skeletal_mesh_subsystem.get_lod_count(skeletal_mesh)
        if lod_count > 1:
            skeletal_mesh.remove_lo_ds(list(range(1, lod_count)))

        lod_settings_path = property_data.get('unreal_skeletal_mesh_lod_settings_path', {}).get('value', '')
        if lod_settings_path:
            data_asset = Unreal.get_asset(asset_path)
            skeletal_mesh.lod_settings = data_asset
            skeletal_mesh_subsystem.regenerate_lod(skeletal_mesh, new_lod_count=lod_count)

    @staticmethod
    def reset_static_mesh_lods(asset_path):
        """
        Removes all lods on the given static mesh.

        :param str asset_path: The project path to the static mesh in unreal.
        """
        static_mesh = Unreal.get_asset(asset_path)
        static_mesh_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        lod_count = static_mesh_subsystem.get_lod_count(static_mesh)
        if lod_count > 1:
            static_mesh_subsystem.remove_lods(static_mesh)

    @staticmethod
    def set_static_mesh_sockets(asset_path, asset_data):
        """
        Sets sockets on a static mesh.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param dict asset_data: A dictionary of import parameters.
        """
        static_mesh = Unreal.get_asset(asset_path)
        for socket_name, socket_data in asset_data.get('sockets').items():
            socket = unreal.StaticMeshSocket(static_mesh)

            # apply the socket settings
            socket.set_editor_property('relative_location', socket_data.get('relative_location'))
            socket.set_editor_property('relative_rotation', socket_data.get('relative_rotation'))
            socket.set_editor_property('relative_scale', socket_data.get('relative_scale'))
            socket.set_editor_property('socket_name', socket_name)

            # if that socket already exists remove it
            existing_socket = static_mesh.find_socket(socket_name)
            if existing_socket:
                static_mesh.remove_socket(existing_socket)

            # create a new socket
            static_mesh.add_socket(socket)

    @staticmethod
    def get_lod_build_settings(asset_path, index):
        """
        Gets the lod build settings from the given asset.

        :param str asset_path: The project path to the asset.
        :param int index: The lod index to check.
        :return dict: A dictionary of lod build settings.
        """
        build_settings = None
        mesh = Unreal.get_asset(asset_path)
        if not mesh:
            raise RuntimeError(f'"{asset_path}" was not found in the unreal project!')
        if mesh.__class__.__name__ == 'SkeletalMesh':
            skeletal_mesh_subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
            build_settings = skeletal_mesh_subsystem.get_lod_build_settings(mesh, index)
        if mesh.__class__.__name__ == 'StaticMesh':
            static_mesh_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
            build_settings = static_mesh_subsystem.get_lod_build_settings(mesh, index)

        return Unreal.object_attributes_to_dict(build_settings)

    @staticmethod
    def get_bone_path_to_root(asset_path, bone_name):
        """
        Gets the path to the root bone from the given skeleton.

        :param str asset_path: The project path to the asset.
        :param str bone_name: The name of the bone to start from.
        :return list: A list of bone name all the way to the root bone.
        """
        animation = Unreal.get_asset(asset_path)
        path = unreal.AnimationLibrary.find_bone_path_to_root(animation, bone_name)
        return [str(i) for i in path]

    @staticmethod
    def get_bone_transform_for_frame(asset_path, bone_name, frame):
        """
        Gets the transformations of the given bone on the given frame.

        :param str asset_path: The project path to the asset.
        :param str bone_name: The name of the bone to get the transforms of.
        :param float frame: The frame number.
        :return dict: A dictionary of transformation values.
        """
        animation = Unreal.get_asset(asset_path)
        path = unreal.AnimationLibrary.find_bone_path_to_root(animation, bone_name)
        transform = Unreal.get_bone_pose_for_frame(animation, bone_name, frame, True)
        world_rotation = unreal.Rotator()
        world_location = unreal.Transform()

        # this walks the bone hierarchy to get the world transforms
        for bone in path:
            bone_transform = Unreal.get_bone_pose_for_frame(animation, str(bone), frame, True)
            world_rotation = world_rotation.combine(bone_transform.rotation.rotator())
            world_location = world_location.multiply(bone_transform)

        return {
            'scale': transform.scale3d.to_tuple(),
            'world_rotation': world_rotation.transform().rotation.euler().to_tuple(),
            'local_rotation': transform.rotation.euler().to_tuple(),
            'world_location': world_location.translation.to_tuple(),
            'local_location': transform.translation.to_tuple()
        }

    @staticmethod
    def get_bone_count(skeleton_path):
        """
        Gets the bone count from the given skeleton.

        :param str skeleton_path: The project path to the skeleton.
        :return int: The number of bones.
        """
        skeleton = unreal.load_asset(skeleton_path)
        return len(skeleton.get_editor_property('bone_tree'))

    @staticmethod
    def get_origin(asset_path):
        """
        Gets the location of the asset origin.

        :param str asset_path: The project path to the asset.
        :return list: A list of bone name all the way to the root bone.
        """
        mesh = Unreal.get_asset(asset_path)
        return mesh.get_bounds().origin.to_tuple()

    @staticmethod
    def get_morph_target_names(asset_path):
        """
        Gets the name of the morph targets on the given asset.

        :param str asset_path: The project path to the asset.
        :return list[str]: A list of morph target names.
        """
        skeletal_mesh = Unreal.get_asset(asset_path)
        return list(skeletal_mesh.get_all_morph_target_names())

    @staticmethod
    def get_sequence_track_keyframe(asset_path, track_name, curve_name, frame):
        """
        Gets the transformations of the given bone on the given frame.

        :param str asset_path: The project path to the asset.
        :param str track_name: The name of the track.
        :param str curve_name: The curve name.
        :param float frame: The frame number.
        :return dict: A dictionary of transformation values.
        """
        sequence = unreal.load_asset(asset_path)
        bindings = {binding.get_name(): binding for binding in sequence.get_bindings()}
        binding = bindings.get(track_name)
        track = binding.get_tracks()[0]
        section = track.get_sections()[0]
        data = {}
        for channel in section.get_channels():
            if channel.get_name().startswith(curve_name):
                for key in channel.get_keys():
                    if key.get_time().frame_number.value == frame:
                        data[channel.get_name()] = key.get_value()
        return data

    @staticmethod
    def import_animation_fcurves(asset_path, fcurve_file_path):
        """
        Imports fcurves from a file onto an animation sequence.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param str fcurve_file_path: The file path to the fcurve file.
        """
        animation_sequence = Unreal.get_asset(asset_path)
        with open(fcurve_file_path, 'r') as fcurve_file:
            fcurve_data = json.load(fcurve_file)

        for fcurve_name, keys in fcurve_data.items():
            unreal.AnimationLibrary.add_curve(animation_sequence, fcurve_name)
            for key in keys:
                unreal.AnimationLibrary.add_float_curve_key(animation_sequence, fcurve_name, key[0], key[1])

    @staticmethod
    def does_curve_exist(asset_path, curve_name):
        """
        Checks if the fcurve exists on the animation sequence.

        :param str asset_path: The project path to the skeletal mesh in unreal.
        :param str curve_name: The fcurve name.
        """
        animation_sequence = Unreal.get_asset(asset_path)
        return unreal.AnimationLibrary.does_curve_exist(
            animation_sequence,
            curve_name,
            unreal.RawCurveTrackTypes.RCT_FLOAT
        )

    @staticmethod
    def instance_asset(asset_path, location, rotation, scale, label):
        """
        Instances the given asset into the active level.

        :param str asset_path: The project path to the asset in unreal.
        :param list location: The unreal actor world location.
        :param list rotation: The unreal actor world rotation.
        :param list scale: The unreal actor world scale.
        :param str label: The unreal actor label.
        """
        asset = Unreal.get_asset(asset_path)
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

        # if the unique name is found delete it
        if Unreal.has_asset_actor_with_label(label):
            Unreal.delete_asset_actor_with_label(label)

        # spawn the actor
        actor = actor_subsystem.spawn_actor_from_object(
            asset,
            location,
            rotation=rotation,
            transient=False
        )
        actor.set_actor_label(label)

        # set the transforms of the actor with the tag that matches the unique name
        actor = Unreal.get_asset_actor_by_label(label)
        if actor:
            actor.set_actor_transform(
                new_transform=unreal.Transform(
                    location=location,
                    rotation=rotation,
                    scale=scale
                ),
                sweep=False,
                teleport=True
            )

    @staticmethod
    def delete_all_asset_actors():
        """
        Deletes all asset actors from the current level.
        """
        Unreal.delete_all_asset_actors()

    @staticmethod
    def get_asset_actor_transforms(label):
        """
        Get the transforms for the provided actor.

        :param str label: The unreal actor label.
        :returns: A dictionary of transforms.
        :rtype: dict
        """
        actor = Unreal.get_asset_actor_by_label(label)
        if actor:
            root_component = actor.get_editor_property('root_component')
            return {
                'location': root_component.get_world_location().to_tuple(),
                'rotation': root_component.get_world_rotation().to_tuple(),
                'scale': root_component.get_world_scale().to_tuple(),
            }
