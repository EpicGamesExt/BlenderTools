# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from ..properties import Send2UeProperties, Send2UeUIProperties
from ..functions import validations, utilities


def draw_general_tab(properties, layout):
    """
    Draws all the properties in the General tab.
    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'automatically_create_collections')


def draw_paths_tab(properties, layout):
    """
    Draws all the properties in the Paths tab.
    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'path_mode', text='')
    row = layout.row()
    row.prop(properties, 'use_immediate_parent_collection_name')

    if properties.path_mode in ['send_to_unreal', 'both']:
        row = layout.row()
        row.prop(properties, 'use_collections_as_folders')
        # Mesh Folder (Unreal)
        row = layout.row()
        row.label(text='Mesh Folder (Unreal)')
        # disable the mesh folder path input if a skeleton path is provided
        row = layout.row()
        row.alert = properties.incorrect_unreal_mesh_folder_path
        row.prop(properties, 'unreal_mesh_folder_path', text='')
        utilities.report_path_error_message(
            layout,
            properties.incorrect_unreal_mesh_folder_path,
            validations.validate_unreal_path_by_property(
                properties,
                "incorrect_unreal_mesh_folder_path"
            )
        )

        # Animation Folder (Unreal)
        row = layout.row()
        row.label(text='Animation Folder (Unreal)')
        row = layout.row()
        row.alert = properties.incorrect_unreal_animation_folder_path
        row.prop(properties, 'unreal_animation_folder_path', text='')
        utilities.report_path_error_message(
            layout,
            properties.incorrect_unreal_animation_folder_path,
            validations.validate_unreal_path_by_property(
                properties,
                "incorrect_unreal_animation_folder_path"
            )
        )

        # Skeleton Asset (Unreal)
        row = layout.row()
        row.label(text='Skeleton Asset (Unreal)')
        row = layout.row()
        row.alert = properties.incorrect_unreal_skeleton_path
        row.prop(properties, 'unreal_skeleton_asset_path', text='')
        utilities.report_path_error_message(
            layout,
            properties.incorrect_unreal_skeleton_path,
            validations.validate_unreal_path_by_property(
                properties,
                "incorrect_unreal_skeleton_path"
            )
        )

    if properties.path_mode in ['export_to_disk', 'both']:
        # Mesh Folder (Disk)
        row = layout.row()
        row.label(text='Mesh Folder (Disk)')
        # disable the mesh folder path input if a skeleton path is provided
        row.enabled = not bool(properties.unreal_skeleton_asset_path)
        row = layout.row()
        row.alert = properties.incorrect_disk_mesh_folder_path or properties.mesh_folder_untitled_blend_file
        row.prop(properties, 'disk_mesh_folder_path', text='')
        utilities.report_path_error_message(
            layout,
            properties.incorrect_disk_mesh_folder_path,
            validations.validate_disk_path_by_property(
                properties,
                "incorrect_disk_mesh_folder_path"
            )
        )
        utilities.report_path_error_message(
            layout,
            properties.mesh_folder_untitled_blend_file,
            validations.validate_disk_path_by_property(
                properties,
                "mesh_folder_untitled_blend_file"
            )
        )

        utilities.report_path_error_message(
            layout,
            properties.disk_mesh_folder_path,
            validations.validate_file_permissions(
                properties.disk_mesh_folder_path,
                properties,
                ui=True
            )
        )

        # Animation Folder (Disk)
        row = layout.row()
        row.label(text='Animation Folder (Disk)')
        row = layout.row()
        row.alert = properties.incorrect_disk_animation_folder_path or properties.animation_folder_untitled_blend_file
        row.prop(properties, 'disk_animation_folder_path', text='')
        utilities.report_path_error_message(
            layout,
            properties.incorrect_disk_animation_folder_path,
            validations.validate_disk_path_by_property(
                properties,
                "incorrect_disk_animation_folder_path"
            )
        )
        utilities.report_path_error_message(
            layout,
            properties.animation_folder_untitled_blend_file,
            validations.validate_disk_path_by_property(
                properties,
                "animation_folder_untitled_blend_file"
            )
        )
        utilities.report_path_error_message(
            layout,
            properties.disk_animation_folder_path,
            validations.validate_file_permissions(
                properties.disk_animation_folder_path,
                properties,
                ui=True
            )
        )


