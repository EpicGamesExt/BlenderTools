# Copyright Epic Games, Inc. All Rights Reserved.

import os
import uuid
import bpy
from .constants import ToolInfo, PathModes, Template
from .core import settings, formatting, extension


class Send2UeAddonProperties:
    """
    This class holds the properties for the addon.
    """
    automatically_create_collections: bpy.props.BoolProperty(
        name="Automatically create pre-defined collections",
        default=True,
        description=f"This automatically creates the pre-defined collection (Export)"
    )
    rpc_response_timeout: bpy.props.IntProperty(
        name="RPC Response Timeout",
        default=60,
        description=(
            "The amount of seconds that blender stops waiting for an unreal response after it has issued a command. "
            "This might need to be increased if you plan on importing really large assets, where the import could "
            "be longer then the timeout value"
        ),
        set=settings.set_rpc_response_timeout,
        get=settings.get_rpc_response_timeout
    )
    extensions_repo_path: bpy.props.StringProperty(
            name="Extensions Repo Path",
            default="",
            description=(
                "Set this path to the folder that contains your Send to Unreal python extensions. All extensions "
                "in this folder will be automatically loaded"
            )
        )


class Send2UeWindowMangerProperties(bpy.types.PropertyGroup):
    """
    This class holds the properties for a window.
    """
    # ------------- current asset info ------------------
    asset_data = {}
    asset_id: bpy.props.StringProperty(
        default='',
        description=(
            'Holds the current asset id. This can be used in an extension method to access and modify specific '
            'asset data'
        )
    )
    # ----------- read/write dictionaries -----------
    property_errors = {}
    section_collapse_states = {}

    # ----------- read/write variables -----------
    show_animation_settings: bpy.props.BoolProperty(default=False)
    show_fbx_export_settings: bpy.props.BoolProperty(default=False)
    show_abc_export_settings: bpy.props.BoolProperty(default=False)
    show_fbx_import_settings: bpy.props.BoolProperty(default=False)
    show_abc_import_settings: bpy.props.BoolProperty(default=False)
    show_lod_settings: bpy.props.BoolProperty(default=False)
    show_editor_library_settings: bpy.props.BoolProperty(default=False)
    show_export_extensions: bpy.props.BoolProperty(default=False)
    show_import_extensions: bpy.props.BoolProperty(default=False)
    show_validation_extensions: bpy.props.BoolProperty(default=False)

    # this stores the error messages
    error_message: bpy.props.StringProperty(default='')
    error_message_details: bpy.props.StringProperty(default='')

    # import dialog interface properties
    source_application: bpy.props.EnumProperty(
        name="Source Application",
        description="The application the original file was created with",
        items=[
            ('ue4', 'Unreal Engine 4', '', '', 0),
            ('ue5', 'Unreal Engine 5', '', '', 1)
        ],
        default="ue5",
    )

    path_validation: bpy.props.BoolProperty(default=True)
    progress_label: bpy.props.StringProperty()
    progress: bpy.props.FloatProperty(
        name="Progress",
        subtype="PERCENTAGE",
        soft_min=0,
        soft_max=100,
        precision=0,
        default=0
    )


