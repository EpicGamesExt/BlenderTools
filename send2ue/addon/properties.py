# Copyright Epic Games, Inc. All Rights Reserved.
import bpy
from .functions import utilities
from .functions import validations


class Send2UeProperties:
    """
    This class holds the variables for the addon.
    """
    # read only properties
    module_name = __package__
    collection_names = ['Mesh', 'Rig', 'Collision', 'Extras']
    mesh_collection_name = 'Mesh'
    rig_collection_name = 'Rig'
    collision_collection_name = 'Collision'

    # ----------- read/write variables -----------

    # this stores the error messages
    error_message: bpy.props.StringProperty(default='')
    error_message_details: bpy.props.StringProperty(default='')
    # whether to use ue2rigify or not
    use_ue2rigify: bpy.props.BoolProperty(default=False)
    # the path made by the collection hierarchy
    sub_folder_path: bpy.props.StringProperty(default='')


class Send2UeUIProperties:
    """
    This class holds the UI variables for the addon.
    """
    # import dialog interface properties
    source_application: bpy.props.EnumProperty(
        name="Source Application",
        description="The application the original file was created with",
        items=[
            ('ue4', 'Unreal Engine 4', '', '', 0)
        ],
        default="ue4",
    )

    # addon preferences user interface properties
    options_type: bpy.props.EnumProperty(
        items=[
            ('general', 'General', '', '', 0),
            ('paths', 'Paths', '', '', 1),
            ('export', 'Export', '', '', 2),
            ('import', 'Import', '', '', 3),
            ('validations', 'Validations', '', '', 4)
        ],
        default="paths",
        description="Select which preferences you want to edit"
    )
    automatically_create_collections: bpy.props.BoolProperty(
        name="Automatically create pre-defined addon collections",
        default=True,
        description=f"This automatically creates the pre-defined addon collections (Mesh, Rig, Collision, Extras)"
    )
    path_mode: bpy.props.EnumProperty(
        name='Path Mode',
        items=[
            ('send_to_unreal', 'Send to Unreal', '', '', 0),
            ('export_to_disk', 'Export to Disk', '', '', 1),
            ('both', 'Both', '', '', 2)
        ],
        default='send_to_unreal',
        description="Select which type of paths you want to export to"
    )
    use_immediate_parent_collection_name: bpy.props.BoolProperty(
        name="Use immediate parent collection name",
        default=False,
        description=(
            "This makes the immediate parent collection the name of the asset"
        )
    )
    use_collections_as_folders: bpy.props.BoolProperty(
        name="Use collections as folders",
        default=False,
        description=(
            "This uses the collection hierarchy in your scene as sub folders from the specified mesh folder in your "
            "unreal project"
        )
    )
    unreal_mesh_folder_path: bpy.props.StringProperty(
        name="Set the mesh import path",
        default=r"/Game/untitled_category/untitled_asset/",
        update=utilities.auto_format_unreal_mesh_folder_path,
        description=(
            "This is the mesh import path. All your static and skeletal meshes will be imported to this location in"
            " your open unreal project"
        )
    )
    unreal_animation_folder_path: bpy.props.StringProperty(
        name="Set the animation import path",
        default=r"/Game/untitled_category/untitled_asset/animations/",
        update=utilities.auto_format_unreal_animation_folder_path,
        description=(
            "This is the animation import path. All your actions that are in an Armature object’s NLA strips will be "
            "imported to this location in your open Unreal Project"
        )
    )
    unreal_skeleton_asset_path: bpy.props.StringProperty(
        name="Set the reference to skeleton",
        default=r"",
        update=utilities.auto_format_unreal_skeleton_asset_path,
        description=(
            "This is the direct path to the Skeleton you want to import animation on. You can get this path by "
            "right-clicking on the skeleton asset in Unreal and selecting ‘Copy Reference’"
        )
    )
    disk_mesh_folder_path: bpy.props.StringProperty(
        name="Set the mesh import path",
        default=r"C:/",
        update=utilities.auto_format_disk_mesh_folder_path,
        description=(
            "This is the path to the folder where your mesh is exported to on disk. All your static and skeletal "
            "meshes will be exported to this location. The file names will match the object names in Blender"
        )
    )
    disk_animation_folder_path: bpy.props.StringProperty(
        name="Set the animation import path",
        default=r"C:/",
        update=utilities.auto_format_disk_animation_folder_path,
        description=(
            "This is the path to the folder where your actions will be exported to on disk. All your actions that "
            "are in an Armature object’s NLA strips will be exported to this location. The file names will match the "
            "action names in Blender"
        )
    )
    automatically_scale_bones: bpy.props.BoolProperty(
        name="Automatically scale bones",
        default=True,
        description=(
            "This automatically scales your armature objects so they import at scale of 1"
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
    auto_stash_active_action: bpy.props.BoolProperty(
        name="Auto stash active action",
        default=True,
        description=(
            "This is supposed to simplify the process of creating animation and stashing it into the object’s NLA "
            "strips. With this option turned on you can start animating on an object and export it and not have to "
            "manually edit NLA strips."
        )
    )
    auto_sync_control_nla_to_source: bpy.props.BoolProperty(
        name="Auto sync control NLA strips to source",
        default=True,
        description=(
            "When using ‘UE to Rigify’ with this option turned on, ‘Send to Unreal’ will remove the NLA strips from "
            "the source rig, then copy over the strips from the control rig to the source rig. The values copied over "
            "are: nla track name, nla track mute value, strip name, strip start frame, strip end frame, and strip scale"
        )
    )
    use_object_origin: bpy.props.BoolProperty(
        name="Use object origin",
        default=False,
        description=(
            "When active, this option will center each object at world origin before it is exported to an FBX, then it "
            "will move each object back to its original position"
        )
    )
    combine_child_meshes: bpy.props.BoolProperty(
        name="Combine child meshes",
        default=False,
        description=(
            "This combines all children mesh of an object into as a single mesh when exported"
        )
    )
    import_materials: bpy.props.BoolProperty(
        name="Materials",
        default=True,
        description="Whether or not to import the materials from the FBX file"
    )
    import_textures: bpy.props.BoolProperty(
        name="Textures",
        default=True,
        description="Whether or not to import the Textures from the FBX file"
    )
    import_animations: bpy.props.BoolProperty(
        name="Animations",
        default=True,
        description="Whether or not to import the animation from the FBX file"
    )
    import_lods: bpy.props.BoolProperty(
        name="LODs",
        default=False,
        description="Whether or not to import the custom LODs from the FBX file"
    )
    import_sockets: bpy.props.BoolProperty(
        name="Sockets",
        default=False,
        description="Imports an empty as a socket as long as it is a child of a mesh and its name starts with 'SOCKET_'."
                    "(Only works on static meshes)"
    )
    import_object_name_as_root: bpy.props.BoolProperty(
        name="Object name as root bone",
        default=True,
        description=(
            "This uses the armature object's name in blender as the root bone name in Unreal"
        )
    )
    advanced_ui_import: bpy.props.BoolProperty(
        name="Launch FBX Import UI",
        default=False,
        description="When enabled this option launches the FBX import UI in Unreal"
    )
    validate_unit_settings: bpy.props.BoolProperty(
        name="Check scene units",
        default=True,
        description=(
            "This checks the scene units and ensures they are set to metric, and the scene scale is 1"
        )
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

    # ----------- read/write variables -----------
    show_animation_settings: bpy.props.BoolProperty(default=False)
    show_name_affix_settings: bpy.props.BoolProperty(default=False)
    show_fbx_settings: bpy.props.BoolProperty(default=False)
    incorrect_static_mesh_name_affix: bpy.props.BoolProperty(default=False)
    incorrect_texture_name_affix: bpy.props.BoolProperty(default=False)
    incorrect_material_name_affix: bpy.props.BoolProperty(default=False)
    incorrect_skeletal_mesh_name_affix: bpy.props.BoolProperty(default=False)
    incorrect_animation_sequence_name_affix: bpy.props.BoolProperty(default=False)
    incorrect_unreal_mesh_folder_path: bpy.props.BoolProperty(default=False)
    incorrect_unreal_animation_folder_path: bpy.props.BoolProperty(default=False)
    incorrect_unreal_skeleton_path: bpy.props.BoolProperty(default=False)
    incorrect_disk_mesh_folder_path: bpy.props.BoolProperty(default=False)
    incorrect_disk_animation_folder_path: bpy.props.BoolProperty(default=False)
    mesh_folder_untitled_blend_file: bpy.props.BoolProperty(default=False)
    animation_folder_untitled_blend_file: bpy.props.BoolProperty(default=False)

    # ---------------------------- name affix settings --------------------------------
    auto_add_asset_name_affixes: bpy.props.BoolProperty(
        name="Automatically add affixes on export",
        description=(
            "Whether or not to add the affixes (prefix, suffix) to the asset names before the export. "
            "Prefixes end with an underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
        ),
        default=False,
    )
    auto_remove_original_asset_names: bpy.props.BoolProperty(
        name="Remove affixes after export",
        description=(
            "Whether or not to remove the affixes (prefix, suffix) from the asset names after the export, "
            + "basically restoring the original names."
        ),
        default=False,
    )
    static_mesh_name_affix: bpy.props.StringProperty(
        name="Static Mesh Affix",
        default="SM_",
        update=validations.validate_asset_affixes,
        description="The prefix or suffix to use for exported static mesh assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    material_name_affix: bpy.props.StringProperty(
        name="Material Affix",
        default="M_",
        update=validations.validate_asset_affixes,
        description="The prefix or suffix to use for exported material assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    texture_name_affix: bpy.props.StringProperty(
        name="Texture Affix",
        default="T_",
        update=validations.validate_asset_affixes,
        description="The prefix or suffix to use for exported texture assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    skeletal_mesh_name_affix: bpy.props.StringProperty(
        name="Skeletal Mesh Affix",
        default="SK_",
        update=validations.validate_asset_affixes,
        description="The prefix or suffix to use for exported skeletal mesh assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    animation_sequence_name_affix: bpy.props.StringProperty(
        name="Animation Sequence Affix",
        default="Anim_",
        update=validations.validate_asset_affixes,
        description="The prefix or suffix to use for exported animation sequence assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )

    # ---------------------------- fbx file settings --------------------------------
    # Include
    use_custom_props: bpy.props.BoolProperty(
        name="Custom Properties",
        description="Export custom properties",
        default=False,
    )
    # Transform
    global_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale all data (Some importers do not support scaled armatures!)",
        min=0.001, max=1000.0,
        soft_min=0.01, soft_max=1000.0,
        default=1.0,
    )
    apply_scale_options: bpy.props.EnumProperty(
        items=(('FBX_SCALE_NONE', "All Local",
                "Apply custom scaling and units scaling to each object transformation, FBX scale remains at 1.0"),
               ('FBX_SCALE_UNITS', "FBX Units Scale",
                "Apply custom scaling to each object transformation, and units scaling to FBX scale"),
               ('FBX_SCALE_CUSTOM', "FBX Custom Scale",
                "Apply custom scaling to FBX scale, and units scaling to each object transformation"),
               ('FBX_SCALE_ALL', "FBX All",
                "Apply custom scaling and units scaling to FBX scale"),
               ),
        name="Apply Scalings",
        description="How to apply custom and units scalings in generated FBX file "
                    "(Blender uses FBX scale to detect units on import, "
                    "but many other applications do not handle the same way)",
    )
    axis_forward: bpy.props.EnumProperty(
        name="Forward",
        items=(('X', "X Forward", ""),
               ('Y', "Y Forward", ""),
               ('Z', "Z Forward", ""),
               ('-X', "-X Forward", ""),
               ('-Y', "-Y Forward", ""),
               ('-Z', "-Z Forward", ""),
               ),
        default='-Y',
    )
    axis_up: bpy.props.EnumProperty(
        name="Up",
        items=(('X', "X Up", ""),
               ('Y', "Y Up", ""),
               ('Z', "Z Up", ""),
               ('-X', "-X Up", ""),
               ('-Y', "-Y Up", ""),
               ('-Z', "-Z Up", ""),
               ),
        default='Z',
    )
    apply_unit_scale: bpy.props.BoolProperty(
        name="Apply Unit",
        description=(
            "Take into account current Blender units settings (if unset, raw Blender Units values are used as-is)"
        ),
        default=True,
    )
    bake_space_transform: bpy.props.BoolProperty(
        name="!EXPERIMENTAL! Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
                    "target space is not aligned with Blender's space "
                    "(WARNING! experimental option, use at own risks, known broken with armatures/animations)",
        default=False,
    )
    # -------------- Geometry --------------
    mesh_smooth_type: bpy.props.EnumProperty(
        name="Smoothing",
        items=(('OFF', "Normals Only", "Export only normals instead of writing edge or face smoothing data"),
               ('FACE', "Face", "Write face smoothing"),
               ('EDGE', "Edge", "Write edge smoothing"),
               ),
        description="Export smoothing information "
                    "(prefer 'Normals Only' option if your target importer understand split normals)",
        default='OFF',
    )
    use_subsurf: bpy.props.BoolProperty(
        name="Export Subdivision Surface",
        description="Export the last Catmull-Rom subdivision modifier as FBX subdivision "
                    "(does not apply the modifier even if 'Apply Modifiers' is enabled)",
        default=False,
    )
    use_mesh_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (except Armature ones) - "
                    "WARNING: prevents exporting shape keys",
        default=True,
    )
    use_mesh_edges: bpy.props.BoolProperty(
        name="Loose Edges",
        description="Export loose edges (as two-vertices polygons)",
        default=False,
    )
    use_tspace: bpy.props.BoolProperty(
        name="Tangent Space",
        description="Add binormal and tangent vectors, together with normal they form the tangent space "
                    "(will only work correctly with tris/quads only meshes!)",
        default=False,
    )
    # -------------- Armature --------------
    primary_bone_axis: bpy.props.EnumProperty(
        name="Primary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='Y',
    )
    secondary_bone_axis: bpy.props.EnumProperty(
        name="Secondary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='X',
    )
    armature_nodetype: bpy.props.EnumProperty(
        name="Armature FBXNode Type",
        items=(('NULL', "Null", "'Null' FBX node, similar to Blender's Empty (default)"),
               ('ROOT', "Root", "'Root' FBX node, supposed to be the root of chains of bones..."),
               ('LIMBNODE', "LimbNode", "'LimbNode' FBX node, a regular joint between two bones..."),
               ),
        description="FBX type of node (object) used to represent Blender's armatures "
                    "(use Null one unless you experience issues with other app, other choices may no import back "
                    "perfectly in Blender...)",
        default='NULL',
    )
    use_armature_deform_only: bpy.props.BoolProperty(
        name="Only Deform Bones",
        description="Only write deforming bones (and non-deforming ones when they have deforming children)",
        default=False,
    )
    add_leaf_bones: bpy.props.BoolProperty(
        name="Add Leaf Bones",
        description="Append a final bone to the end of each chain to specify last bone length "
                    "(use this when you intend to edit the armature from exported data)",
        default=False  # False for commit!
    )
    # -------------- Animation --------------
    bake_anim: bpy.props.BoolProperty(
        name="Baked Animation",
        description="Export baked keyframe animation",
        default=True,
    )
    bake_anim_use_all_bones: bpy.props.BoolProperty(
        name="Key All Bones",
        description="Force exporting at least one key of animation for all bones "
                    "(needed with some target applications, like UE4)",
        default=True,
    )
    bake_anim_force_startend_keying: bpy.props.BoolProperty(
        name="Force Start/End Keying",
        description="Always add a keyframe at start and end of actions for animated channels",
        default=True,
    )
    bake_anim_step: bpy.props.FloatProperty(
        name="Sampling Rate",
        description="How often to evaluate animated values (in frames)",
        min=0.01, max=100.0,
        soft_min=0.1, soft_max=10.0,
        default=1.0,
    )
    bake_anim_simplify_factor: bpy.props.FloatProperty(
        name="Simplify",
        description="How much to simplify baked values (0.0 to disable, the higher the more simplified)",
        min=0.0,
        max=100.0,
        soft_min=0.0, soft_max=10.0,
        default=0.0,  # default: min slope: 0.005, max frame step: 10.
    )
    # -------------- Extras --------------
    use_metadata: bpy.props.BoolProperty(
        name="Use Metadata",
        default=True,
        options={'HIDDEN'},
    )


class Send2UeWindowMangerPropertyGroup(bpy.types.PropertyGroup, Send2UeProperties):
    """
    This class defines a property group that stores constants in the window manger context.
    """


class Send2UeSavedProperties(bpy.types.PropertyGroup):
    """
    This class defines a property group that stores constants in the scene context. The reason we
    store the addon properties in the scene context is so the modified addons preferences will get
    saved to the blend file.
    """


def register():
    """
    This function registers the property group class and adds it to the window manager context when the
    addon is enabled.
    """
    bpy.utils.register_class(Send2UeWindowMangerPropertyGroup)
    bpy.utils.register_class(Send2UeSavedProperties)

    bpy.types.WindowManager.send2ue = bpy.props.PointerProperty(type=Send2UeWindowMangerPropertyGroup)
    bpy.types.Scene.send2ue = bpy.props.PointerProperty(type=Send2UeSavedProperties)


def unregister():
    """
    This function unregisters the property group class and deletes it from the window manager context when the
    addon is disabled.
    """
    bpy.utils.unregister_class(Send2UeWindowMangerPropertyGroup)

    del bpy.types.WindowManager.send2ue
    del bpy.types.Scene.send2ue