def draw_export_tab(properties, layout):
    """
    Draws all the properties in the Export tab.

    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'use_object_origin')
    row = layout.row()
    row.prop(properties, 'combine_child_meshes')

    #  animation settings box
    row = layout.row()
    box = row.box()
    row = box.row()
    row.prop(
        properties,
        'show_animation_settings',
        icon='TRIA_DOWN' if properties.show_animation_settings else 'TRIA_RIGHT',
        icon_only=True,
        emboss=False
    )
    row.label(text='Animation Settings', icon='ARMATURE_DATA')

    if properties.show_animation_settings:
        draw_animation_box(properties, box)

    #  asset name affixes box
    row = layout.row()
    box = row.box()
    row = box.row()
    row.prop(
        properties,
        'show_name_affix_settings',
        icon='TRIA_DOWN' if properties.show_name_affix_settings else 'TRIA_RIGHT',
        icon_only=True,
        emboss=False
    )
    row.label(text='Asset Name Affixes', icon='SYNTAX_OFF')

    if properties.show_name_affix_settings:
        draw_asset_affix_settings(properties, box)

    # fbx export settings box
    row = layout.row()
    box = row.box()
    row = box.row()
    row.prop(
        properties,
        'show_fbx_settings',
        icon='TRIA_DOWN' if properties.show_fbx_settings else 'TRIA_RIGHT',
        icon_only=True,
        emboss=False
    )
    row.label(text='FBX Settings', icon='EXPORT')

    if properties.show_fbx_settings:
        draw_fbx_box(properties, box)


def draw_import_tab(properties, layout):
    """
    Draws all the properties in the Import tab.

    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'import_materials')
    row = layout.row()
    row.prop(properties, 'import_textures')
    row = layout.row()
    row.prop(properties, 'import_animations')
    row = layout.row()
    row.prop(properties, 'import_lods')
    row = layout.row()
    row.prop(properties, 'import_sockets')
    row = layout.row()
    row.prop(properties, 'import_object_name_as_root')
    row = layout.row()
    row.prop(properties, 'advanced_ui_import')


def draw_validations_tab(properties, layout):
    """
    Draws all the properties in the Validations tab.

    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'validate_unit_settings')
    row = layout.row()
    row.prop(properties, 'validate_armature_transforms')
    row = layout.row()
    row.prop(properties, 'validate_materials')
    row = layout.row()
    row.prop(properties, 'validate_textures')


def draw_animation_box(properties, layout):
    """
    Draws all the properties in the Animation Settings box.

    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()
    row.prop(properties, 'automatically_scale_bones')
    row = layout.row()
    row.prop(properties, 'export_all_actions')
    row = layout.row()
    row.prop(properties, 'auto_stash_active_action')

    # this option is greyed out unless ue2rigify is active
    row = layout.row()
    row.enabled = bool(bpy.context.preferences.addons.get('ue2rigify'))
    row.prop(properties, 'auto_sync_control_nla_to_source')


def draw_asset_affix_settings(properties, layout):
    """
    Draws all the properties in the Name Affix Settings box.
    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """

    # Automatically Add Asset Affixes on export
    column = layout.column()
    row = column.split(factor=0.4)
    row.prop(properties, 'auto_add_asset_name_affixes')
    if properties.auto_add_asset_name_affixes:
        row.label(text='Warning: This will rename the exported assets in Blender!',
                  icon='ERROR')
    # Automatically Remove Asset Affixes after export
    row = layout.row()
    row.prop(properties, 'auto_remove_original_asset_names')

    # Static Mesh Affix
    row = layout.row()
    row.alert = properties.incorrect_static_mesh_name_affix
    row.prop(properties, 'static_mesh_name_affix')
    utilities.report_path_error_message(
        layout,
        properties.incorrect_static_mesh_name_affix,
        validations.show_asset_affix_message(properties, 'incorrect_static_mesh_name_affix')
    )
    # Material Affix
    row = layout.row()
    row.alert = properties.incorrect_material_name_affix
    row.prop(properties, 'material_name_affix')
    utilities.report_path_error_message(
        layout,
        properties.incorrect_material_name_affix,
        validations.show_asset_affix_message(properties, 'incorrect_material_name_affix')
    )
    # Texture Affix
    row = layout.row()
    row.alert = properties.incorrect_texture_name_affix
    row.prop(properties, 'texture_name_affix')
    utilities.report_path_error_message(
        layout,
        properties.incorrect_texture_name_affix,
        validations.show_asset_affix_message(properties, 'incorrect_texture_name_affix')
    )
    # Skeletal Mesh Affix
    row = layout.row()
    row.alert = properties.incorrect_skeletal_mesh_name_affix
    row.prop(properties, 'skeletal_mesh_name_affix')
    utilities.report_path_error_message(
        layout,
        properties.incorrect_skeletal_mesh_name_affix,
        validations.show_asset_affix_message(properties, 'incorrect_skeletal_mesh_name_affix')
    )
    # Animation Sequence Affix
    row = layout.row()
    row.alert = properties.incorrect_animation_sequence_name_affix
    row.prop(properties, 'animation_sequence_name_affix')
    utilities.report_path_error_message(
        layout,
        properties.incorrect_animation_sequence_name_affix,
        validations.show_asset_affix_message(properties, 'incorrect_animation_sequence_name_affix')
    )