def get_scene_property_class():
    """
    Gets the scene property class.
    """
    # the extension factory will add in the extension properties
    extension_factory = extension.ExtensionFactory()
    property_class = extension_factory.get_property_group_class()

    class Send2UeSceneProperties(property_class):
        """
        This class holds the properties for the scene.
        """
        # track the template version
        template_version: bpy.props.FloatProperty(
            name='Template Version',
            default=Template.VERSION,
            description=(
                'This is the version of the template format. As updates are made, variable name might change, '
                'so this keeps track of the expected variable names'
            )
        )
        active_settings_template: bpy.props.EnumProperty(
            name="Setting Template",
            items=settings.populate_settings_template_dropdown,
            options={'ANIMATABLE'},
            description="Select which settings template you want to load",
            update=settings.set_active_template
        )
        tab: bpy.props.EnumProperty(
            items=[
                ('paths', 'Paths', 'Paths', '', 0),
                ('export', 'Export', 'Export', '', 1),
                ('import', 'Import', 'Import', '', 2),
                ('validations', 'Validations', 'Validations', '', 3)
            ],
            default="paths",
            description="Choose which section of the settings to view"
        )
        path_mode: bpy.props.EnumProperty(
            name='Path Mode',
            items=[
                (
                    PathModes.SEND_TO_PROJECT.value,
                    'Send to Project',
                    (
                        'Sends the intermediate files to a temporary location on disk and then imports them into'
                        'the Unreal Project. This does not require any extra configuration, but might not be ideal if '
                        'your intermediate files need to be under source control.'
                    ),
                    '',
                    0
                ),
                (
                    PathModes.SEND_TO_DISK.value,
                    'Send to Disk',
                    (
                        'Sends the intermediate files to a specified location on disk and does not import them.'
                    ),
                    '',
                    1
                ),
                (
                    PathModes.SEND_TO_DISK_THEN_PROJECT.value,
                    'Send to Disk then Project',
                    (
                        'Sends the intermediate files to a specified location on disk and then imports them into '
                        'the Unreal Project. This requires extra paths to be configured, but is ideal if your intermediate'
                        ' files need to be under source control.'
                    ),
                    '',
                    2
                )
            ],
            default=PathModes.SEND_TO_PROJECT.value,
            description="Select which type of paths you want to export to"
        )
        unreal_mesh_folder_path: bpy.props.StringProperty(
            name="Mesh Folder (Unreal)",
            default=r"/Game/untitled_category/untitled_asset/",
            update=formatting.update_unreal_mesh_folder_path,
            description=(
                "This is the mesh import path. All your static and skeletal meshes will be imported to this location in"
                " your open unreal project"
            )
        )
        unreal_animation_folder_path: bpy.props.StringProperty(
            name="Animation Folder (Unreal)",
            default=r"/Game/untitled_category/untitled_asset/animations/",
            update=formatting.update_unreal_animation_folder_path,
            description=(
                "This is the animation import path. All your actions that are in an Armature object’s NLA strips will "
                "be imported to this location in your open Unreal Project"
            )
        )
        unreal_groom_folder_path: bpy.props.StringProperty(
            name="Groom Folder (Unreal)",
            default=r"/Game/untitled_category/untitled_asset/groom/",
            update=formatting.update_unreal_groom_folder_path,
            description=(
                "This is the groom import path. All your Curves objects and hair particle systems will be imported "
                "to this location in your open Unreal Project"
            )
        )
        unreal_skeleton_asset_path: bpy.props.StringProperty(
            name="Skeleton Asset (Unreal)",
            default=r"",
            update=formatting.update_unreal_skeleton_asset_path,
            description=(
                "This is the direct path to the Skeleton you want to import animation on. You can get this path by "
                "right-clicking on the skeleton asset in Unreal and selecting ‘Copy Reference’"
            )
        )
        unreal_physics_asset_path: bpy.props.StringProperty(
            name="Physics Asset (Unreal)",
            default=r"",
            update=formatting.update_unreal_physics_asset_path,
            description=(
                "This is the direct path to the physics asset you want to use. You can get this path by "
                "right-clicking on the physics asset in Unreal and selecting ‘Copy Reference’"
            )
        )
        disk_mesh_folder_path: bpy.props.StringProperty(
            name="Mesh Folder (Disk)",
            default=os.path.expanduser('~'),
            update=formatting.update_disk_mesh_folder_path,
            description=(
                "This is the path to the folder where your mesh is exported to on disk. All your static and skeletal "
                "meshes will be exported to this location. The file names will match the name of the mesh object"
                " in Blender."
            )
        )
        disk_animation_folder_path: bpy.props.StringProperty(
            name="Animation Folder (Disk)",
            default=os.path.expanduser('~'),
            update=formatting.update_disk_animation_folder_path,
            description=(
                "This is the path to the folder where your actions will be exported to on disk. All your actions that "
                "are in an Armature object’s NLA strips will be exported to this location. The file names will match the "
                "action names in Blender"
            )
        )
        disk_groom_folder_path: bpy.props.StringProperty(
            name="Groom Folder (Disk)",
            default=os.path.expanduser('~'),
            update=formatting.update_disk_groom_folder_path,
            description=(
                "This is the path to the folder where your curves objects and particle systems will be exported to on "
                "disk. The file names will match either the name of the curves object or that of the particle system."
            )
        )
        export_all_actions: bpy.props.BoolProperty(
            name="Export all actions",
            default=True,
            description=(
                "This setting ensures that regardless of the mute values or the solo value (star) on your NLA tracks, your "
                "actions will get exported. It does this by un-muting all NLA tracks before the FBX export"
            )
        )
        # TODO validate this to prevent unreal error multiple roots found
        export_object_name_as_root: bpy.props.BoolProperty(
            name="Export object name as root bone",
            default=True,
            description=(
                "If true, this uses the armature object's name in blender as the root bone name in Unreal, otherwise "
                "the first bone in the armature hierarchy is used as the root bone in unreal."
            )
        )
        export_custom_property_fcurves: bpy.props.BoolProperty(
            name="Export custom property fcurves",
            default=True,
            description=(
                "When enabled, this will export any object's custom properties that are in the action fcurves"
            )
        )
        auto_stash_active_action: bpy.props.BoolProperty(
            name="Auto stash active action",
            default=True,
            description=(
                "This is supposed to simplify the process of creating animation and stashing it into the object’s NLA "
                "strips. With this option turned on you can start animating on an object and export it and not have to "
                "manually edit NLA strips."
            )
        )
        use_object_origin: bpy.props.BoolProperty(
            name="Use object origin",
            default=False,
            description=(
                "This forces the unreal asset to use the blender object origin instead of the blender scene's world"
                " origin"
            )
        )
        import_meshes: bpy.props.BoolProperty(
            name="Meshes",
            default=True,
            description="Whether or not to import the meshes from the FBX file"
        )
        import_materials_and_textures: bpy.props.BoolProperty(
            name="Materials and Textures",
            default=True,
            description="Whether or not to import the materials and textures from the FBX file"
        )
        import_animations: bpy.props.BoolProperty(
            name="Animations",
            default=True,
            description="Whether or not to import the animation from the FBX file"
        )
        import_grooms: bpy.props.BoolProperty(
            name="Grooms",
            default=True,
            description="Whether or not to import groom assets"
        )
        advanced_ui_import: bpy.props.BoolProperty(
            name="Launch Import UI",
            default=False,
            description="When enabled this option launches the import UI in Unreal"
        )
        # LOD settings
        import_lods: bpy.props.BoolProperty(
            name="LODs",
            default=False,
            description="Whether or not to export the custom LODs"
        )
        lod_regex: bpy.props.StringProperty(
            name="LOD Regex",
            default=r"(?i)(_LOD\d).*",
            description=(
                "Set a regular expression to determine an asset's lod identifier. The remaining unmatched string will "
                "be used as the asset name. The first matched group's last character should be the LOD index."
            )
        )
        unreal_skeletal_mesh_lod_settings_path: bpy.props.StringProperty(
            name="LOD Settings (Unreal)",
            default=r"",
            update=formatting.update_unreal_skeletal_mesh_lod_settings_path,
            description=(
                "This is the direct path to the LOD settings data asset in your unreal project. You can get this path "
                "by right-clicking on the LOD settings data asset in Unreal and selecting 'Copy Reference'"
            )
        )
        validate_scene_scale: bpy.props.BoolProperty(
            name="Check scene scale",
            default=True,
            description=(
                "This checks that the scene scale is set to 1"
            )
        )
        validate_time_units: bpy.props.EnumProperty(
            name="Check scene frame rate",
            items=[
                (
                    'off',
                    'Off',
                    'Dont run this validation',
                    '',
                    0
                ),
                (
                    '29.38',
                    '29.38',
                    'Validate that the scene frame rate is 29.38',
                    '',
                    1
                ),
                (
                    '24',
                    '24',
                    'Validate that the scene frame rate is 24',
                    '',
                    2
                ),
                (
                    '25',
                    '25',
                    'Validate that the scene frame rate is 25',
                    '',
                    3
                ),
                (
                    '29.97',
                    '29.97',
                    'Validate that the scene frame rate is 29.97',
                    '',
                    4
                ),
                (
                    '30',
                    '30',
                    'Validate that the scene frame rate is 30',
                    '',
                    5
                ),
                (
                    '50',
                    '50',
                    'Validate that the scene frame rate is 50',
                    '',
                    6
                ),
                (
                    '59.94',
                    '59.94',
                    'Validate that the scene frame rate is 59.94',
                    '',
                    7
                ),
                (
                    '60',
                    '60',
                    'Validate that the scene frame rate is 60',
                    '',
                    8
                ),
                (
                    '120',
                    '120',
                    'Validate that the scene frame rate is 120',
                    '',
                    9
                ),
                (
                    '240',
                    '240',
                    'Validate that the scene frame rate is 240',
                    '',
                    10
                )
            ],
            default='off',
            description="This checks the scene time units and ensures they are set to the specified value"
        )

        validate_armature_transforms: bpy.props.BoolProperty(
            name="Check armatures for un-applied transforms",
            default=True,
            description=(
                "If an armature object has un-applied transforms a message is thrown to the user"
            )
        )
        validate_materials: bpy.props.BoolProperty(
            name="Check if asset has unused materials",
            default=False,
            description=(
                "If this option is on it looks at each material index on the object and it checks if that material is "
                "assigned to a vertex on the mesh object. If there is a unused material, then an error message is thrown "
                "to the user"
            )
        )
        validate_textures: bpy.props.BoolProperty(
            name="Check texture references",
            default=False,
            description=(
                "If a texture referenced in an object’s material can not be found in the blend file data than a error "
                "message is thrown to the user"
            )
        )
        validate_paths: bpy.props.BoolProperty(
            name="Check paths",
            default=True,
            description=(
                "This checks the export and import paths and makes sure they are valid before preforming "
                "the operation"
            )
        )
        validate_project_settings: bpy.props.BoolProperty(
            name="Check project settings",
            default=True,
            description=(
                "This checks whether the required unreal project settings are in place before performing "
                "the operation"
            )
        )
        validate_object_names: bpy.props.BoolProperty(
            name="Check blender object names",
            default=False,
            description=(
                "This checks whether object names in the Export folder contain any special characters "
                "that unreal does not accept"
            )
        )
        validate_meshes_for_vertex_groups: bpy.props.BoolProperty(
            name="Check meshes for vertex groups",
            default=True,
            description="This checks that a mesh with an armature modifier has vertex groups"
        )

    return Send2UeSceneProperties