def draw_fbx_box(properties, layout):
    """
    Draws all the properties in the FBX Settings box.

    :param properties: The add-on properties to use.
    :param layout: The layout container for this tab.
    """
    row = layout.row()

    row.label(text='Include:')
    row = layout.row()
    row.prop(properties, 'use_custom_props')
    row = layout.row()

    row.label(text='Transform:')
    row = layout.row()
    row.prop(properties, 'global_scale')
    row = layout.row()
    row.prop(properties, 'apply_scale_options')
    row = layout.row()
    row.prop(properties, 'axis_forward')
    row = layout.row()
    row.prop(properties, 'axis_up')
    row = layout.row()
    row.prop(properties, 'apply_unit_scale')
    row = layout.row()
    row.prop(properties, 'bake_space_transform')
    row = layout.row()

    row.label(text='Geometry:')
    row = layout.row()
    row.prop(properties, 'mesh_smooth_type')
    row = layout.row()
    row.prop(properties, 'use_subsurf')
    row = layout.row()
    row.prop(properties, 'use_mesh_modifiers')
    row = layout.row()
    row.prop(properties, 'use_mesh_edges')
    row = layout.row()
    row.prop(properties, 'use_tspace')
    row = layout.row()

    row.label(text='Armature:')
    row = layout.row()
    row.prop(properties, 'primary_bone_axis')
    row = layout.row()
    row.prop(properties, 'secondary_bone_axis')
    row = layout.row()
    row.prop(properties, 'armature_nodetype')
    row = layout.row()
    row.prop(properties, 'use_armature_deform_only')
    row = layout.row()
    row.prop(properties, 'add_leaf_bones')
    row = layout.row()

    row.label(text='Animation:')
    row = layout.row()
    row.prop(properties, 'bake_anim')
    row = layout.row()
    row.prop(properties, 'bake_anim_use_all_bones')
    row = layout.row()
    row.prop(properties, 'bake_anim_force_startend_keying')
    row = layout.row()
    row.prop(properties, 'bake_anim_step')
    row = layout.row()
    row.prop(properties, 'bake_anim_simplify_factor')
    row = layout.row()

    row.label(text='Extras:')
    row = layout.row()
    row.prop(properties, 'use_metadata')


class SendToUnrealPreferences(Send2UeProperties, Send2UeUIProperties, bpy.types.AddonPreferences):
    """
    This class creates the settings interface in the send to unreal addon.
    """
    bl_idname = __package__.split('.')[0]

    def draw(self, context, properties=None):
        """
        This defines the draw method, which is in all Blender UI types that create interfaces.
        :param context: The context of this interface.
        :param properties: The add-on properties to use.
        """
        layout = self.layout

        if not properties:
            properties = self

        row = layout.row()
        row.prop(properties, 'options_type', expand=True)

        if properties.options_type == 'general':
            draw_general_tab(properties, layout)
        elif properties.options_type == 'paths':
            draw_paths_tab(properties, layout)
        elif properties.options_type == 'export':
            draw_export_tab(properties, layout)
        elif properties.options_type == 'import':
            draw_import_tab(properties, layout)
        elif properties.options_type == 'validations':
            draw_validations_tab(properties, layout)