def register_scene_properties():
    """
    Registers the scene properties.
    """
    if not bpy.types.PropertyGroup.bl_rna_get_subclass_py('Send2UeSceneProperties'):
        scene_property_class = get_scene_property_class()
        bpy.utils.register_class(scene_property_class)
        bpy.types.Scene.send2ue = bpy.props.PointerProperty(type=scene_property_class)


def unregister_scene_properties():
    """
    Unregisters the scene properties.
    """
    scene_property_class = bpy.types.PropertyGroup.bl_rna_get_subclass_py('Send2UeSceneProperties')
    if scene_property_class:
        bpy.utils.unregister_class(scene_property_class)


def register():
    """
    Registers the property group class and adds it to the window manager context when the
    addon is enabled.
    """
    if not bpy.types.PropertyGroup.bl_rna_get_subclass_py('Send2UeWindowMangerProperties'):
        bpy.utils.register_class(Send2UeWindowMangerProperties)
        bpy.types.WindowManager.send2ue = bpy.props.PointerProperty(type=Send2UeWindowMangerProperties)

    register_scene_properties()


def unregister():
    """
    Unregisters the property group class and deletes it from the window manager context when the
    addon is disabled.
    """

    # remove the extension property data
    extension_factory = extension.ExtensionFactory()
    extension_factory.remove_property_data()
    unregister_scene_properties()

    window_manager_property_class = bpy.types.PropertyGroup.bl_rna_get_subclass_py('Send2UeWindowMangerProperties')
    if window_manager_property_class:
        bpy.utils.unregister_class(window_manager_property_class)

    if hasattr(bpy.types.WindowManager, ToolInfo.NAME.value):
        del bpy.types.WindowManager.send2ue

    if hasattr(bpy.types.Scene, ToolInfo.NAME.value):
        del bpy.types.Scene.send2ue
